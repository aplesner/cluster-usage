"""
Timezone utilities for consistent CET/CEST handling across the application.
"""
import pytz
from datetime import datetime, timedelta

# Central timezone configuration
CET_TIMEZONE = pytz.timezone('Europe/Berlin')

def get_current_time_cet() -> datetime:
    """Get current time in CET/CEST timezone."""
    return datetime.now(CET_TIMEZONE)

def localize_naive_datetime(dt: datetime) -> datetime:
    """Convert a naive datetime to CET/CEST timezone."""
    if dt.tzinfo is None:
        return CET_TIMEZONE.localize(dt)
    return dt

def parse_datetime_cet(dt_str: str) -> datetime:
    """Parse a datetime string and ensure it's in CET/CEST timezone."""
    dt = datetime.fromisoformat(dt_str)
    return localize_naive_datetime(dt)

def format_datetime_cet(dt: datetime, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """Format a datetime in CET/CEST timezone."""
    if dt.tzinfo is None:
        dt = localize_naive_datetime(dt)
    return dt.strftime(format_str)

def get_datetime_cet_isoformat(dt: datetime = None) -> str:
    """Get datetime in CET/CEST timezone as ISO format string."""
    if dt is None:
        dt = get_current_time_cet()
    elif dt.tzinfo is None:
        dt = localize_naive_datetime(dt)
    return dt.isoformat() 