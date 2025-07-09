import logging
import smtplib
import ssl
import time
from datetime import datetime, timedelta
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..database.schema import get_db_connection
from ..config import DB_PATH
from .email_config import (
    SMTP_SERVER, SMTP_PORT, EMAIL_SENDER, EMAIL_PASSWORD, 
    EMAIL_DOMAIN, ADMIN_EMAIL, CLUSTER_NAME, MAX_RETRIES, 
    RETRY_DELAY, MAX_EMAILS_PER_HOUR
)

logger = logging.getLogger(__name__)

# Rate limiting storage (in-memory for simplicity)
email_rate_limit = {}

def send_email(user: str, email_type: str = "reservation-not-used", context: str = "") -> bool:
    """
    Send email notification to user with rate limiting.
    
    Args:
        user: Username to send email to
        email_type: Type of email notification
        context: Additional context information
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Check rate limiting
        if not check_rate_limit(user):
            logger.warning(f"Rate limit exceeded for user {user}")
            return False
        
        # For now, just log to console
        logger.info(f"EMAIL NOTIFICATION - To: {user}, Type: {email_type}, Context: {context}")
        
        # Store email notification in task logs
        store_email_notification(user, email_type, context)
        
        # Send actual email with retries
        for attempt in range(MAX_RETRIES):
            if send_smtp_email(user, email_type, context):
                logger.info(f"Email sent successfully to {user}")
                update_rate_limit(user)
                return True
            else:
                logger.warning(f"Email attempt {attempt + 1} failed for {user}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
        
        logger.error(f"All email attempts failed for {user}")
        return False
        
    except Exception as e:
        logger.error(f"Error sending email to {user}: {str(e)}")
        return False

def check_rate_limit(user: str) -> bool:
    """Check if user has exceeded email rate limit."""
    now = datetime.now()
    if user in email_rate_limit:
        user_emails = email_rate_limit[user]
        # Remove emails older than 1 hour
        user_emails = [email_time for email_time in user_emails 
                      if now - email_time < timedelta(hours=1)]
        email_rate_limit[user] = user_emails
        
        if len(user_emails) >= MAX_EMAILS_PER_HOUR:
            return False
    
    return True

def update_rate_limit(user: str) -> None:
    """Update rate limit for user after successful email send."""
    now = datetime.now()
    if user not in email_rate_limit:
        email_rate_limit[user] = []
    email_rate_limit[user].append(now)

def send_smtp_email(recipient: str, email_type: str, context: str) -> bool:
    """
    Send email via SMTP using Google's SMTP server.
    
    Args:
        recipient: Email recipient (username@domain.com)
        email_type: Type of email notification
        context: Additional context information
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = f"{recipient}@{EMAIL_DOMAIN}"
        msg['Subject'] = get_email_subject(email_type)
        
        # Create email body
        body = create_email_body(recipient, email_type, context)
        msg.attach(MIMEText(body, 'html'))
        
        # Create SMTP session
        context_ssl = ssl.create_default_context()
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context_ssl)
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            
            # Send email
            text = msg.as_string()
            server.sendmail(EMAIL_SENDER, msg['To'], text)
            
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication failed: {e}")
        return False
    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"Recipient refused: {e}")
        return False
    except smtplib.SMTPServerDisconnected as e:
        logger.error(f"SMTP server disconnected: {e}")
        return False
    except Exception as e:
        logger.error(f"SMTP error: {e}")
        return False

def get_email_subject(email_type: str) -> str:
    """Get email subject based on email type."""
    subjects = {
        "reservation-not-used": "Cluster Reservation Alert - Underutilized Resources",
        "reservation-expired": "Cluster Reservation Alert - Reservation Expired",
        "reservation-reminder": "Cluster Reservation Reminder",
        "default": "Cluster Usage Notification"
    }
    return subjects.get(email_type, subjects["default"])

def create_email_body(recipient: str, email_type: str, context: str) -> str:
    """Create HTML email body based on email type and context."""
    
    if email_type == "reservation-not-used":
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .alert {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .details {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{CLUSTER_NAME} - Reservation Alert</h2>
                    <p>Hello {recipient},</p>
                </div>
                
                <div class="alert">
                    <h3>⚠️ Underutilized Resources Detected</h3>
                    <p>Your cluster reservation is currently underutilized. According to our monitoring system, 
                    you are not using at least 50% of your reserved resources.</p>
                </div>
                
                <div class="details">
                    <h4>Resource Usage Details:</h4>
                    <p>{context}</p>
                </div>
                
                <div class="footer">
                    <p><strong>Action Required:</strong></p>
                    <ul>
                        <li>Please start using your reserved resources or</li>
                        <li>Consider releasing the reservation if not needed</li>
                        <li>Contact the cluster administrator if you need assistance</li>
                    </ul>
                    
                    <p>This is an automated notification from the {CLUSTER_NAME} monitoring system.</p>
                    <p>If you have any questions, please contact: <a href="mailto:{ADMIN_EMAIL}">{ADMIN_EMAIL}</a></p>
                </div>
            </div>
        </body>
        </html>
        """
    
    elif email_type == "reservation-expired":
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .alert {{ background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{CLUSTER_NAME} - Reservation Expired</h2>
                    <p>Hello {recipient},</p>
                </div>
                
                <div class="alert">
                    <h3>⏰ Reservation Expired</h3>
                    <p>Your cluster reservation has expired. The reserved resources are now available for other users.</p>
                </div>
                
                <div class="footer">
                    <p>If you need to reserve resources again, please contact: <a href="mailto:{ADMIN_EMAIL}">{ADMIN_EMAIL}</a></p>
                    <p>This is an automated notification from the {CLUSTER_NAME} monitoring system.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    else:
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .content {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{CLUSTER_NAME} - Usage Notification</h2>
                    <p>Hello {recipient},</p>
                </div>
                
                <div class="content">
                    <p>{context}</p>
                </div>
                
                <div class="footer">
                    <p>This is an automated notification from the {CLUSTER_NAME} monitoring system.</p>
                    <p>If you have any questions, please contact: <a href="mailto:{ADMIN_EMAIL}">{ADMIN_EMAIL}</a></p>
                </div>
            </div>
        </body>
        </html>
        """

def store_email_notification(user: str, email_type: str, context: str) -> None:
    """Store email notification in the task logs table."""
    conn = get_db_connection(DB_PATH)
    try:
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS PeriodicTaskLogs (
                log_id INTEGER PRIMARY KEY,
                timestamp DATETIME NOT NULL,
                task_name TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                details TEXT
            )
        """)
        
        # Insert email notification as a task log entry
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        task_name = f"email-{email_type}"
        status = "sent"
        message = f"Email notification sent to {user}"
        details = context
        
        cursor.execute("""
            INSERT INTO PeriodicTaskLogs 
            (timestamp, task_name, status, message, details)
            VALUES (?, ?, ?, ?, ?)
        """, (timestamp, task_name, status, message, details))
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"Error storing email notification: {str(e)}")
        raise
    finally:
        conn.close()

def get_email_notifications(limit: int = 20, offset: int = 0) -> list:
    """Get recent email notifications from task logs with pagination."""
    conn = get_db_connection(DB_PATH)
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, task_name, status, message, details
            FROM PeriodicTaskLogs 
            WHERE task_name LIKE 'email-%'
            ORDER BY timestamp DESC 
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        notifications = []
        for row in cursor.fetchall():
            notifications.append({
                'timestamp': row[0],
                'email_type': row[1].replace('email-', ''),
                'status': row[2],
                'message': row[3],
                'details': row[4]
            })
        
        return notifications
        
    except Exception as e:
        logger.error(f"Error getting email notifications: {str(e)}")
        return []
    finally:
        conn.close()

def get_email_notifications_count() -> int:
    """Get total count of email notifications."""
    conn = get_db_connection(DB_PATH)
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM PeriodicTaskLogs 
            WHERE task_name LIKE 'email-%'
        """)
        
        result = cursor.fetchone()
        return result[0] if result else 0
        
    except Exception as e:
        logger.error(f"Error getting email notifications count: {str(e)}")
        return 0
    finally:
        conn.close() 

def get_email_counts_by_user(start_time: str, end_time: str) -> dict:
    """
    Get the number of sent emails to each user in a given time range.
    Args:
        start_time: Start of the time range (inclusive), as ISO string or 'YYYY-MM-DD HH:MM:SS'.
        end_time: End of the time range (inclusive), as ISO string or 'YYYY-MM-DD HH:MM:SS'.
    Returns:
        Dict mapping username to count of sent emails.
    """
    import re
    conn = get_db_connection(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT message FROM PeriodicTaskLogs 
            WHERE task_name LIKE 'email-%' 
              AND timestamp >= ? AND timestamp <= ?
            """,
            (start_time, end_time)
        )
        user_counts = {}
        pattern = re.compile(r"Email notification sent to ([^\s]+)")
        for row in cursor.fetchall():
            message = row[0]
            match = pattern.search(message or "")
            if match:
                username = match.group(1)
                user_counts[username] = user_counts.get(username, 0) + 1
        return user_counts
    except Exception as e:
        logger.error(f"Error getting email counts by user: {str(e)}")
        return {}
    finally:
        conn.close() 