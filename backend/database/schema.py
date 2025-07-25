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
        full_name TEXT,
        title TEXT,
        image_url TEXT,
        is_alumni INTEGER DEFAULT 0,
        last_updated DATETIME,
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
    
    # Define Jobs table structure
    jobs_table_structure = '''
    (
        job_id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        machine_id INTEGER NOT NULL,
        cpus INTEGER NOT NULL,
        memory INTEGER NOT NULL,
        gpus INTEGER NOT NULL,
        runtime TEXT NOT NULL,
        state TEXT NOT NULL,
        command TEXT NOT NULL,
        end_time TEXT NOT NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES Users (user_id),
        FOREIGN KEY (machine_id) REFERENCES Machines (machine_id)
    )
    '''
    
    cursor.execute("CREATE TABLE IF NOT EXISTS Jobs" + jobs_table_structure)
    
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
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS UserSupervisors (
        id INTEGER PRIMARY KEY,
        student_username TEXT NOT NULL,
        supervisor_username TEXT NOT NULL,
        thesis_title TEXT,
        semester TEXT,
        student_email TEXT,
        UNIQUE(student_username, supervisor_username, thesis_title)
    )
    ''')
    
    # Add end_time column to Jobs table if it does not exist
    try:
        cursor.execute("PRAGMA table_info(Jobs)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'end_time' not in columns:
            cursor.execute("ALTER TABLE Jobs ADD COLUMN end_time TEXT NOT NULL DEFAULT ''")
            print("Added end_time column to Jobs table.")
    except Exception as e:
        print(f"Error checking/adding end_time column: {e}")
    
    # Check and fix Jobs table schema
    try:
        cursor.execute("PRAGMA table_info(Jobs)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'log_id' in columns:
            # Old schema detected - drop and recreate table
            print("Detected old Jobs table schema with log_id. Recreating table...")
            cursor.execute("DROP TABLE Jobs")
            cursor.execute("CREATE TABLE Jobs" + jobs_table_structure)
            print("✅ Recreated Jobs table with new schema")
        elif 'created_at' not in columns:
            # Missing created_at column - add it
            cursor.execute("ALTER TABLE Jobs ADD COLUMN created_at DATETIME")
            print("Added created_at column to Jobs table.")
    except Exception as e:
        print(f"Error checking/fixing Jobs table schema: {e}")
    
    conn.commit()
    conn.close()

