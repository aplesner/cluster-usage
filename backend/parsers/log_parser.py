import re
import sys
import os
import sqlite3
from datetime import datetime
import shutil

def convert_to_bytes(size_str):
    """Convert a size string (e.g., '512', '1K', '2M') to bytes"""
    multipliers = {
        '': 1,
        'K': 1024,
        'M': 1024 * 1024,
        'G': 1024 * 1024 * 1024
    }
    
    match = re.match(r'(\d+)([KMG])?$', size_str)
    if match:
        value = int(match.group(1))
        unit = match.group(2) if match.group(2) else ''
        return value * multipliers[unit]
    else:
        return 0

def log_exists(conn, unix_timestamp):
    """Check if a log entry with the given timestamp already exists"""
    cursor = conn.cursor()
    cursor.execute("SELECT log_id FROM LogEntries WHERE unix_timestamp = ?", (unix_timestamp,))
    return cursor.fetchone() is not None

def get_log_id(conn, unix_timestamp):
    """Get the log_id for a given unix_timestamp"""
    cursor = conn.cursor()
    cursor.execute("SELECT log_id FROM LogEntries WHERE unix_timestamp = ?", (unix_timestamp,))
    result = cursor.fetchone()
    return result[0] if result else None

def get_or_create_user(conn, username, user_role, user_affiliation):
    """Get existing user ID or create a new user and return its ID"""
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM Users WHERE username = ?", (username,))
    result = cursor.fetchone()
    
    if result:
        return result[0]
    else:
        cursor.execute(
            "INSERT INTO Users (username, user_role, user_affiliation) VALUES (?, ?, ?)",
            (username, user_role, user_affiliation)
        )
        return cursor.lastrowid

def get_or_create_machine(conn, machine_name, machine_type):
    """Get existing machine ID or create a new machine and return its ID"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT machine_id FROM Machines WHERE machine_name = ? AND machine_type = ?", 
        (machine_name, machine_type)
    )
    result = cursor.fetchone()
    
    if result:
        return result[0]
    else:
        cursor.execute(
            "INSERT INTO Machines (machine_name, machine_type) VALUES (?, ?)",
            (machine_name, machine_type)
        )
        return cursor.lastrowid

def get_or_create_io_size_range(conn, min_bytes, max_bytes, display_text):
    """Get existing IO size range ID or create a new one and return its ID"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT range_id FROM IOSizeRanges WHERE min_bytes = ? AND max_bytes = ?", 
        (min_bytes, max_bytes)
    )
    result = cursor.fetchone()
    
    if result:
        return result[0]
    else:
        cursor.execute(
            "INSERT INTO IOSizeRanges (min_bytes, max_bytes, display_text) VALUES (?, ?, ?)",
            (min_bytes, max_bytes, display_text)
        )
        return cursor.lastrowid

def parse_and_store_log_data(conn, log_content):
    """Parse log content and store in the database"""
    # Regular expressions for parsing
    timestamp_pattern = re.compile(r'Log: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \((\d+)\)')
    session_pattern = re.compile(r'@rd_client\(([^,]+),([^)]+)\)\[([^(]+)\(([^)]+)\)\]:')
    histogram_pattern = re.compile(r'\[([^,]+), ([^)]+)\)\s+(\d+) \|.*')
    
    # Variables to track current context
    current_timestamp = None
    current_unix_timestamp = None
    current_log_id = None
    current_machine_name = None
    current_machine_type = None
    current_user = None
    current_user_role = None
    current_user_affiliation = None
    current_session_id = None
    
    cursor = conn.cursor()
    
    # Start a transaction
    conn.execute("BEGIN TRANSACTION")
    
    # Process each line
    lines = log_content.strip().split('\n')
    line_index = 0
    
    while line_index < len(lines):
        line = lines[line_index].strip()
        line_index += 1
        
        if not line:
            continue
            
        # Check if this is a timestamp line
        timestamp_match = timestamp_pattern.match(line)
        if timestamp_match:
            timestamp_str = timestamp_match.group(1)
            unix_timestamp = int(timestamp_match.group(2))
            
            # Check if this log entry already exists
            if log_exists(conn, unix_timestamp):
                # Skip to the next timestamp
                current_log_id = get_log_id(conn, unix_timestamp)
                current_timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                current_unix_timestamp = unix_timestamp
                continue
            
            # Insert new log entry
            cursor.execute(
                "INSERT INTO LogEntries (timestamp, unix_timestamp) VALUES (?, ?)",
                (timestamp_str, unix_timestamp)
            )
            current_log_id = cursor.lastrowid
            current_timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            current_unix_timestamp = unix_timestamp
            continue
        
        # Check if this is a user session line
        session_match = session_pattern.match(line)
        if session_match and current_log_id:
            current_machine_name = session_match.group(1)
            current_machine_type = session_match.group(2)
            current_user = session_match.group(3)
            user_status = session_match.group(4)
            
            # Extract user role and affiliation
            user_status_parts = user_status.split('/')
            current_user_role = user_status_parts[0] if len(user_status_parts) > 0 else None
            current_user_affiliation = user_status_parts[1] if len(user_status_parts) > 1 else None
            
            # Get or create user and machine
            user_id = get_or_create_user(conn, current_user, current_user_role, current_user_affiliation)
            machine_id = get_or_create_machine(conn, current_machine_name, current_machine_type)
            
            # Create user session
            try:
                cursor.execute(
                    "INSERT INTO UserSessions (log_id, user_id, machine_id) VALUES (?, ?, ?)",
                    (current_log_id, user_id, machine_id)
                )
                current_session_id = cursor.lastrowid
            except sqlite3.IntegrityError:
                # Session already exists, get its ID
                cursor.execute(
                    "SELECT session_id FROM UserSessions WHERE log_id = ? AND user_id = ? AND machine_id = ?",
                    (current_log_id, user_id, machine_id)
                )
                current_session_id = cursor.fetchone()[0]
                
            continue
        
        # Check if this is a histogram line
        histogram_match = histogram_pattern.match(line)
        if histogram_match and current_session_id:
            size_min_str = histogram_match.group(1)
            size_max_str = histogram_match.group(2)
            count = int(histogram_match.group(3))
            
            # Convert size ranges to bytes
            min_bytes = convert_to_bytes(size_min_str)
            max_bytes = convert_to_bytes(size_max_str)
            display_text = f"[{size_min_str}, {size_max_str})"
            
            # Get or create IO size range
            range_id = get_or_create_io_size_range(conn, min_bytes, max_bytes, display_text)
            
            # Insert or update IO operation
            try:
                cursor.execute(
                    "INSERT INTO IOOperations (session_id, range_id, operation_count) VALUES (?, ?, ?)",
                    (current_session_id, range_id, count)
                )
            except sqlite3.IntegrityError:
                # Update existing operation count
                cursor.execute(
                    "UPDATE IOOperations SET operation_count = ? WHERE session_id = ? AND range_id = ?",
                    (count, current_session_id, range_id)
                )
    
    # Commit transaction
    conn.commit()

def process_log_file(conn, log_path, archive_dir=None):
    """Process a log file and update the database"""
    try:
        with open(log_path, 'r') as file:
            log_content = file.read()
        
        # Process log content
        parse_and_store_log_data(conn, log_content)
        
        # Archive the processed file if archive directory is provided
        if archive_dir:
            log_filename = os.path.basename(log_path)
            # Move the file to the archive directory using rsync
            archive_path: str = os.path.join(archive_dir, log_filename)
            # Add datetime to the filename to avoid overwriting
            archive_path = f"{archive_path.removesuffix(".log")}_{datetime.now().strftime('%Y-%m-%d.log')}"
            shutil.move(log_path, archive_path)
            print(f"Archived {log_filename} to {archive_dir}")
        
        print(f"Successfully processed log file: {log_path}")
        return True
    except Exception as e:
        print(f"Error processing log file {log_path}: {e}")
        return False

