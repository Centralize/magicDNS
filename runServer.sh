#!/bin/bash

# Navigate to the project root directory
cd "$(dirname "$0")"

# Define log file path
LOG_FILE="server.log"

# Function to display usage
usage() {
    echo "Usage: $0 [start|convert-zone <zone_file_path> <output_json_path>|export-zone <json_file_path> <output_zone_path>]"
    echo "  start: Starts the DNS server."
    echo "  convert-zone: Converts a standard zone file to magicDNS JSON format."
    echo "  export-zone: Converts a magicDNS JSON zone file to standard zone file format."
    exit 1
}

# Check for arguments
if [ "$#" -eq 0 ]; then
    usage
fi

# Activate the virtual environment
source venv/bin/activate

# Process commands
case "$1" in
    start)
        echo "Starting DNS server..."
        # Start the server in the foreground and redirect stdout/stderr to log file
        python3 src/app.py > "$LOG_FILE" 2>&1
        echo "DNS server stopped. Check $LOG_FILE for output."
        ;;
    convert-zone)
        if [ "$#" -ne 3 ]; then
            echo "Error: Missing arguments for convert-zone."
            usage
        fi
        ZONE_FILE="$2"
        OUTPUT_JSON="$3"
        echo "Converting zone file '$ZONE_FILE' to JSON '$OUTPUT_JSON'..."
        python3 src/zone_converter.py "$ZONE_FILE" "$OUTPUT_JSON"
        ;;
    export-zone)
        if [ "$#" -ne 3 ]; then
            echo "Error: Missing arguments for export-zone."
            usage
        fi
        JSON_FILE="$2"
        OUTPUT_ZONE="$3"
        echo "Exporting JSON zone file '$JSON_FILE' to standard zone file '$OUTPUT_ZONE'..."
        python3 src/zone_exporter.py "$JSON_FILE" "$OUTPUT_ZONE"
        ;;
    *)
        echo "Error: Unknown command '$1'."
        usage
        ;;
esac

deactivate # Deactivate virtual environment
