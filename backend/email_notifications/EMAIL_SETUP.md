# Email Setup Guide

This guide explains how to configure the email notification system to send emails via Google's SMTP server.

## Prerequisites

1. A Google account (Gmail)
2. 2-Factor Authentication enabled on your Google account
3. An App Password generated for this application

## Step 1: Enable 2-Factor Authentication

1. Go to your Google Account settings: https://myaccount.google.com/
2. Navigate to "Security"
3. Enable "2-Step Verification" if not already enabled

## Step 2: Generate an App Password

1. Go to your Google Account settings: https://myaccount.google.com/
2. Navigate to "Security"
3. Under "2-Step Verification", click on "App passwords"
4. Select "Mail" as the app and "Other" as the device
5. Enter a name for this app (e.g., "Cluster Usage Monitor")
6. Click "Generate"
7. **Copy the 16-character password** (you'll need this for the configuration)

## Step 3: Configure Email Settings

Edit the file `backend/email_notifications/email_config.py` and update the following values:

```python
# Replace with your actual Gmail address
EMAIL_SENDER = "your-email@gmail.com"

# Replace with the 16-character app password from Step 2
EMAIL_PASSWORD = "your-16-char-app-password"

# Replace with your organization's email domain
EMAIL_DOMAIN = "your-domain.com"  # e.g., "company.com", "university.edu"

# Replace with your admin contact email
ADMIN_EMAIL = "admin@your-domain.com"

# Replace with your cluster name
CLUSTER_NAME = "Your Cluster Name"
```

## Step 4: Test the Email Configuration

You can test the email configuration by running a simple test script:

```python
from backend.email_notifications import send_email

# Test email (replace 'testuser' with a valid username)
success = send_email(
    user="testuser",
    email_type="reservation-not-used",
    context="Test: tikgpu10: 1/4 GPUs (25%)"
)

if success:
    print("Email sent successfully!")
else:
    print("Failed to send email. Check the logs for details.")
```

## Security Notes

1. **Never commit your actual email credentials to version control**
2. **Use environment variables for production deployments**
3. **The app password is specific to this application - don't share it**
4. **Regular passwords won't work - you must use an app password**

## Environment Variables (Recommended for Production)

For production deployments, it's recommended to use environment variables instead of hardcoding credentials:

```python
import os

EMAIL_SENDER = os.getenv('EMAIL_SENDER', 'your-email@gmail.com')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'your-app-password')
EMAIL_DOMAIN = os.getenv('EMAIL_DOMAIN', 'your-domain.com')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@your-domain.com')
CLUSTER_NAME = os.getenv('CLUSTER_NAME', 'Your Cluster Name')
```

Then set the environment variables:
```bash
export EMAIL_SENDER="your-email@gmail.com"
export EMAIL_PASSWORD="your-16-char-app-password"
export EMAIL_DOMAIN="your-domain.com"
export ADMIN_EMAIL="admin@your-domain.com"
export CLUSTER_NAME="Your Cluster Name"
```

## Troubleshooting

### Common Issues:

1. **SMTP Authentication Error**: 
   - Make sure you're using an app password, not your regular Gmail password
   - Ensure 2-factor authentication is enabled

2. **Recipient Refused**:
   - Check that the email domain is correct
   - Verify the recipient email address format

3. **Rate Limiting**:
   - The system limits emails to 5 per hour per user
   - Check the logs for rate limit warnings

### Logs:
Check the application logs for detailed error messages when emails fail to send.

## Email Templates

The system includes three email templates:

1. **reservation-not-used**: Sent when resources are underutilized (< 50%)
2. **reservation-expired**: Sent when a reservation expires
3. **default**: Generic notification template

All templates are HTML-formatted and include:
- Professional styling
- Clear action items
- Contact information
- Cluster branding 