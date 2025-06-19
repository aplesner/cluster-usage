import os
import sys
import argparse
import sqlite3
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

# Add the parent directory to the Python path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import (
    DATA_DIR, DB_PATH, INCOMING_LOGS_DIR, ARCHIVE_LOGS_DIR, 
    API_PREFIX, DEBUG, HOST, PORT
)
from backend.database import schema # import initialize_database, get_db_connection
from api import routes # import api
from parsers import log_parser # import process_log_file
from backend.tasks.periodic_tasks import scheduler
from backend.tasks.example_tasks import log_current_time
from backend.tasks.calendar_tasks import get_active_calendar_events
from backend.tasks.check_reservation import check_reservation_activity

# Create Flask app
app = Flask(__name__, static_folder=None)
app.config['DB_PATH'] = DB_PATH
app.config['INCOMING_LOGS_DIR'] = INCOMING_LOGS_DIR
app.config['ARCHIVE_LOGS_DIR'] = ARCHIVE_LOGS_DIR

# Enable CORS for all routes and origins
CORS(app)

# Register API blueprint
app.register_blueprint(routes.api, url_prefix=API_PREFIX)

# Route for home page - serve static files from frontend build
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    # This assumes you've built the frontend and placed it in a 'build' directory
    frontend_build_dir = os.path.join(os.path.dirname(app.root_path), 'frontend', 'build')
    
    if path == "" or path == "/":
        return send_from_directory(frontend_build_dir, 'index.html')
    
    # Try to serve the requested file
    try:
        return send_from_directory(frontend_build_dir, path)
    except:
        # If the file doesn't exist, return the index.html for client-side routing
        return send_from_directory(frontend_build_dir, 'index.html')

def find_log_files(directory):
    """Find all log files in the given directory"""
    import glob
    log_files = glob.glob(os.path.join(directory, "*.log"))
    return log_files

def init_database():
    """Initialize the database"""
    if not os.path.exists(os.path.dirname(DB_PATH)):
        os.makedirs(os.path.dirname(DB_PATH))
    
    schema.initialize_database(DB_PATH)
    print(f"Database initialized at {DB_PATH}")
    return True

def process_logs(incoming_dir=INCOMING_LOGS_DIR, archive_dir=ARCHIVE_LOGS_DIR):
    """Process all log files in the incoming directory"""
    log_files = find_log_files(incoming_dir)
    
    if not log_files:
        print(f"No log files found in {incoming_dir}")
        return True
    
    print(f"Found {len(log_files)} log files to process")
    
    conn = schema.get_db_connection(DB_PATH)
    processed_count = 0
    
    for log_file in log_files:
        print(f"Processing {log_file}...")
        if log_parser.process_log_file(conn, log_file, archive_dir):
            processed_count += 1
    
    conn.close()
    
    print(f"Processed {processed_count} out of {len(log_files)} log files")
    return processed_count == len(log_files)

def process_specific_log(log_path, archive_dir=None):
    """Process a specific log file"""
    if not os.path.exists(log_path):
        print(f"Log file not found: {log_path}")
        return False
    
    conn = schema.get_db_connection(DB_PATH)
    result = log_parser.process_log_file(conn, log_path, archive_dir)
    conn.close()
    
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='IO Usage Dashboard Backend')
    parser.add_argument('action', choices=['run', 'init', 'process_logs', 'process_file'], 
                       help='Action to perform')
    parser.add_argument('--file', help='Path to log file for process_file action')
    parser.add_argument('--archive', action='store_true', help='Archive processed files')
    
    # In case no arguments provided, default to 'run'
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    if args.action == 'init':
        init_database()
    elif args.action == 'process_logs':
        if not os.path.exists(DB_PATH):
            print(f"Database not found at {DB_PATH}. Initializing...")
            init_database()
        archive_dir = ARCHIVE_LOGS_DIR if args.archive else None
        process_logs(archive_dir=archive_dir)
    elif args.action == 'process_file':
        if not args.file:
            print("Error: --file argument is required for process_file action")
            sys.exit(1)
        if not os.path.exists(DB_PATH):
            print(f"Database not found at {DB_PATH}. Initializing...")
            init_database()
        archive_dir = ARCHIVE_LOGS_DIR if args.archive else None
        process_specific_log(args.file, archive_dir)
    elif args.action == 'run':
        if not os.path.exists(DB_PATH):
            print(f"Database not found at {DB_PATH}. Initializing...")
            init_database()
        
        # Register and start the example task
        scheduler.add_task("time_logger", log_current_time, interval_minutes=4*60)
        print("Registered time_logger task (runs every minute)")
        
        # Register and start the calendar task
        scheduler.add_task("calendar_checker", get_active_calendar_events, interval_minutes=10)
        print("Registered calendar_checker task (runs every minute)")
        
        # Register and start the reservation check task
        scheduler.add_task("reservation_checker", check_reservation_activity, interval_minutes=4*60)
        print("Registered reservation_checker task (runs every minutes)")
        
        # Start the task scheduler
        scheduler.start()
        
        try:
            app.run(host=HOST, port=PORT, debug=DEBUG)
        finally:
            # Stop the scheduler when the app stops
            scheduler.stop()