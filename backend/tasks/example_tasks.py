from datetime import datetime

def log_current_time():
    """Example task that logs the current time"""
    current_time = datetime.now()
    return {
        "timestamp": current_time.isoformat(),
        "formatted_time": current_time.strftime("%Y-%m-%d %H:%M:%S")
    } 