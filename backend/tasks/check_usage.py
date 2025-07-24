from datetime import datetime
import logging
from ..config import DB_PATH
from ..database.queries import get_all_users, get_historic_usage_per_user, get_user_usage
from ..email_notifications import send_email
from ..tasks.calendar_tasks import CALENDAR_LOGS_DIR
import os
import json

logger = logging.getLogger(__name__)

# Thresholds (can be moved to config)
from backend.config import GPU_HOURS_THRESHOLD, IO_OPS_THRESHOLD

def user_has_active_reservation(username, gpu_hours):
    """
    Return True if the user has an active reservation in calendar_today.log and utilization is not above 1.1.
    Utilization = gpu_hours / total_reserved_gpus. If utilization > 1.1, return False.
    """
    log_file = os.path.join(CALENDAR_LOGS_DIR, 'calendar_today.log')
    if not os.path.exists(log_file):
        return False, GPU_HOURS_THRESHOLD
    total_reserved_gpus = 0
    found_reservation = False
    with open(log_file, 'r') as f:
        for line in f:
            try:
                reservation = json.loads(line.strip())
                if reservation.get('username') == username:
                    found_reservation = True
                    # reservation['resources'] is a list of (num, resource) pairs
                    for num, resource in reservation.get('resources', []):
                        try:
                            total_reserved_gpus += int(num)
                        except Exception:
                            continue
            except Exception:
                continue
    found_reservation = max(found_reservation, GPU_HOURS_THRESHOLD)

    if found_reservation and total_reserved_gpus > 0:
        utilization = gpu_hours / total_reserved_gpus

        if utilization > 1.1:
            return False, found_reservation
        return True, found_reservation
    return False, found_reservation

def check_usage_activity():
    """
    Scheduled task: For all users, check if GPU or IO usage exceeds thresholds and send email if so.
    Returns a summary dict.
    """
    try:
        users = get_all_users(DB_PATH)
        usage_by_user = get_historic_usage_per_user(DB_PATH)
        now = datetime.now().isoformat()
        results = []
        for user in users:
            username = user['username']
            has_tikgpu = False
            if username in usage_by_user:
                for machine_name in usage_by_user[username]:
                    if 'tikgpu' in machine_name:
                        has_tikgpu = True
                        break
            if not has_tikgpu:
                continue
            # GPU usage: sum across all machines
            gpu_hours = 0.0
            if username in usage_by_user:
                for machine, stats in usage_by_user[username].items():
                    gpu_hours += stats.get('total_gpu_hours', 0.0)

            # IO usage: use most recent time point
            user_usage = get_user_usage(DB_PATH, username=username)
            if user_usage and 'time_series' in user_usage and user_usage['time_series']:
                io_ops = user_usage['time_series'][-1].get('total_operations', 0)
            else:
                io_ops = 0
            # Email if over threshold and no active reservation
            gpu_alert = False
            io_alert = False
            if gpu_hours > GPU_HOURS_THRESHOLD:
                has_reservation, THRESH = user_has_active_reservation(username, gpu_hours)
                if not has_reservation:
                    context = f"Total GPU hours: {gpu_hours:.2f} (computed threshold according to policy, including active reservations: {THRESH})"
                    send_email(username, "gpu-usage-high", context)
                    gpu_alert = True
            if io_ops > IO_OPS_THRESHOLD:
                context = f"Total IO operations: {io_ops:,} (threshold: {IO_OPS_THRESHOLD:,})"
                send_email(username, "io-usage-high", context)
                io_alert = True
            results.append({
                'username': username,
                'gpu_hours': gpu_hours,
                'io_ops': io_ops,
                'gpu_alert': gpu_alert,
                'io_alert': io_alert,
            })
        logger.info(f"check_usage_activity completed at {now}")
        return {
            'status': 'success',
            'timestamp': now,
            'results': results
        }
    except Exception as e:
        logger.error(f"Error in check_usage_activity: {e}")
        return {'status': 'error', 'error': str(e)} 