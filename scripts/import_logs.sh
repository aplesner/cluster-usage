
#!/bin/bash

# This script processes log files and imports them into the database
# Usage: ./import_logs.sh [path_to_log_file]

# Root directory
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

# Create virtual environment if it doesn't exist
if [ ! -d "$ROOT_DIR/backend/venv" ]; then
    echo "Creating virtual environment..."
    cd "$ROOT_DIR/backend" && python -m venv venv
    source "$ROOT_DIR/backend/venv/bin/activate"
    pip install -r "$ROOT_DIR/backend/requirements.txt"
else
    source "$ROOT_DIR/backend/venv/bin/activate"
fi

# Check if a specific log file was provided
if [ $# -eq 1 ]; then
    LOG_FILE="$1"

    # Check if file exists
    if [ ! -f "$LOG_FILE" ]; then
        echo "Error: Log file not found: $LOG_FILE"
        exit 1
    fi

    echo "Processing log file: $LOG_FILE"
    python "$ROOT_DIR/backend/app.py" process_file --file "$LOG_FILE" --archive

else
    # No file specified, process all logs in the incoming directory
    echo "Processing all logs in incoming directory..."
    python "$ROOT_DIR/backend/app.py" process_logs --archive
fi

deactivate
echo "Import completed."

