from datetime import datetime, timedelta, date
import requests
from icalendar import Calendar
from io import BytesIO
import pytz
import re
import os
import json
import sqlite3
from backend.database import schema
from config import DB_PATH
from backend.database.schema import get_db_connection

# Add this near the top with other imports
CALENDAR_LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'calendar')

def is_valid_user(username):
    """Check if a user exists in the database"""
    conn = get_db_connection(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id FROM Users WHERE username = ?", (username,))
    result = cursor.fetchone()
    
    conn.close()
    return result is not None

def is_valid_resource(resource_name):
    """Check if the resource name matches allowed patterns."""
    # Matches artongpu01-10, tikgpu01-10, tikgpuX
    return re.match(r'^(artongpu(0[1-9]|10)|tikgpu(0[1-9]|10|X))$', resource_name) is not None

def calculate_duration(start_time, end_time):
    """Calculate the duration between start and end time in days and hours"""
    if isinstance(start_time, str):
        start_time = datetime.fromisoformat(start_time)
    if isinstance(end_time, str):
        end_time = datetime.fromisoformat(end_time)
    
    from backend.utils.timezone_utils import get_current_time_cet
    now = get_current_time_cet()
    if end_time < now:
        return "Expired"
        
    duration = end_time - now
    days = duration.days
    hours = duration.seconds // 3600
    
    if days > 0:
        return f"{days} days {hours} hours"
    else:
        return f"{hours} hours"

def ensure_calendar_logs_dir():
    """Ensure the calendar logs directory exists"""
    if not os.path.exists(CALENDAR_LOGS_DIR):
        os.makedirs(CALENDAR_LOGS_DIR)

def write_calendar_entries_to_log(active_events, unparsed_events=[]):
    """Write all active and unparsed calendar entries to their respective log files, overwriting previous entries."""
    ensure_calendar_logs_dir()
    log_file = os.path.join(CALENDAR_LOGS_DIR, 'calendar_today.log')
    with open(log_file, 'w') as f:
        for event in active_events:
            f.write(json.dumps(event) + '\n')
    if unparsed_events is not None:
        unparsed_file = os.path.join(CALENDAR_LOGS_DIR, 'calendar_unparsed.log')
        with open(unparsed_file, 'w') as f:
            for summary in unparsed_events:
                f.write(summary + '\n')

def parse_event_summary(summary):
    """Parse event summary to extract username, resources, and comment.
    Format: username @ resources (comment)
    Resources can be multiple: "4xtikgpu10 6x tikgpu09 2 x tikgpu01, 8x tikgpu001"
    Returns: {
        'username': str,
        'resources': list of (number, resource) tuples,
        'comment': str or None,
        'original': str
    }
    If invalid, returns {'error': reason, 'original': summary}
    """
    summary = summary.strip()
    
    # Step 1: Split by @ to get username and the rest
    if '@' not in summary:
        return {'error': 'missing @', 'original': summary}
    
    username, rest = summary.split('@', 1)
    username = username.strip()
    rest = rest.strip()
    
    # Check if username is valid
    if not is_valid_user(username):
        return {'error': f'invalid username: {username}', 'original': summary}
    
    # Step 2: Extract comment if present
    comment = None
    if '(' in rest and ')' in rest:
        # Find the last occurrence of ( and )
        last_open = rest.rindex('(')
        last_close = rest.rindex(')')
        if last_open < last_close:  # Make sure they're in the right order
            comment = rest[last_open + 1:last_close].strip()
            # Remove the comment from rest
            rest = (rest[:last_open] + rest[last_close + 1:]).strip()
    
    # Step 3: Parse resources
    resources = []
    # Split by commas and spaces to get individual resource entries
    resource_entries = re.split(r'[,\s]+', rest)
    
    current_number = None
    for entry in resource_entries:
        entry = entry.strip()
        if not entry:
            continue
        
        # Try to match patterns like "4x", "4xtikgpu10", "x tikgpu10"
        number_match = re.match(r'^(\d+)?x', entry)
        if number_match:
            # If we found a number, use it
            if number_match.group(1):
                current_number = int(number_match.group(1))
            else:
                current_number = 8  # Default to 8 if no number specified
                
            # Extract the resource name (everything after the x)
            resource = entry[number_match.end():].strip()
            if resource:  # If resource name is in the same entry
                if not is_valid_resource(resource):
                    return {'error': f'invalid resource: {resource}', 'original': summary}
                resources.append((current_number, resource))
                current_number = None
        elif current_number is not None:
            # If we have a number from previous entry, this must be the resource
            if not is_valid_resource(entry):
                return {'error': f'invalid resource: {entry}', 'original': summary}
            resources.append((current_number, entry))
            current_number = None
        else:
            # If no number found, assume 8x
            if not is_valid_resource(entry):
                return {'error': f'invalid resource: {entry}', 'original': summary}
            resources.append((8, entry))
    
    return {
        'username': username,
        'resources': resources,
        'comment': comment,
        'original': summary
    }

def get_active_calendar_events():
    """Task that checks for currently active events in the Google Calendar using the public iCal feed"""
    try:
        # Calendar ID from the embed URL
        calendar_id = '97b9d921cbee75fb048013a177956dff66bef6eafc0cbedcf14b58acad7e414e@group.calendar.google.com'
        
        # Get current time in local timezone
        local_tz = pytz.timezone('Europe/Zurich')  # Adjust this to your timezone
        now = datetime.now(local_tz)
        
        # Construct the iCal feed URL
        url = f'https://calendar.google.com/calendar/ical/{calendar_id}/public/basic.ics'
        
        # Make the request
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse the iCal data
        cal = Calendar.from_ical(response.content)
        
        # Format the events into a readable string
        active_events = []
        log_entries = []
        unparsed_events = []
        
        for event in cal.walk('VEVENT'):
            start = event.get('dtstart').dt
            end = event.get('dtend').dt
            summary = str(event.get('summary', 'No title'))
            

                
            # Convert dates to datetimes for consistent comparison
            if isinstance(start, date) and not isinstance(start, datetime):
                # Convert date to datetime at midnight in local timezone
                start = local_tz.localize(datetime.combine(start, datetime.min.time()))
            elif isinstance(start, datetime) and start.tzinfo is None:
                # If datetime is naive, assume it's in local timezone
                start = local_tz.localize(start)
            elif isinstance(start, datetime):
                # If datetime is timezone-aware, convert to local timezone
                start = start.astimezone(local_tz)
                
            if isinstance(end, date) and not isinstance(end, datetime):
                # Convert date to datetime at midnight in local timezone
                end = local_tz.localize(datetime.combine(end, datetime.min.time()))
            elif isinstance(end, datetime) and end.tzinfo is None:
                # If datetime is naive, assume it's in local timezone
                end = local_tz.localize(end)
            elif isinstance(end, datetime):
                # If datetime is timezone-aware, convert to local timezone
                end = end.astimezone(local_tz)
            
            # Check if the event is currently active
            is_active = start <= now <= end

            if not is_active:
                continue

            # Parse the event summary
            parsed_event = parse_event_summary(summary)
            if 'error' in parsed_event:
                unparsed_events.append(f"{summary} [reason: {parsed_event['error']}]")
                continue
 
            if is_active and parsed_event:
                # Only include events for users that exist in the database
                    
                # Calculate duration
                duration = calculate_duration(start, end)
                if duration == "Expired":
                    continue
                
                # Create log entry
                from backend.utils.timezone_utils import get_datetime_cet_isoformat
                log_entry = {
                    'timestamp': get_datetime_cet_isoformat(),
                    'username': parsed_event['username'],
                    'resources': parsed_event['resources'],
                    'comment': parsed_event['comment'],
                    'start_time': start.isoformat(),
                    'end_time': end.isoformat(),
                    'duration': duration,
                    'original_summary': parsed_event['original']
                }
                log_entries.append(log_entry)
                
                # Format the event details for display
                details = [
                    f"User: {parsed_event['username']}",
                    f"Resources: [{', '.join([f'{num}x {resource}' for num, resource in parsed_event['resources']])}]",
                    f"Duration: {duration}"
                ]
                if parsed_event['comment']:
                    details.append(f"Comment: {parsed_event['comment']}")
                
                active_events.append('\n'.join(details))
        
        # Write all entries to log file at once
        write_calendar_entries_to_log(log_entries, unparsed_events)
        
        result = {
            'active_events': active_events,
            'unparsed_events': unparsed_events
        }
        if not active_events:
            result['message'] = "No active events found at the current time."
        return result
        
    except requests.exceptions.RequestException as e:
        return f"Error fetching calendar events: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}" 