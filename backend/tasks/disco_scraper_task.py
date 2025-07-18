import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import re
import logging
from backend.email_notifications.email_notifications import send_email
from backend.config import DB_PATH, NOTIFY_SUPERVISORS_ON_NON_ETHZ_STUDENT_EMAILS
from backend.database.schema import get_db_connection

def extract_theses_data():
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

            # For current theses, find the specific section
            if page_name == "current":
                header = soup.find('h2', string='Current Theses & Labs')
                if not header:
                    logging.warning(f"Could not find header on {page_name} page")
                    continue
                    
                table = header.find_parent('table')
                if not table:
                    logging.warning(f"Could not find table on {page_name} page")
                    continue
                
                # Find the index of the header row
                rows = table.find_all('tr')
                header_index = None
                for i, row in enumerate(rows):
                    if row.find('h2', string='Current Theses & Labs'):
                        header_index = i
                        break
                
                if header_index is None:
                    logging.warning(f"Could not determine header index on {page_name} page")
                    continue
                    
                # The theses start after the header row and the column format row
                thesis_rows = rows[header_index + 2:]
                
            else:  # past theses
                # Find the main table - <table> tag 
                table = soup.find('table')
                
                # Get all rows after the header
                rows = table.find_all('tr')
                
                # Skip the first row (header)
                thesis_rows = rows[1:]
            
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
        
        # Create DataFrame
        df = pd.DataFrame(all_theses_data)
        
        # Save to CSV
        csv_path = 'disco_all_theses.csv'
        df.to_csv(csv_path, index=False)
        logging.info(f"Data saved to {csv_path}")
        
        return df
        
    finally:
        # Clean up browser
        driver.quit()

def run_disco_scraper():
    logging.info('Running DISCO thesis scraper task...')
    try:
        df = extract_theses_data()
        logging.info(f'DISCO thesis scraper completed. Extracted {len(df) if df is not None else 0} theses.')
        
        # Filter for current theses only
        if df is not None:
            current_theses = df[df['is_past'] == False]
            non_ethz_entries = []
            user_supervisor_pairs = []
            for _, row in current_theses.iterrows():
                emails = row['student_emails'].split(';') if row['student_emails'] else []
                student_names = row['student_names'].split(';') if row['student_names'] else []
                supervisors = [s.strip() for s in row['supervisors'].split(',') if s.strip()]
                thesis_title = row['title']
                semester = row['semester']
                # For each student email/name, pair with each supervisor
                for student_email, student_name in zip(emails, student_names):
                    student_email = student_email.strip()
                    student_name = student_name.strip()
                    # Only process if student_email contains 'ethz'
                    if 'ethz' not in student_email:
                        continue
                    # Use username before @ if email, else use name
                    if '@' in student_email:
                        student_username = student_email.split('@')[0]
                    else:
                        student_username = student_name
                    for supervisor in supervisors:
                        user_supervisor_pairs.append((student_username, supervisor, thesis_title, semester, student_email))
                # Check if any email does not contain 'ethz'
                if any('ethz' not in email for email in emails):
                    non_ethz_entries.append(row.to_dict())
            # Store user-supervisor pairs in the database
            conn = get_db_connection(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM UserSupervisors')
            for student_username, supervisor_username, thesis_title, semester, student_email in user_supervisor_pairs:
                cursor.execute(
                    'INSERT OR IGNORE INTO UserSupervisors (student_username, supervisor_username, thesis_title, semester, student_email) VALUES (?, ?, ?, ?, ?)',
                    (student_username, supervisor_username, thesis_title, semester, student_email)
                )
            conn.commit()
            conn.close()
            if non_ethz_entries:
                logging.info(f"Current theses with non-ethz student emails: {non_ethz_entries}")
                # Send email to supervisors for each entry, if flag is enabled
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
                        # Send a separate email to each supervisor (using username)
                        for username in supervisors:
                            send_email(username, email_type="student-non-ethz-email", context=context)
                        # Also send an email to each non-ethz student email
                        for email in student_emails.split(';'):
                            email = email.strip()
                            if email and 'ethz' not in email:
                                send_email(email, email_type="student-non-ethz-email", context=context)
                else:
                    logging.info("Supervisor notification for non-ethz student emails is disabled by config flag.")
            else:
                logging.info("All current theses have only ethz student emails.")
        
        return f'Extracted {len(df) if df is not None else 0} theses.'
    except Exception as e:
        logging.error(f'Error in DISCO thesis scraper: {e}')
        return f'Error: {e}'

def register_disco_scraper_task(scheduler):
    """Register the DISCO thesis scraper task to run daily (every 1440 minutes)"""
    scheduler.add_task('disco_thesis_scraper', run_disco_scraper, interval_minutes=1440) 