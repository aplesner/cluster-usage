import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import re

def extract_theses_data():
    """
    Extract thesis information from current and past DISCO website pages.
    Save results to a pandas DataFrame and CSV file.
    """
    print("Starting thesis data extraction...")
    
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
            print(f"\nProcessing {page_name} theses from {url}...")
            
            # Load the page
            driver.get(url)
            
            # Wait for JavaScript to execute
            time.sleep(3)
            
            # Get the rendered page source
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            print(f"Page source loaded for {page_name} page")

            # For current theses, find the specific section
            if page_name == "current":
                header = soup.find('h2', string='Current Theses & Labs')
                if not header:
                    print(f"Could not find header on {page_name} page")
                    continue
                    
                table = header.find_parent('table')
                if not table:
                    print(f"Could not find table on {page_name} page")
                    continue
                
                # Find the index of the header row
                rows = table.find_all('tr')
                header_index = None
                for i, row in enumerate(rows):
                    if row.find('h2', string='Current Theses & Labs'):
                        header_index = i
                        break
                
                if header_index is None:
                    print(f"Could not determine header index on {page_name} page")
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
                    print(f"Error processing row: {e}")
                    continue
            
            print(f"Extracted {len(all_theses_data)} theses until now")
        
        # Create DataFrame
        df = pd.DataFrame(all_theses_data)
        
        # Save to CSV
        csv_path = 'disco_all_theses.csv'
        df.to_csv(csv_path, index=False)
        print(f"Data saved to {csv_path}")
        
        return df
        
    finally:
        # Clean up browser
        driver.quit()

if __name__ == "__main__":
    # Run the extraction
    df = extract_theses_data()
    
    # Display results
    if df is not None:
        print("\nFirst few rows of extracted data:")
        print(df.head())
        print(f"\nTotal theses extracted: {len(df)}")
        
        # Show statistics
        print("\nStatistics:")
        print(f"Current theses: {len(df[df['is_past'] == False])}")
        print(f"Past theses: {len(df[df['is_past'] == True])}")
        
        # Count theses by semester
        print("\nTheses by semester:")
        semester_counts = df['semester'].value_counts()
        for semester, count in semester_counts.items():
            print(f"{semester}: {count}")
    else:
        print("Failed to extract thesis data")
