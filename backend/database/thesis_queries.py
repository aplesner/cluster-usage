import logging
from .schema import get_db_connection
from ..config import DB_PATH

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
        
        # Sort the combined result by is_past ASC, semester DESC to ensure proper ordering
        def parse_semester(semester):
            """Parse semester string to get year and type for sorting"""
            if not semester:
                return (0, 0)  # Default for missing semester
            try:
                # Expected format: "HS 2023" or "FS 2023"
                parts = semester.split()
                if len(parts) >= 2:
                    semester_type = parts[0]  # HS or FS
                    year = int(parts[1])
                    # HS (Herbst/Fall) is 2, FS (Frühling/Spring) is 1
                    type_num = 2 if semester_type == 'HS' else 1
                    return (year, type_num)
                else:
                    return (0, 0)
            except (ValueError, IndexError):
                return (0, 0)
        
        # Sort by is_past first (current before past), then by semester (newest first)
        result.sort(key=lambda x: (x['is_past'], -parse_semester(x['semester'])[0], -parse_semester(x['semester'])[1]))
        
        return result
        
    except Exception as e:
        logging.error(f"Error fetching thesis details for user {username}: {e}")
        return []
    finally:
        conn.close() 