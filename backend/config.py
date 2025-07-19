import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database and log directories
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_DIR = os.path.join(DATA_DIR, 'db')
LOG_DIR = os.path.join(DATA_DIR, 'logs')
INCOMING_LOGS_DIR = os.path.join(LOG_DIR, 'incoming')
ARCHIVE_LOGS_DIR = os.path.join(LOG_DIR, 'archive')
DB_PATH = os.path.join(DB_DIR, 'io_usage.db')

# Ensure directories exist
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(INCOMING_LOGS_DIR, exist_ok=True)
os.makedirs(ARCHIVE_LOGS_DIR, exist_ok=True)

# API settings
API_PREFIX = '/api'

# App settings
DEBUG = False
HOST = '0.0.0.0'
PORT = 5001

GPU_HOURS_THRESHOLD = 4
IO_OPS_THRESHOLD = 250*1000
GPU_MAX_HOURS = 4.0

# Feature flags
NOTIFY_SUPERVISORS_ON_NON_ETHZ_STUDENT_EMAILS = False