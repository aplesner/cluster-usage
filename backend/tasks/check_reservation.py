from datetime import datetime
from typing import Dict, List, Optional
import logging
import os
import json
import requests
from dataclasses import dataclass

from ..database.schema import get_db_connection
from ..parsers.slurm_parser import get_current_usage_summary, parse_slurm_log
from .calendar_tasks import get_active_calendar_events, CALENDAR_LOGS_DIR
from ..config import DB_PATH, HOST, PORT
from ..email_notifications import send_email

logger = logging.getLogger(__name__)

@dataclass
class ReservationActivity:
    username: str
    reservation_resources: Dict[str, int]  # resource_name -> count
    actual_usage: Dict[str, int]  # resource_name -> count
    is_active: bool
    hosts_used: List[str]
    timestamp: datetime

def check_reservation_activity():
    """
    Task that checks activity for all active reservations by comparing with current cluster usage.
    Returns a dict with activity status for each reservation.
    """
    try:
        # Get active reservations from the log file
        log_file = os.path.join(CALENDAR_LOGS_DIR, 'calendar_today.log')
        if not os.path.exists(log_file):
            return {"error": "No calendar log file found - no active reservations"}
            
        active_reservations = []
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    reservation = json.loads(line.strip())
                    active_reservations.append(reservation)
                except json.JSONDecodeError:
                    continue
        
        if not active_reservations:
            return {"status": "success", "message": "No active reservations found"}
        
        # Get current cluster usage and ensure Slurm data is parsed
        slurm_log_file = os.path.join(CALENDAR_LOGS_DIR, 'slurm', 'slurm.log')
        if not os.path.exists(slurm_log_file):
            return {"error": "Slurm log file not found"}
            
        with open(slurm_log_file, 'r') as f:
            log_content = f.read()
        jobs = parse_slurm_log(log_content)
        
        
        # Check each reservation
        reservation_activities = []
        for reservation in active_reservations:
            username = reservation['username']
            current_user_usage_by_host = get_user_gpu_usage_by_host_api(username)
           
            # Parse reservation resources
            reservation_resources = {}
            for num, resource in reservation['resources']:


                reservation_resources[resource] = num
           
            # Check if at least 50% of each reserved resource is being used
            is_active = True
            resource_usage_status = {}
            
            for resource_name, reserved_amount in reservation_resources.items():
                # Get actual usage for this specific resource (host)
                actual_amount = current_user_usage_by_host.get(resource_name, 0)
                
                # Check if at least 50% of the reserved resource is being used
                usage_percentage = actual_amount / reserved_amount if reserved_amount > 0 else 0
                is_resource_active = usage_percentage >= 0.5
                
                resource_usage_status[resource_name] = {
                    'reserved': reserved_amount,
                    'actual': actual_amount,
                    'percentage': round(usage_percentage * 100, 1),
                    'active': is_resource_active
                }
                
                # If any resource is not active enough, the overall reservation is not active
                if not is_resource_active:
                    is_active = False
            
            # Create activity record
            activity = ReservationActivity(
                username=username,
                reservation_resources=reservation_resources,
                actual_usage=current_user_usage_by_host,
                is_active=is_active,
                hosts_used=list(current_user_usage_by_host.keys()),
                timestamp=datetime.now()
            )
            
            reservation_activities.append(activity)
            
            # Log activity status with detailed resource information
            if is_active:
                pass
            else:
                #logger.info(f"Reservation inactive for {username}: Insufficient resource usage")
                
                # Send email notification for insufficient resource usage
                context_parts = []
                for resource_name, status in resource_usage_status.items():
                    if not status['active']:
                        context_parts.append(f"{resource_name}: {status['actual']}/{status['reserved']} GPUs ({status['percentage']}%)")
                
                context = f"Resources under 50% usage: {', '.join(context_parts)}"
                send_email(username, "reservation-not-used", context)

        
        # Store activities in database
        store_reservation_activity(reservation_activities, DB_PATH)
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "activities": [
                {
                    "username": a.username,
                    "reservation_resources": a.reservation_resources,
                    "actual_usage": a.actual_usage,
                    "is_active": a.is_active,
                    "hosts_used": a.hosts_used,
                    "timestamp": a.timestamp.isoformat()
                }
                for a in reservation_activities
            ]
        }
        
    except Exception as e:
        error_msg = f"Error checking reservation activity: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}

def store_reservation_activity(activities: List[ReservationActivity], db_path: str) -> None:
    """Store reservation activity records in the database."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ReservationActivity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                reservation_resources TEXT NOT NULL,
                actual_usage TEXT NOT NULL,
                is_active BOOLEAN NOT NULL,
                hosts_used TEXT NOT NULL,
                timestamp DATETIME NOT NULL
            )
        """)
        
        # Insert activity records
        for activity in activities:
            cursor.execute("""
                INSERT INTO ReservationActivity 
                (username, reservation_resources, actual_usage, is_active, hosts_used, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                activity.username,
                json.dumps(activity.reservation_resources),
                json.dumps(activity.actual_usage),
                activity.is_active,
                json.dumps(activity.hosts_used),
                activity.timestamp.isoformat()
            ))
            
        conn.commit()
        
    except Exception as e:
        logger.error(f"Error storing reservation activity: {str(e)}")
        raise
    finally:
        conn.close()

def get_user_gpu_usage_by_host_api(username: str) -> Dict[str, int]:
    """
    Get the total number of GPUs used by a specific user on each host via API call.
    
    Args:
        username: The username to check
        
    Returns:
        Dictionary mapping host names to total GPU count used
    """
    try:
        # Construct API URL using config values
        api_base_url = f"http://{HOST}:{PORT}"
        url = f"{api_base_url}/api/users/{username}/historic-usage"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if username in data and data[username]:
            # Convert the API response format to the expected format
            usage_by_host = {}
            for machine, machine_data in data[username].items():
                usage_by_host[machine] = machine_data['total_gpus']
            return usage_by_host
        else:
            logger.info(f"No historic usage data found for user {username}")
            return {}
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling API for user {username}: {str(e)}")
        return {}
    except Exception as e:
        logger.error(f"Error processing API response for user {username}: {str(e)}")
        return {}
