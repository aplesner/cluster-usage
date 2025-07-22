import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import re
import os
import logging
from backend.email_notifications.email_notifications import send_email
from backend.config import DATA_DIR, DB_PATH, NOTIFY_SUPERVISORS_ON_NON_ETHZ_STUDENT_EMAILS
from backend.database.schema import get_db_connection

CSV_FILE_PATH = f'{DATA_DIR}/disco_all_theses.csv'

def get_theses_rows(soup, page_name):
    """
    Extract thesis rows from the BeautifulSoup object based on the page type.
    
    Args:
        soup: BeautifulSoup object of the page content.
        page_name: 'current' or 'past' to determine how to extract rows.
        
    Returns:
        List of thesis rows.
    """
    if page_name == "current":
        header = soup.find('h2', string='Current Theses & Labs')
        if not header:
            logging.warning(f"Could not find header on {page_name} page")
            return []
        
        table = header.find_parent('table')
        if not table:
            logging.warning(f"Could not find table on {page_name} page")
            return []
        
        # Find the index of the header row
        rows = table.find_all('tr')
        header_index = None
        for i, row in enumerate(rows):
            if row.find('h2', string='Current Theses & Labs'):
                header_index = i
                break
        
        if header_index is None:
            logging.warning(f"Could not determine header index on {page_name} page")
            return []
        
        # The theses start after the header row and the column format row
        return rows[header_index + 2:]
    
    else:  # past theses
        # Find the main table - <table> tag 
        table = soup.find('table')
        
        # Get all rows after the header
        rows = table.find_all('tr')
        
        # Skip the first row (header)
        return rows[1:]


def extract_theses_data() -> pd.DataFrame:
    """
    Extract thesis information from current and past DISCO website pages.
    Save results to a pandas DataFrame and CSV file.
    """
    logging.info("Starting thesis data extraction...")
    
    # Set up Chrome in headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Process both current and past theses
        urls = [
            "https://disco.ethz.ch/theses",
            "https://disco.ethz.ch/theses/past",
        ]
        
        all_theses_data = []
        
        for url in urls:
            page_name = "current" if url.endswith("theses") else "past"
            logging.info(f"Processing {page_name} theses from {url}...")
            
            # Load the page
            driver.get(url)
            
            # Wait for JavaScript to execute
            time.sleep(3)
            
            # Get the rendered page source
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            logging.info(f"Page source loaded for {page_name} page")

            thesis_rows = get_theses_rows(soup, page_name)
            if not thesis_rows:
                logging.warning(f"No thesis rows found on {page_name} page")
                continue

            # Process thesis rows
            for row in thesis_rows:
                # Stop if we reach another section header on current page
                if page_name == "current" and row.find('h2'):
                    break
                    
                cells = row.find_all('td')
                if len(cells) < 6:
                    continue  # Skip incomplete rows
                    
                try:
                    # Extract thesis icon URL
                    icon_cell = cells[0]
                    icon_link = icon_cell.find('a')
                    if icon_link and icon_link.find('img'):
                        icon_url = icon_link.find('img')['src']
                    else:
                        icon_img = icon_cell.find('img')
                        icon_url = icon_img['src'] if icon_img else ""
                    
                    # Extract thesis title
                    title_cell = cells[1]
                    title_link = title_cell.find('a')
                    if title_link:
                        title = title_link.text.strip()
                    else:
                        title = title_cell.text.strip()
                    
                    # Extract supervisor usernames (remove /members/ or /alumni/ prefix)
                    supervisor_cell = cells[3]
                    supervisor_links = supervisor_cell.find_all('a')
                    supervisors = []
                    for link in supervisor_links:
                        href = link['href']
                        if href.startswith('/members/'):
                            supervisors.append(href[9:])  # Remove '/members/'
                        elif href.startswith('/alumni/'):
                            supervisors.append(href[8:])  # Remove '/alumni/'
                    
                    # Extract the semester (Assigned column)
                    assigned_cell = cells[4]
                    semester = assigned_cell.text.strip()
                    
                    # Extract student information with multiple students support
                    student_cell = cells[5]
                    student_links = student_cell.find_all('a')
                    
                    student_names = []
                    student_emails = []
                    
                    for student_link in student_links:
                        href = student_link.get('href', '')
                        if 'mailto:' in href:
                            # Get student name from link text
                            student_names.append(student_link.text.strip())
                            
                            # Get email from mailto: href
                            student_email = href[7:]  # Remove 'mailto:' prefix
                            
                            # Extract email address from format like "Name <email@domain.com>"
                            email_match = re.search(r'<([^>]+)>', student_email)
                            if email_match:
                                student_emails.append(email_match.group(1))
                            else:
                                student_emails.append(student_email)
                    
                    # Format multiple students as semicolon-separated lists
                    student_names_str = "; ".join(student_names)
                    student_emails_str = "; ".join(student_emails)
                    
                    # Add to theses data
                    thesis_data = {
                        'title': title,
                        'icon_url': icon_url,
                        'supervisors': ', '.join(supervisors),
                        'semester': semester,
                        'student_names': student_names_str,
                        'student_emails': student_emails_str,
                        'is_past': page_name == "past"
                    }
                    
                    all_theses_data.append(thesis_data)
                        
                except Exception as e:
                    logging.error(f"Error processing row: {e}")
                    continue
            
            logging.info(f"Extracted {len(all_theses_data)} theses until now")

        # Return DataFrame
        return pd.DataFrame(all_theses_data)
        
    finally:
        # Clean up browser
        driver.quit()


def scrape_disco_theses() -> None:
    
    df = extract_theses_data()

    # Save to CSV
    csv_path = CSV_FILE_PATH
    df.to_csv(csv_path, index=False)
    logging.info(f"Data saved to {csv_path}")

    store_thesis_data_in_database(df)

    logging.info("DISCO thesis scraping completed and data stored in database.")

 
def read_disco_theses_from_csv() -> pd.DataFrame:
    """
    Read the DISCO theses data from the CSV file.

    Returns:
        DataFrame: DataFrame containing the theses data.
    """
    csv_path = CSV_FILE_PATH
    logging.info(f"Reading DISCO theses from CSV: {csv_path}")
    if not os.path.exists(csv_path):
        logging.error(f"CSV file not found: {csv_path}")
        return pd.DataFrame()  # Return empty DataFrame if file does not exist
    
    df = pd.read_csv(csv_path)
    logging.info(f"Read {len(df)} theses from CSV")
    
    return df


def run_disco_scraper() -> str:
    logging.info('Running DISCO thesis scraper task...')
    try:
        df = read_disco_theses_from_csv()
        
        if df is not None and not df.empty:
            
            # Filter for current theses only for email notifications
            current_theses = df[df['is_past'] == False]
            non_ethz_entries = []
            
            for _, row in current_theses.iterrows():
                emails = row['student_emails'].split(';') if row['student_emails'] else []
                # Check if any email does not contain 'ethz'
                if any('ethz' not in email.strip() for email in emails if email.strip()):
                    non_ethz_entries.append(row.to_dict())
            
            # Handle non-ETH email notifications
            if non_ethz_entries:
                logging.info(f"Current theses with non-ethz student emails: {len(non_ethz_entries)}")
                
                if NOTIFY_SUPERVISORS_ON_NON_ETHZ_STUDENT_EMAILS:
                    for entry in non_ethz_entries:
                        supervisors = [s.strip() for s in entry['supervisors'].split(',') if s.strip()]
                        if not supervisors:
                            logging.warning(f"No supervisors found for thesis: {entry['title']}")
                            continue
                        
                        student_names = entry['student_names']
                        student_emails = entry['student_emails']
                        thesis_title = entry['title']
                        
                        context = (
                            f"Thesis: {thesis_title}\n"
                            f"Student(s): {student_names} ({student_emails})\n"
                            "Please remind your student(s) to use their ETH email address for thesis registration."
                        )
                        
                        # Send email to each supervisor
                        for username in supervisors:
                            send_email(username, email_type="student-non-ethz-email", context=context)
                        
                        # Send email to each non-ETH student email
                        for email in student_emails.split(';'):
                            email = email.strip()
                            if email and 'ethz' not in email:
                                send_email(email, email_type="student-non-ethz-email", context=context)
                else:
                    logging.info("Supervisor notification for non-ethz student emails is disabled by config flag.")
            else:
                logging.info("All current theses have only ethz student emails.")
            
            return f'Extracted and stored {len(df)} theses successfully.'
        else:
            logging.warning('No thesis data extracted.')
            return 'No thesis data extracted.'
            
    except Exception as e:
        logging.error(f'Error in DISCO thesis scraper: {e}')
        return f'Error: {e}'


def register_disco_scraper_task(scheduler):
    """Register the DISCO thesis scraper task to run daily (every 1440 minutes)"""
    scheduler.add_task('disco_thesis_scraper', run_disco_scraper, interval_minutes=1440) 


def store_thesis_data_in_database(df: pd.DataFrame) -> None:
    """
    Store thesis data from DataFrame into the database.
    
    Args:
        df: DataFrame containing thesis data with columns:
            - title, supervisors, semester, student_names, student_emails, is_past, icon_url
    """
    if df is None or df.empty:
        logging.warning("No thesis data to store in database")
        return
    
    conn = get_db_connection(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Clear existing thesis data
        cursor.execute('DELETE FROM UserSupervisors')
        
        # Also create a dedicated Theses table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Theses (
            thesis_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            icon_url TEXT,
            semester TEXT,
            is_past INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('DELETE FROM Theses')
        
        thesis_id_counter = 1
        
        for _, row in df.iterrows():
            # Insert thesis into Theses table
            cursor.execute('''
                INSERT INTO Theses (thesis_id, title, icon_url, semester, is_past)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                thesis_id_counter,
                row['title'],
                row.get('icon_url', ''),
                row['semester'],
                1 if row['is_past'] else 0
            ))
            
            # Process student-supervisor relationships
            supervisors = [s.strip() for s in row['supervisors'].split(',') if s.strip()]
            student_emails = [e.strip() for e in row['student_emails'].split(';') if e.strip()]
            student_names = [n.strip() for n in row['student_names'].split(';') if n.strip()]
            
            # Create student-supervisor pairs
            for i, student_email in enumerate(student_emails):
                student_name = student_names[i] if i < len(student_names) else ""
                
                # Extract username from email (only for ETH emails)
                if 'ethz' in student_email and '@' in student_email:
                    student_username = student_email.split('@')[0]
                else:
                    # Skip non-ETH emails or use name as fallback
                    continue
                
                # Insert each student-supervisor relationship
                for supervisor_username in supervisors:
                    cursor.execute('''
                        INSERT OR IGNORE INTO UserSupervisors 
                        (student_username, supervisor_username, thesis_title, semester, student_email)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        student_username,
                        supervisor_username,
                        row['title'],
                        row['semester'],
                        student_email
                    ))
            
            thesis_id_counter += 1
        
        conn.commit()
        logging.info(f"Successfully stored {len(df)} theses in database")
        
    except Exception as e:
        logging.error(f"Error storing thesis data in database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def get_user_thesis_details(username: str) -> list[dict]:
    """
    Get detailed thesis information for a specific user.
    
    Args:
        username: The username to fetch thesis information for
        
    Returns:
        List[Dict]: List of thesis details including supervisors, thesis info, etc.
    """
    conn = get_db_connection(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get thesis information where user is a student
        cursor.execute('''
            SELECT DISTINCT 
                us.thesis_title,
                us.semester,
                us.student_email,
                t.icon_url,
                t.is_past,
                GROUP_CONCAT(DISTINCT us.supervisor_username) as supervisors
            FROM UserSupervisors us
            LEFT JOIN Theses t ON us.thesis_title = t.title AND us.semester = t.semester
            WHERE us.student_username = ?
            GROUP BY us.thesis_title, us.semester, us.student_email, t.icon_url, t.is_past
            ORDER BY t.is_past ASC, us.semester DESC
        ''', (username,))
        
        student_theses = cursor.fetchall()
        
        # Get thesis information where user is a supervisor
        cursor.execute('''
            SELECT DISTINCT 
                us.thesis_title,
                us.semester,
                t.icon_url,
                t.is_past,
                GROUP_CONCAT(DISTINCT us.student_username) as students,
                GROUP_CONCAT(DISTINCT us.student_email) as student_emails
            FROM UserSupervisors us
            LEFT JOIN Theses t ON us.thesis_title = t.title AND us.semester = t.semester
            WHERE us.supervisor_username = ?
            GROUP BY us.thesis_title, us.semester, t.icon_url, t.is_past
            ORDER BY t.is_past ASC, us.semester DESC
        ''', (username,))
        
        supervised_theses = cursor.fetchall()
        
        result = []
        
        # Add theses where user is a student
        for row in student_theses:
            result.append({
                'thesis_title': row[0],
                'semester': row[1],
                'role': 'student',
                'student_email': row[2],
                'icon_url': row[3] or '',
                'is_past': bool(row[4]),
                'supervisors': row[5].split(',') if row[5] else [],
                'students': []
            })
        
        # Add theses where user is a supervisor
        for row in supervised_theses:
            result.append({
                'thesis_title': row[0],
                'semester': row[1],
                'role': 'supervisor',
                'icon_url': row[2] or '',
                'is_past': bool(row[3]),
                'supervisors': [username],
                'students': row[4].split(',') if row[4] else [],
                'student_emails': row[5].split(',') if row[5] else []
            })
        
        return result
        
    except Exception as e:
        logging.error(f"Error fetching thesis details for user {username}: {e}")
        return []
    finally:
        conn.close()
