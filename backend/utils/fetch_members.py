#!/usr/bin/env python3
"""
Script to fetch DISCO members from the website and update the database.
Designed to run as a weekly scheduled task.
"""

import os
import sys
import time
import logging
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Set up the parent directory in path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from database.schema import get_db_connection, initialize_database
from config import DB_PATH

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(parent_dir, 'logs', 'member_sync.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('member_sync')

class MemberSyncError(Exception):
    """Custom exception for member sync errors"""
    pass

def extend_users_table(conn):
    """Extend the Users table with new columns for member information"""
    cursor = conn.cursor()
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(Users)")
    columns = [info[1] for info in cursor.fetchall()]
    
    # Add new columns if they don't exist
    columns_to_add = {
        'full_name': 'TEXT',
        'title': 'TEXT',
        'image_url': 'TEXT',
        'is_alumni': 'INTEGER DEFAULT 0',
        'last_updated': 'DATETIME'
    }
    
    for column, data_type in columns_to_add.items():
        if column not in columns:
            try:
                cursor.execute(f"ALTER TABLE Users ADD COLUMN {column} {data_type}")
                logger.info(f"Added column '{column}' to Users table")
            except sqlite3.Error as e:
                logger.error(f"Error adding column '{column}': {e}")
                raise
    
    conn.commit()
    logger.info("Users table schema update completed")

def fetch_members_page():
    """Fetch the members page from the DISCO website"""
    url = "https://disco.ethz.ch/members"
    logger.info(f"Fetching member data from {url}")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"Failed to fetch member data: {e}")
        raise MemberSyncError(f"Failed to fetch member data: {e}")

def validate_html_data(html_content):
    """Validate that the HTML content contains the expected structure"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Check for DISCO Members heading
    members_heading = soup.find('h1', string='DISCO Members')
    if not members_heading:
        raise MemberSyncError("HTML validation failed: Could not find 'DISCO Members' heading")
    
    # Check for members list
    members_list = members_heading.find_next('ul', class_='members')
    if not members_list:
        raise MemberSyncError("HTML validation failed: Could not find members list")
    
    # Check for Alumni heading
    alumni_heading = soup.find('h1', string='DISCO Alumni')
    if not alumni_heading:
        raise MemberSyncError("HTML validation failed: Could not find 'DISCO Alumni' heading")
    
    # Check for alumni list
    alumni_list = alumni_heading.find_next('ul', class_='members')
    if not alumni_list:
        raise MemberSyncError("HTML validation failed: Could not find alumni list")
    
    # Check for at least some members
    members = members_list.find_all('li', recursive=False)
    if not any(li.text.strip() for li in members):
        raise MemberSyncError("HTML validation failed: No members found in the members list")
    
    return True

def extract_members_from_html(html_content):
    """Extract member information from HTML content"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    members = []
    
    # Process current members
    members_section = soup.find('h1', string='DISCO Members')
    if members_section:
        members_list = members_section.find_next('ul', class_='members')
        if members_list:
            for li in members_list.find_all('li', recursive=False):
                # Skip empty list items
                if not li.text.strip():
                    continue
                
                # Extract member info
                member = extract_person_info(li, False)
                if member:
                    members.append(member)
    
    # Process alumni
    alumni_section = soup.find('h1', string='DISCO Alumni')
    if alumni_section:
        alumni_list = alumni_section.find_next('ul', class_='members')
        if alumni_list:
            for li in alumni_list.find_all('li', recursive=False):
                # Skip empty list items
                if not li.text.strip():
                    continue
                
                # Extract alumni info
                member = extract_person_info(li, True)
                if member:
                    members.append(member)
    
    logger.info(f"Extracted {len(members)} members/alumni from HTML")
    return members

def extract_person_info(li_element, is_alumni):
    """Extract information for a single person from an li element"""
    # Skip empty elements
    if not li_element.text.strip():
        return None
    
    a_tag = li_element.find('a')
    if not a_tag:
        return None
    
    # Extract username from href
    href = a_tag.get('href', '')
    if not href:
        return None
    
    # URLs are either /members/{username} or /alumni/{username}
    username = href.split('/')[-1]
    
    # Extract image URL
    img_tag = a_tag.find('img')
    image_url = img_tag.get('src', '') if img_tag else ""
    
    # If the image URL is relative, make it absolute
    if image_url and image_url.startswith('//'):
        image_url = 'https:' + image_url
    elif image_url and image_url.startswith('/'):
        image_url = 'https://disco.ethz.ch' + image_url
    
    # Extract name from alt attribute
    name = img_tag.get('alt', '') if img_tag else ""
    if not name:
        name = img_tag.get('title', '') if img_tag else ""
    
    # Extract title from the text after the <br> tags
    text_parts = [part.strip() for part in li_element.get_text().strip().split('\n') if part.strip()]
    
    # Check for Administrative Assistant to skip
    for part in text_parts:
        if "Administrative Assistant" in part:
            return None
    
    # Extract title - it's typically the last line for members
    # or second to last line for alumni (with years on the last line)
    title = ""
    if is_alumni and len(text_parts) > 2:
        if len(text_parts) >= 3:
            title = text_parts[-2]  # Role
            years = text_parts[-1]  # Year range
            title = f"{title} ({years})"
        else:
            title = text_parts[-1]
    elif len(text_parts) > 1:
        title = text_parts[-1]
    
    return {
        'username': username,
        'full_name': name,
        'title': title,
        'image_url': image_url,
        'is_alumni': 1 if is_alumni else 0,
        'last_updated': datetime.now().isoformat()
    }

def update_user_database(conn, members):
    """Update the Users table with member information"""
    cursor = conn.cursor()
    
    updated = 0
    inserted = 0
    skipped = 0
    
    for member in members:
        username = member['username']
        
        # Skip empty usernames
        if not username:
            skipped += 1
            continue
        
        # Check if user exists
        cursor.execute("SELECT user_id FROM Users WHERE username = ?", (username,))
        result = cursor.fetchone()
        
        if result:
            # Update existing user
            cursor.execute("""
                UPDATE Users 
                SET full_name = ?, title = ?, image_url = ?, is_alumni = ?, last_updated = ?
                WHERE username = ?
            """, (
                member['full_name'], 
                member['title'], 
                member['image_url'], 
                member['is_alumni'], 
                member['last_updated'],
                username
            ))
            updated += 1
        else:
            # Insert new user
            cursor.execute("""
                INSERT INTO Users (username, full_name, title, image_url, is_alumni, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                username,
                member['full_name'], 
                member['title'], 
                member['image_url'], 
                member['is_alumni'],
                member['last_updated']
            ))
            inserted += 1
    
    conn.commit()
    logger.info(f"Database updated: {inserted} new users inserted, {updated} existing users updated, {skipped} entries skipped")
    return inserted, updated, skipped

def sync_members():
    """Main function to sync members from the website to the database"""
    try:
        # Ensure database exists and is initialized
        if not os.path.exists(DB_PATH):
            logger.info(f"Database not found at {DB_PATH}. Initializing...")
            initialize_database(DB_PATH)
        
        # Connect to the database
        conn = get_db_connection(DB_PATH)
        
        # Extend the database schema if needed
        extend_users_table(conn)
        
        # Fetch the HTML content
        html_content = fetch_members_page()
        
        # Validate the HTML content
        validate_html_data(html_content)
        
        # Extract member information
        members = extract_members_from_html(html_content)
        
        if not members:
            raise MemberSyncError("No members found in the HTML content")
        
        # Log extracted members
        for member in members:
            status = "Alumni" if member['is_alumni'] else "Current"
            logger.debug(f"- {member['full_name']} ({member['username']}): {member['title']} [{status}]")
        
        # Update the database
        inserted, updated, skipped = update_user_database(conn, members)
        
        # Close the database connection
        conn.close()
        
        logger.info("Member sync completed successfully")
        return True
    except MemberSyncError as e:
        logger.error(f"Member sync failed: {e}")
        return False
    except Exception as e:
        logger.exception(f"Unexpected error in member sync: {e}")
        return False

if __name__ == "__main__":
    # Ensure logs directory exists
    os.makedirs(os.path.join(parent_dir, 'logs'), exist_ok=True)
    
    # Run the script
    logger.info("----- Starting member sync -----")
    start_time = time.time()
    success = sync_members()
    elapsed_time = time.time() - start_time
    
    if success:
        logger.info(f"Member sync completed in {elapsed_time:.2f} seconds")
        sys.exit(0)
    else:
        logger.error(f"Member sync failed after {elapsed_time:.2f} seconds")
        sys.exit(1)
