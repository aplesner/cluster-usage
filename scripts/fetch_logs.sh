#!/bin/bash

# Check variables
if [ -z "$SERVER" ] || [ -z "$USER" ] || [ -z "$REMOTE_LOG_DIR" ] || [ -z "$LOG_FILE" ] || [ -z "$LOCAL_LOG_DIR" ] || [ -z "$LOG_FILE_NAME" ]; then
    source scripts/variables.sh
fi

# Fetch logs from the server
rsync "$USER@$SERVER:$REMOTE_LOG_DIR/$LOG_FILE" "$LOCAL_LOG_DIR/$LOG_FILE_NAME"
