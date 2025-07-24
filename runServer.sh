#!/bin/bash

# Navigate to the project root directory
cd "$(dirname "$0")"

# Define log file path
LOG_FILE="server.log"

# Activate the virtual environment and start the server in the foreground
# Redirect stdout and stderr to the log file
source venv/bin/activate && python3 src/app.py > "$LOG_FILE" 2>&1

echo "DNS server stopped. Check $LOG_FILE for output."
