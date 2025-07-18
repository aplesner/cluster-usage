from flask import Blueprint, jsonify, request, current_app, send_from_directory
import os
import sys
import json
from datetime import datetime, timedelta

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database.queries import (
    get_database_stats, get_all_users, get_all_machines,
    get_user_usage, get_machine_usage, get_time_usage, get_size_distribution,
    get_time_stats_for_user, get_top_users_recent_logs, get_historic_usage,
    get_historic_usage_per_user, get_user_thesis_and_supervisors, get_all_theses_and_supervisors
)
from backend.tasks.periodic_tasks import get_task_logs, get_task_logs_count
from backend.tasks.calendar_tasks import CALENDAR_LOGS_DIR
from backend.database.schema import get_db_connection
from backend.parsers.slurm_parser import (
    parse_slurm_log, 
    get_current_usage_summary,
    store_slurm_jobs,
    SlurmJob
)
from backend.email_notifications.email_notifications import get_email_notifications, get_email_notifications_count, get_email_counts_by_user

api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/stats', methods=['GET'])
def stats():
    """Get overall database statistics"""
    db_path = current_app.config['DB_PATH']
    stats = get_database_stats(db_path)
    return jsonify(stats)

@api.route('/users', methods=['GET'])
def users():
    """Get all users"""
    db_path = current_app.config['DB_PATH']
    users_list = get_all_users(db_path)
    return jsonify(users_list)

@api.route('/machines', methods=['GET'])
def machines():
    """Get all machines"""
    db_path = current_app.config['DB_PATH']
    machines_list = get_all_machines(db_path)
    return jsonify(machines_list)

@api.route('/usage/user/<username>', methods=['GET'])
def user_usage(username):
    """Get usage statistics for a specific user"""
    db_path = current_app.config['DB_PATH']
    user_data = get_user_usage(db_path, username=username)
    
    if not user_data:
        return jsonify({'error': f'User {username} not found'}), 404
    
    return jsonify(user_data)

@api.route('/usage/machine/<machine_name>', methods=['GET'])
def machine_usage(machine_name):
    """Get usage statistics for a specific machine"""
    db_path = current_app.config['DB_PATH']
    machine_data = get_machine_usage(db_path, machine_name=machine_name)
    
    if not machine_data:
        return jsonify({'error': f'Machine {machine_name} not found'}), 404
    
    return jsonify(machine_data)

@api.route('/usage/time', methods=['GET'])
def time_usage():
    """Get time-based usage statistics"""
    db_path = current_app.config['DB_PATH']
    time_data = get_time_usage(db_path)
    return jsonify(time_data)

@api.route('/usage/size', methods=['GET'])
def size_usage():
    """Get size distribution statistics"""
    db_path = current_app.config['DB_PATH']
    size_data = get_size_distribution(db_path)
    return jsonify(size_data)

@api.route('/usage/user/<username>/time', methods=['GET'])
def user_time_stats(username):
    """Get time-based usage statistics for a specific user"""
    db_path = current_app.config['DB_PATH']
    time_data = get_time_stats_for_user(db_path, username)
    return jsonify(time_data)

@api.route('/top-users/recent', methods=['GET'])
def top_users_recent():
    """Get top users by IO operations for recent logs"""
    db_path = current_app.config['DB_PATH']
    log_count = request.args.get('logs', default=5, type=int)
    user_count = request.args.get('users', default=10, type=int)
    users_data = get_top_users_recent_logs(db_path, log_count, user_count)
    return jsonify(users_data)

@api.route('/usage/historic', methods=['GET'])
def historic_usage():
    """Get historic usage data with top N users for each log entry"""
    db_path = current_app.config['DB_PATH']
    top_n = request.args.get('top_n', default=10, type=int)
    historic_data = get_historic_usage(db_path, top_n)
    return jsonify(historic_data)

@api.route('/task-logs', methods=['GET'])
def task_logs():
    """Get periodic task logs with pagination"""
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=20, type=int)
    offset = (page - 1) * limit
    
    logs = get_task_logs(limit=limit, offset=offset)
    total_count = get_task_logs_count()
    
    return jsonify({
        'logs': logs,
        'pagination': {
            'page': page,
            'limit': limit,
            'total': total_count,
            'pages': (total_count + limit - 1) // limit
        }
    })

@api.route('/email-notifications', methods=['GET'])
def email_notifications():
    """Get email notifications with pagination"""
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=20, type=int)
    offset = (page - 1) * limit
    
    notifications = get_email_notifications(limit=limit, offset=offset)
    total_count = get_email_notifications_count()
    
    return jsonify({
        'notifications': notifications,
        'pagination': {
            'page': page,
            'limit': limit,
            'total': total_count,
            'pages': (total_count + limit - 1) // limit
        }
    })

@api.route('/email-notifications/counts', methods=['GET'])
def email_notifications_counts():
    """Get number of sent emails to each user for a given time range"""
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    if not start_time or not end_time:
        return jsonify({'error': 'start_time and end_time query parameters are required (ISO format)'}), 400
    try:
        # Validate time format (will raise if invalid)
        from datetime import datetime
        datetime.fromisoformat(start_time)
        datetime.fromisoformat(end_time)
    except Exception:
        return jsonify({'error': 'Invalid time format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)'}), 400
    counts = get_email_counts_by_user(start_time, end_time)
    return jsonify({'counts': counts})

@api.route('/calendar/active', methods=['GET'])
def get_active_calendar_events():
    """Get currently active calendar events from the log file and unparsed events if available"""
    try:
        log_file = os.path.join(CALENDAR_LOGS_DIR, 'calendar_today.log')
        unparsed_file = os.path.join(CALENDAR_LOGS_DIR, 'calendar_unparsed.log')
        events = []
        unparsed_events = []
        conn = get_db_connection(current_app.config['DB_PATH'])
        cursor = conn.cursor()
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        event = json.loads(line)
                        cursor.execute("SELECT user_role FROM Users WHERE username = ?", (event['username'],))
                        result = cursor.fetchone()
                        user_role = result[0] if result else None
                        events.append({
                            'username': event['username'],
                            'user_role': user_role,
                            'resources': event['resources'],
                            'comment': event['comment'],
                            'start_time': event['start_time'],
                            'end_time': event['end_time'],
                            'duration': event['duration'],
                            'timestamp': event['timestamp']
                        })
        if os.path.exists(unparsed_file):
            with open(unparsed_file, 'r') as f:
                for line in f:
                    if line.strip():
                        unparsed_events.append(line.strip())
        conn.close()
        return jsonify({'active_events': events, 'unparsed_events': unparsed_events})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/calendar/last-refresh', methods=['GET'])
def get_calendar_last_refresh():
    """Return the last modification time of calendar_today.log as an ISO string."""
    try:
        from backend.tasks.calendar_tasks import CALENDAR_LOGS_DIR
        log_file = os.path.join(CALENDAR_LOGS_DIR, 'calendar_today.log')
        mtime = os.path.getmtime(log_file)
        dt = datetime.fromtimestamp(mtime)
        return jsonify({'last_refresh': dt.isoformat()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/calendar/current-usage', methods=['GET'])
def get_current_usage():
    """Get current resource usage from Slurm logs (now from DB only)"""
    try:
        db_path = current_app.config['DB_PATH']
        usage_summary, log_timestamp = get_current_usage_summary(db_path)

        return jsonify({
            'timestamp': log_timestamp,
            'usage': usage_summary
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/users/<username>/overview', methods=['GET'])
def get_user_overview(username):
    try:
        db_path = current_app.config['DB_PATH']
        
        # Get current usage
        current_usage = get_user_current_usage(username, db_path)
        
        # Get running jobs
        running_jobs = get_user_running_jobs(username, db_path)
        
        # Get job history (last 100 jobs)
        job_history = get_user_job_history(username, db_path, limit=100)
        
        return jsonify({
            'currentUsage': current_usage,
            'runningJobs': running_jobs,
            'jobHistory': job_history
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_user_current_usage(username, db_path):
    """Get current resource usage for a specific user"""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        
        # Get the latest log entry
        cursor.execute("""
            SELECT log_id, unix_timestamp 
            FROM LogEntries 
            ORDER BY unix_timestamp DESC 
            LIMIT 1
        """)
        latest_log = cursor.fetchone()
        if not latest_log:
            return None
            
        log_id = latest_log[0]
        
        # Get user's current usage from the latest log using the Jobs table
        cursor.execute("""
            SELECT 
                m.machine_name as host,
                SUM(j.cpus) as total_cpus,
                SUM(j.memory) as total_memory,
                SUM(j.gpus) as total_gpus
            FROM Jobs j
            JOIN Machines m ON j.machine_id = m.machine_id
            JOIN Users u ON j.user_id = u.user_id
            WHERE j.log_id = ? AND u.username = ? AND j.state = 'RUNNING'
            GROUP BY m.machine_name
        """, (log_id, username))
        
        hosts = []
        total_cpus = 0
        total_memory = 0
        total_gpus = 0
        
        for row in cursor.fetchall():
            host = {
                'name': row[0],
                'cpus': row[1] or 0,
                'memory': row[2] or 0,
                'gpus': row[3] or 0
            }
            hosts.append(host)
            total_cpus += row[1] or 0
            total_memory += row[2] or 0
            total_gpus += row[3] or 0
            
        return {
            'hosts': hosts,
            'totalCpus': total_cpus,
            'totalMemory': total_memory,
            'totalGpus': total_gpus
        }
    finally:
        conn.close()

def get_user_running_jobs(username, db_path):
    """Get currently running jobs for a specific user"""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        
        # Get running jobs from the latest log
        cursor.execute("""
            SELECT 
                j.job_id,
                m.machine_name as host,
                j.cpus,
                j.memory,
                j.gpus,
                j.runtime,
                j.state,
                j.command,
                j.end_time
            FROM Jobs j
            JOIN Machines m ON j.machine_id = m.machine_id
            JOIN Users u ON j.user_id = u.user_id
            JOIN LogEntries l ON j.log_id = l.log_id
            WHERE u.username = ? 
            AND j.state = 'RUNNING'
            AND l.unix_timestamp = (
                SELECT MAX(unix_timestamp) 
                FROM LogEntries
            )
            ORDER BY j.job_id DESC
        """, (username,))
        
        jobs = []
        for row in cursor.fetchall():
            job = {
                'jobId': row[0],
                'host': row[1],
                'cpus': row[2],
                'memory': row[3],
                'gpus': row[4],
                'runtime': row[5],
                'state': row[6],
                'command': row[7],
                'endTime': row[8]
            }
            jobs.append(job)
            
        return jobs
    finally:
        conn.close()

def get_user_job_history(username, db_path, limit=100):
    """Get job history for a specific user"""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        
        # Get job history
        cursor.execute("""
            SELECT 
                j.job_id,
                m.machine_name as host,
                j.cpus,
                j.memory,
                j.gpus,
                j.runtime,
                j.state,
                j.command,
                l.timestamp as start_time,
                j.end_time
            FROM Jobs j
            JOIN Machines m ON j.machine_id = m.machine_id
            JOIN Users u ON j.user_id = u.user_id
            JOIN LogEntries l ON j.log_id = l.log_id
            WHERE u.username = ?
            ORDER BY l.unix_timestamp DESC, j.job_id DESC
            LIMIT ?
        """, (username, limit))
        
        jobs = []
        for row in cursor.fetchall():
            job = {
                'jobId': row[0],
                'host': row[1],
                'cpus': row[2],
                'memory': row[3],
                'gpus': row[4],
                'runtime': row[5],
                'state': row[6],
                'command': row[7],
                'startTime': row[8],
                'endTime': row[9]
            }
            jobs.append(job)
            
        return jobs
    finally:
        conn.close()

@api.route('/users/<username>/thesis-supervisors', methods=['GET'])
def get_user_thesis_supervisors(username):
    db_path = current_app.config['DB_PATH']
    result = get_user_thesis_and_supervisors(db_path, username)
    if not result:
        return jsonify({'error': 'No thesis or supervisor information found'}), 404
    return jsonify(result)

@api.route('/users/<username>/historic-usage', methods=['GET'])
def get_user_historic_usage(username):
    """Get historic GPU usage for a specific user, grouped by machine"""
    try:
        db_path = current_app.config['DB_PATH']
        usage_data = get_historic_usage_per_user(db_path, username)
        return jsonify(usage_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/historic-usage', methods=['GET'])
def get_all_historic_usage():
    """Get historic GPU usage for all users, grouped by machine"""
    try:
        db_path = current_app.config['DB_PATH']
        usage_data = get_historic_usage_per_user(db_path)
        return jsonify(usage_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/users/gpu-hours', methods=['GET'])
def get_all_users_gpu_hours():
    """Return the total GPU hours for all users, summed across all machines."""
    try:
        db_path = current_app.config['DB_PATH']
        usage_by_user = get_historic_usage_per_user(db_path)
        result = {}
        for username, machines in usage_by_user.items():
            gpu_hours = 0.0
            for machine, stats in machines.items():
                gpu_hours += stats.get('total_gpu_hours', 0.0)
            result[username] = gpu_hours
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/users/emails-last-12h', methods=['GET'])
def get_users_emailed_last_12h():
    """Return a list of usernames who received an email from the system in the last 12 hours."""
    try:
        db_path = current_app.config['DB_PATH']
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        twelve_hours_ago = datetime.now() - timedelta(hours=12)
        # Query PeriodicTaskLogs for recent email notifications
        cursor.execute("""
            SELECT message FROM PeriodicTaskLogs
            WHERE task_name LIKE 'email-%' AND timestamp >= ?
        """, (twelve_hours_ago.strftime('%Y-%m-%d %H:%M:%S'),))
        import re
        emailed_users = set()
        pattern = re.compile(r"Email notification sent to ([^\s]+)")
        for row in cursor.fetchall():
            message = row[0]
            match = pattern.search(message or "")
            if match:
                emailed_users.add(match.group(1))
        conn.close()
        return jsonify({'emailed_users': list(emailed_users)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/theses-supervisors', methods=['GET'])
def get_all_theses_supervisors():
    db_path = current_app.config['DB_PATH']
    result = get_all_theses_and_supervisors(db_path)
    return jsonify(result)

