import threading
import time
import sqlite3
from datetime import datetime
import logging
import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database.schema import get_db_connection
from config import DB_PATH

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskScheduler:
    def __init__(self, db_path):
        self.db_path = db_path
        self.tasks = {}
        self.running = False
        self.thread = None

    def log_task_execution(self, task_name, status, message=None, details=None):
        """Log a task execution to the database"""
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO PeriodicTaskLogs (timestamp, task_name, status, message, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (datetime.now(), task_name, status, message, details))
            conn.commit()
        except Exception as e:
            logger.error(f"Error logging task execution: {e}")
        finally:
            conn.close()

    def add_task(self, name, func, interval_minutes, initial_delay=0):
        """Add a periodic task to the scheduler, with optional initial delay in seconds"""
        current_time = time.time()
        self.tasks[name] = {
            'func': func,
            'interval': interval_minutes * 60,  # Convert to seconds
            'last_run': current_time + initial_delay - (interval_minutes * 60)
        }
        logger.info(f"Added task '{name}' with interval {interval_minutes} minutes and initial delay {initial_delay} seconds")

    def run_task(self, name, task_info):
        """Run a single task and log its execution"""
        try:
            logger.info(f"Running task '{name}'")
            result = task_info['func']()
            self.log_task_execution(name, 'success', 
                                  message=f"Task completed successfully",
                                  details=str(result))
        except Exception as e:
            logger.error(f"Error running task '{name}': {e}")
            self.log_task_execution(name, 'error',
                                  message=f"Task failed: {str(e)}")

    def run_scheduler(self):
        """Main scheduler loop"""
        while self.running:
            current_time = time.time()
            
            for name, task_info in self.tasks.items():
                if current_time - task_info['last_run'] >= task_info['interval']:
                    self.run_task(name, task_info)
                    task_info['last_run'] = current_time
            
            time.sleep(1)  # Sleep for 1 second before next check

    def start(self):
        """Start the scheduler in a background thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.run_scheduler)
            self.thread.daemon = True  # Thread will exit when main program exits
            self.thread.start()
            logger.info("Task scheduler started")

    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join()
            logger.info("Task scheduler stopped")

# Create a global scheduler instance
scheduler = TaskScheduler(DB_PATH)

def get_task_logs(limit=20, offset=0):
    """Get recent task logs from the database with pagination"""
    conn = get_db_connection(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM PeriodicTaskLogs 
        ORDER BY timestamp DESC 
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return logs

def get_task_logs_count():
    """Get total count of task logs"""
    conn = get_db_connection(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as count FROM PeriodicTaskLogs')
    result = cursor.fetchone()
    count = result[0] if result else 0
    conn.close()
    return count 