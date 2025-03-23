import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database.schema import get_db_connection

def get_database_stats(db_path: str):
    """Get overall database statistics"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    stats = {}
    
    # Count of log entries
    cursor.execute("SELECT COUNT(*) as count FROM LogEntries")
    stats['log_count'] = cursor.fetchone()['count']
    
    # Count of users
    cursor.execute("SELECT COUNT(*) as count FROM Users")
    stats['user_count'] = cursor.fetchone()['count']
    
    # Count of machines
    cursor.execute("SELECT COUNT(*) as count FROM Machines")
    stats['machine_count'] = cursor.fetchone()['count']
    
    # Count of user sessions
    cursor.execute("SELECT COUNT(*) as count FROM UserSessions")
    stats['session_count'] = cursor.fetchone()['count']
    
    # Count of IO operations
    cursor.execute("SELECT COUNT(*) as count FROM IOOperations")
    stats['operation_count'] = cursor.fetchone()['count']
    
    # Total operations across all sessions
    cursor.execute("SELECT SUM(operation_count) as total FROM IOOperations")
    stats['total_operations'] = cursor.fetchone()['total'] or 0
    
    # Date range
    cursor.execute("SELECT MIN(timestamp) as min_date, MAX(timestamp) as max_date FROM LogEntries")
    result = cursor.fetchone()
    stats['min_date'] = result['min_date']
    stats['max_date'] = result['max_date']
    
    conn.close()
    return stats

def get_all_users(db_path: str):
    """Get list of all users with basic stats"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    query = """
    SELECT 
        u.user_id, 
        u.username, 
        u.user_role, 
        u.user_affiliation,
        COUNT(DISTINCT us.session_id) as session_count,
        COUNT(DISTINCT m.machine_id) as machine_count
    FROM 
        Users u
    LEFT JOIN 
        UserSessions us ON u.user_id = us.user_id
    LEFT JOIN 
        Machines m ON us.machine_id = m.machine_id
    GROUP BY 
        u.user_id
    ORDER BY 
        session_count DESC
    """
    
    cursor.execute(query)
    users = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return users


def get_all_machines(db_path: str):
    """Get list of all machines with basic stats"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    query = """
    SELECT 
        m.machine_id, 
        m.machine_name, 
        m.machine_type,
        COUNT(DISTINCT us.session_id) as session_count,
        COUNT(DISTINCT u.user_id) as user_count
    FROM 
        Machines m
    LEFT JOIN 
        UserSessions us ON m.machine_id = us.machine_id
    LEFT JOIN 
        Users u ON us.user_id = u.user_id
    GROUP BY 
        m.machine_id
    ORDER BY 
        session_count DESC
    """
    
    cursor.execute(query)
    machines = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return machines

def get_user_usage(db_path: str, username: str=None, user_id=None):
    """Get detailed usage statistics for a specific user"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    if username is not None:
        where_clause = "WHERE u.username = ?"
        param = username
    elif user_id is not None:
        where_clause = "WHERE u.user_id = ?"
        param = user_id
    else:
        conn.close()
        return None
    
    # Get user details
    query = f"""
    SELECT 
        u.user_id, 
        u.username, 
        u.user_role, 
        u.user_affiliation
    FROM 
        Users u
    {where_clause}
    """
    
    cursor.execute(query, (param,))
    user = dict(cursor.fetchone() or {})
    
    if not user:
        conn.close()
        return None
    
    # Get user's machines
    query = f"""
    SELECT 
        m.machine_id, 
        m.machine_name, 
        m.machine_type,
        COUNT(DISTINCT us.session_id) as session_count
    FROM 
        Machines m
    JOIN 
        UserSessions us ON m.machine_id = us.machine_id
    JOIN 
        Users u ON us.user_id = u.user_id
    {where_clause}
    GROUP BY 
        m.machine_id
    ORDER BY 
        session_count DESC
    """
    
    cursor.execute(query, (param,))
    user['machines'] = [dict(row) for row in cursor.fetchall()]
    
    # Get user's IO patterns
    query = f"""
    SELECT 
        r.display_text, 
        SUM(io.operation_count) as total_operations
    FROM 
        IOOperations io
    JOIN 
        UserSessions us ON io.session_id = us.session_id
    JOIN 
        Users u ON us.user_id = u.user_id
    JOIN 
        IOSizeRanges r ON io.range_id = r.range_id
    {where_clause}
    GROUP BY 
        r.display_text
    ORDER BY 
        r.min_bytes
    """
    
    cursor.execute(query, (param,))
    user['io_distribution'] = [dict(row) for row in cursor.fetchall()]
    
    # Get user's time series usage
    query = f"""
    SELECT 
        l.timestamp, 
        SUM(io.operation_count) as total_operations
    FROM 
        IOOperations io
    JOIN 
        UserSessions us ON io.session_id = us.session_id
    JOIN 
        Users u ON us.user_id = u.user_id
    JOIN 
        LogEntries l ON us.log_id = l.log_id
    {where_clause}
    GROUP BY 
        l.timestamp
    ORDER BY 
        l.timestamp
    """
    
    cursor.execute(query, (param,))
    user['time_series'] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return user

def get_machine_usage(db_path: str, machine_name: str=None, machine_id=None):
    """Get detailed usage statistics for a specific machine"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    if machine_name is not None:
        where_clause = "WHERE m.machine_name = ?"
        param = machine_name
    elif machine_id is not None:
        where_clause = "WHERE m.machine_id = ?"
        param = machine_id
    else:
        conn.close()
        return None
    
    # Get machine details
    query = f"""
    SELECT 
        m.machine_id, 
        m.machine_name, 
        m.machine_type
    FROM 
        Machines m
    {where_clause}
    """
    
    cursor.execute(query, (param,))
    machine = dict(cursor.fetchone() or {})
    
    if not machine:
        conn.close()
        return None
    
    # Get machine's users
    query = f"""
    SELECT 
        u.user_id, 
        u.username, 
        u.user_role, 
        u.user_affiliation,
        COUNT(DISTINCT us.session_id) as session_count
    FROM 
        Users u
    JOIN 
        UserSessions us ON u.user_id = us.user_id
    JOIN 
        Machines m ON us.machine_id = m.machine_id
    {where_clause}
    GROUP BY 
        u.user_id
    ORDER BY 
        session_count DESC
    """
    
    cursor.execute(query, (param,))
    machine['users'] = [dict(row) for row in cursor.fetchall()]
    
    # Get machine's IO patterns
    query = f"""
    SELECT 
        r.display_text, 
        SUM(io.operation_count) as total_operations
    FROM 
        IOOperations io
    JOIN 
        UserSessions us ON io.session_id = us.session_id
    JOIN 
        Machines m ON us.machine_id = m.machine_id
    JOIN 
        IOSizeRanges r ON io.range_id = r.range_id
    {where_clause}
    GROUP BY 
        r.display_text
    ORDER BY 
        r.min_bytes
    """
    
    cursor.execute(query, (param,))
    machine['io_distribution'] = [dict(row) for row in cursor.fetchall()]
    
    # Get machine's time series usage
    query = f"""
    SELECT 
        l.timestamp, 
        SUM(io.operation_count) as total_operations
    FROM 
        IOOperations io
    JOIN 
        UserSessions us ON io.session_id = us.session_id
    JOIN 
        Machines m ON us.machine_id = m.machine_id
    JOIN 
        LogEntries l ON us.log_id = l.log_id
    {where_clause}
    GROUP BY 
        l.timestamp
    ORDER BY 
        l.timestamp
    """
    
    cursor.execute(query, (param,))
    machine['time_series'] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return machine

def get_time_usage(db_path: str):
    """Get time-based usage statistics"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    # Get overall time series
    query = """
    SELECT 
        l.timestamp, 
        SUM(io.operation_count) as total_operations,
        COUNT(DISTINCT us.user_id) as active_users,
        COUNT(DISTINCT us.machine_id) as active_machines
    FROM 
        IOOperations io
    JOIN 
        UserSessions us ON io.session_id = us.session_id
    JOIN 
        LogEntries l ON us.log_id = l.log_id
    GROUP BY 
        l.timestamp
    ORDER BY 
        l.timestamp
    """
    
    cursor.execute(query)
    time_usage = {
        'time_series': [dict(row) for row in cursor.fetchall()]
    }
    
    # Get hourly patterns (hour of day)
    query = """
    SELECT 
        strftime('%H', timestamp) as hour,
        SUM(io.operation_count) as total_operations
    FROM 
        IOOperations io
    JOIN 
        UserSessions us ON io.session_id = us.session_id
    JOIN 
        LogEntries l ON us.log_id = l.log_id
    GROUP BY 
        hour
    ORDER BY 
        hour
    """
    
    cursor.execute(query)
    time_usage['hourly_pattern'] = [dict(row) for row in cursor.fetchall()]
    
    # Get daily patterns (day of week)
    query = """
    SELECT 
        strftime('%w', timestamp) as day_of_week,
        SUM(io.operation_count) as total_operations
    FROM 
        IOOperations io
    JOIN 
        UserSessions us ON io.session_id = us.session_id
    JOIN 
        LogEntries l ON us.log_id = l.log_id
    GROUP BY 
        day_of_week
    ORDER BY 
        day_of_week
    """
    
    cursor.execute(query)
    time_usage['daily_pattern'] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return time_usage

def get_size_distribution(db_path: str):
    """Get IO size distribution statistics"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    # Get overall size distribution
    query = """
    SELECT 
        r.display_text, 
        r.min_bytes,
        r.max_bytes,
        SUM(io.operation_count) as total_operations
    FROM 
        IOOperations io
    JOIN 
        IOSizeRanges r ON io.range_id = r.range_id
    GROUP BY 
        r.range_id
    ORDER BY 
        r.min_bytes
    """
    
    cursor.execute(query)
    size_dist = {
        'overall': [dict(row) for row in cursor.fetchall()]
    }
    
    # Get size distribution by user role
    query = """
    SELECT 
        u.user_role,
        r.display_text, 
        SUM(io.operation_count) as total_operations
    FROM 
        IOOperations io
    JOIN 
        UserSessions us ON io.session_id = us.session_id
    JOIN 
        Users u ON us.user_id = u.user_id
    JOIN 
        IOSizeRanges r ON io.range_id = r.range_id
    WHERE
        u.user_role IS NOT NULL
    GROUP BY 
        u.user_role, r.display_text
    ORDER BY 
        u.user_role, r.min_bytes
    """
    
    cursor.execute(query)
    roles_data = cursor.fetchall()
    
    # Process role-based data into a structured format
    roles = {}
    for row in roles_data:
        role = row['user_role']
        if role not in roles:
            roles[role] = []
        roles[role].append({
            'display_text': row['display_text'],
            'total_operations': row['total_operations']
        })
    
    size_dist['by_role'] = roles
    
    # Get size distribution by machine type
    query = """
    SELECT 
        m.machine_type,
        r.display_text, 
        SUM(io.operation_count) as total_operations
    FROM 
        IOOperations io
    JOIN 
        UserSessions us ON io.session_id = us.session_id
    JOIN 
        Machines m ON us.machine_id = m.machine_id
    JOIN 
        IOSizeRanges r ON io.range_id = r.range_id
    GROUP BY 
        m.machine_type, r.display_text
    ORDER BY 
        m.machine_type, r.min_bytes
    """
    
    cursor.execute(query)
    machines_data = cursor.fetchall()
    
    # Process machine-based data into a structured format
    machine_types = {}
    for row in machines_data:
        mtype = row['machine_type']
        if mtype not in machine_types:
            machine_types[mtype] = []
        machine_types[mtype].append({
            'display_text': row['display_text'],
            'total_operations': row['total_operations']
        })
    
    size_dist['by_machine_type'] = machine_types
    
    conn.close()
    return size_dist


def get_time_stats_for_user(db_path, username):
    """Get time-based usage statistics for a user with zeros filled in"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Get all timestamps
    cursor.execute("SELECT DISTINCT timestamp FROM LogEntries ORDER BY timestamp")
    all_timestamps = [row['timestamp'] for row in cursor.fetchall()]

    # Get user data
    query = """
    SELECT
        l.timestamp,
        SUM(io.operation_count) as total_operations
    FROM
        IOOperations io
    JOIN
        UserSessions us ON io.session_id = us.session_id
    JOIN
        Users u ON us.user_id = u.user_id
    JOIN
        LogEntries l ON us.log_id = l.log_id
    WHERE
        u.username = ?
    GROUP BY
        l.timestamp
    ORDER BY
        l.timestamp
    """

    cursor.execute(query, (username,))
    user_timestamps = {row['timestamp']: row['total_operations'] for row in cursor.fetchall()}

    # Fill in missing timestamps with zeros
    time_series = []
    for timestamp in all_timestamps:
        time_series.append({
            'timestamp': timestamp,
            'total_operations': user_timestamps.get(timestamp, 0)
        })

    conn.close()
    return time_series

def get_top_users_recent_logs(db_path, log_count=5, user_count=10):
    """Get top users by IO operations for the most recent logs"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    query = """
    WITH RecentLogs AS (
        SELECT log_id, timestamp
        FROM LogEntries
        ORDER BY timestamp DESC
        LIMIT ?
    )
    SELECT
        u.username,
        u.user_role,
        u.user_affiliation,
        SUM(io.operation_count) as total_operations,
        COUNT(DISTINCT us.session_id) as session_count,
        COUNT(DISTINCT m.machine_id) as machine_count,
        GROUP_CONCAT(DISTINCT m.machine_name) as machines
    FROM
        IOOperations io
    JOIN
        UserSessions us ON io.session_id = us.session_id
    JOIN
        Users u ON us.user_id = u.user_id
    JOIN
        Machines m ON us.machine_id = m.machine_id
    JOIN
        RecentLogs rl ON us.log_id = rl.log_id
    GROUP BY
        u.user_id
    ORDER BY
        total_operations DESC
    LIMIT ?
    """

    cursor.execute(query, (log_count, user_count))
    users = [dict(row) for row in cursor.fetchall()]

    # Get timestamp range for the recent logs
    cursor.execute("""
    WITH RecentLogs AS (
        SELECT timestamp
        FROM LogEntries
        ORDER BY timestamp DESC
        LIMIT ?
    )
    SELECT MIN(timestamp) as min_date, MAX(timestamp) as max_date
    FROM RecentLogs;
    """, (log_count,))

    date_range = dict(cursor.fetchone())

    conn.close()
    return {
        'users': users,
        'date_range': date_range
    }

