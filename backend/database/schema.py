import sqlite3

def get_db_connection(db_path: str):
    """Create a database connection to the SQLite database"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

def initialize_database(db_path: str):
    """Create database schema if it doesn't exist"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    # Create tables with the normalized schema
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS LogEntries (
        log_id INTEGER PRIMARY KEY,
        timestamp DATETIME NOT NULL,
        unix_timestamp INTEGER NOT NULL,
        UNIQUE(unix_timestamp)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        user_role TEXT,
        user_affiliation TEXT,
        UNIQUE(username)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Machines (
        machine_id INTEGER PRIMARY KEY,
        machine_name TEXT NOT NULL,
        machine_type TEXT NOT NULL,
        UNIQUE(machine_name, machine_type)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS IOSizeRanges (
        range_id INTEGER PRIMARY KEY,
        min_bytes INTEGER NOT NULL,
        max_bytes INTEGER NOT NULL,
        display_text TEXT NOT NULL,
        UNIQUE(min_bytes, max_bytes)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS UserSessions (
        session_id INTEGER PRIMARY KEY,
        log_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        machine_id INTEGER NOT NULL,
        FOREIGN KEY (log_id) REFERENCES LogEntries (log_id),
        FOREIGN KEY (user_id) REFERENCES Users (user_id),
        FOREIGN KEY (machine_id) REFERENCES Machines (machine_id),
        UNIQUE(log_id, user_id, machine_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS IOOperations (
        operation_id INTEGER PRIMARY KEY,
        session_id INTEGER NOT NULL,
        range_id INTEGER NOT NULL,
        operation_count INTEGER NOT NULL,
        FOREIGN KEY (session_id) REFERENCES UserSessions (session_id),
        FOREIGN KEY (range_id) REFERENCES IOSizeRanges (range_id),
        UNIQUE(session_id, range_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS PeriodicTaskLogs (
        log_id INTEGER PRIMARY KEY,
        timestamp DATETIME NOT NULL,
        task_name TEXT NOT NULL,
        status TEXT NOT NULL,
        message TEXT,
        details TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

