import logging
import smtplib
import ssl
import time
from datetime import datetime, timedelta
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..database.schema import get_db_connection
from ..config import DB_PATH, PORT
from .email_config import (
    SMTP_SERVER, SMTP_PORT, EMAIL_SENDER, EMAIL_PASSWORD, 
    EMAIL_DOMAIN, ADMIN_EMAIL, CLUSTER_NAME, MAX_RETRIES, 
    RETRY_DELAY, MAX_EMAILS_PER_HOUR, ENABLE_EMAILS
)
from ..database.thesis_queries import get_user_thesis_details

logger = logging.getLogger(__name__)

# Rate limiting storage (in-memory for simplicity)
email_rate_limit = {}
IS_DEBUGGING = not (PORT == 5000)

def send_email(user: str, email_type: str = "reservation-not-used", context: str = "") -> bool:
    """
    Send email notification to user with rate limiting.
    If the user has thesis info, CC all their supervisors.
    If user contains '@', treat as full email address.
    """
    if not ENABLE_EMAILS:
        logger.info("Emails disabled")
        return False
    try:
        # Check rate limiting (only for usernames, not raw emails)
        if '@' not in user and not check_rate_limit(user):
            logger.warning(f"Rate limit exceeded for user {user}")
            return False
        
        # Find supervisors for CC
        cc_emails = []
        try:
            # Only look up supervisors if user is a username
            lookup_user = user.split('@')[0] if '@' in user else user
            thesis_info = get_user_thesis_details(lookup_user)
            if thesis_info and len(thesis_info) > 0:
                # Get supervisors from the most recent thesis only
                most_recent_thesis = thesis_info[0]
                
                # Only get supervisors if the user is a student in this thesis
                if most_recent_thesis['role'] == 'student':
                    supervisors = set(most_recent_thesis['supervisors'])
                    # Remove the user from CC if present
                    supervisors.discard(lookup_user)
                    cc_emails = [f"{sup}@{EMAIL_DOMAIN}" for sup in supervisors if sup]
                    
                    # Log which thesis is being used for supervisor lookup
                    logger.info(f"Using most recent thesis for {lookup_user}: '{most_recent_thesis['thesis_title']}' (semester: {most_recent_thesis['semester']}, role: {most_recent_thesis['role']})")
                else:
                    logger.info(f"User {lookup_user} is a supervisor in their most recent thesis, no supervisors to CC")
        except Exception as e:
            logger.error(f"Error fetching supervisors for CC: {e}")
            cc_emails = []
        
        # For now, just log to console
        logger.info(f"EMAIL NOTIFICATION - To: {user}, Type: {email_type}, Context: {context}, CC: {cc_emails}")
        
        # Store email notification in task logs (only for usernames)
        if '@' not in user:
            store_email_notification(user, email_type, context, cc_emails)
        
        # Send actual email with retries
        for attempt in range(MAX_RETRIES):
            if send_smtp_email(user, email_type, context, cc_emails=cc_emails):
                logger.info(f"Email sent successfully to {user}")
                if '@' not in user:
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

def send_smtp_email(recipient: str, email_type: str, context: str, cc_emails=None) -> bool:
    """
    Send email via SMTP using Google's SMTP server.
    Optionally CC additional recipients.
    If recipient contains '@', treat as full email address.
    """
    if cc_emails is None:
        cc_emails = []

    # Allow startup notifications to bypass debugging restriction
    if IS_DEBUGGING and email_type != "startup-notification":
        logger.info(f"DEBUGGING - Email not sent to {recipient} bc of DEBUGGING (CC: {cc_emails})")
        return True
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        if '@' in recipient:
            msg['To'] = recipient
        else:
            msg['To'] = f"{recipient}@{EMAIL_DOMAIN}"
        if cc_emails:
            msg['Cc'] = ', '.join(cc_emails)
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
            to_addrs = [msg['To']] + cc_emails
            text = msg.as_string()
            server.sendmail(EMAIL_SENDER, to_addrs, text)
            
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
        "gpu-usage-high": "Cluster Usage Alert - High GPU Usage",
        "io-usage-high": "Cluster Usage Alert - High IO Usage",
        "startup-notification": f"{CLUSTER_NAME} - Watchdog is Live",
        "default": "Cluster Usage Notification"
    }
    return subjects.get(email_type, subjects["default"])

def create_email_body(recipient: str, email_type: str, context: str) -> str:
    """Create HTML email body based on email type and context."""
    supervisor_note = '''<div style="margin-top:18px; padding:12px; background:#e3f2fd; border-radius:6px;">
        <b>Supervisor Action:</b> If you are a supervisor and your student's email is not username@ethz.ch, please update it here:<br />
        <a href="https://tik-db.ee.ethz.ch/db/restricted/tik/?db=students&form=form_search_students_to_edit" target="_blank">https://tik-db.ee.ethz.ch/db/restricted/tik/?db=students&form=form_search_students_to_edit</a>
    </div>'''
    
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
    
    elif email_type == "gpu-usage-high":
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .alert {{ background-color: #d1ecf1; border: 1px solid #bee5eb; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{CLUSTER_NAME} - High GPU Usage Alert</h2>
                    <p>Hello {recipient},</p>
                </div>
                <div class="alert">
                    <h3>🚨 High GPU Usage Detected</h3>
                    <p>Your total GPU usage has exceeded the configured threshold.</p>
                </div>
                <div class="details">
                    <h4>Usage Details:</h4>
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
    elif email_type == "io-usage-high":
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .alert {{ background-color: #fceabb; border: 1px solid #f8d347; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{CLUSTER_NAME} - High IO Usage Alert</h2>
                    <p>Hello {recipient},</p>
                </div>
                <div class="alert">
                    <h3>🚨 High IO Usage Detected</h3>
                    <p>Your total IO operations have exceeded the configured threshold.</p>
                </div>
                <div class="details">
                    <h4>Usage Details:</h4>
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
    elif email_type == "student-non-ethz-email":
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
                    <h2>{CLUSTER_NAME} - Student Email Alert</h2>
                    <p>Hello {recipient},</p>
                </div>
                <div class="alert">
                    <h3>⚠️ Non-ETHZ Email Detected</h3>
                    <p>This student does not have an @ethz.ch email address registered.</p>
                </div>
                <div class="details">
                    <h4>Details:</h4>
                    <p>{context}</p>
                </div>
                {supervisor_note}
                <div class="footer">
                    <p>This is an automated notification from the {CLUSTER_NAME} monitoring system.</p>
                    <p>If you have any questions, please contact: <a href="mailto:{ADMIN_EMAIL}">{ADMIN_EMAIL}</a></p>
                </div>
            </div>
        </body>
        </html>
        """
    elif email_type == "startup-notification":
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .alert {{ background-color: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{CLUSTER_NAME} - Watchdog Status</h2>
                    <p>Hello {recipient},</p>
                </div>
                
                <div class="alert">
                    <h3>🟢 Cluster Watchdog is Live</h3>
                    <p>The {CLUSTER_NAME} monitoring system has successfully started and is now actively monitoring cluster usage and reservations.</p>
                </div>
                
                <div class="footer">
                    <p><strong>Monitoring Features Active:</strong></p>
                    <ul>
                        <li>Reservation usage tracking</li>
                        <li>GPU and IO usage monitoring</li>
                        <li>Automated email notifications</li>
                        <li>Periodic health checks</li>
                    </ul>
                    
                    <p>This is an automated notification from the {CLUSTER_NAME} monitoring system.</p>
                    <p>If you have any questions, please contact: <a href="mailto:{ADMIN_EMAIL}">{ADMIN_EMAIL}</a></p>
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

def store_email_notification(user: str, email_type: str, context: str, cc_emails=None) -> None:
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
        # Add CC info to details
        cc_line = f"CC: {', '.join(cc_emails)}\n" if cc_emails else ""
        details = f"{cc_line}{context}"
        
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