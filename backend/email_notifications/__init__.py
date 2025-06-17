"""
Email notification system for cluster usage monitoring.
"""

from .email_notifications import send_email, get_email_notifications, get_email_notifications_count

__all__ = ['send_email', 'get_email_notifications', 'get_email_notifications_count'] 