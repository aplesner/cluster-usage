"""
Email configuration for SMTP settings.
Update these values with your actual Google account credentials.
"""

# Google SMTP Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Email account credentials
# Replace these with your actual Google account details
EMAIL_SENDER = "cluster.disco@gmail.com"  # Your Gmail address
EMAIL_PASSWORD = "uylq ashw tany qzih"   # Your Gmail app password

# Email domain for recipients
# Replace with your organization's email domain
EMAIL_DOMAIN = "ethz.ch"  # e.g., "company.com", "university.edu"

# Email templates configuration
ADMIN_EMAIL = "taczel@ethz.ch"  # Admin contact email
CLUSTER_NAME = "The mighty TIK cluster"     # Name of your cluster

# Email sending configuration
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Rate limiting (emails per hour per user)
MAX_EMAILS_PER_HOUR = 5 

ENABLE_EMAILS = True