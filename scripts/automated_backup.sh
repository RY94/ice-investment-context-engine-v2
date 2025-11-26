#!/bin/bash
# Location: /scripts/automated_backup.sh
# Purpose: Automated daily backup script for ICE storage (called by cron)
# Why: Ensures regular backups without manual intervention
# Relevant Files: backup_ice_storage.py

# Set up environment
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Log file for cron job output
LOG_DIR="$PROJECT_ROOT/logs/backups"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/backup_$(date +%Y%m%d).log"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Start backup process
log_message "========================================="
log_message "Starting automated daily backup"
log_message "Project root: $PROJECT_ROOT"

# Change to project directory
cd "$PROJECT_ROOT" || {
    log_message "ERROR: Failed to change to project directory"
    exit 1
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    log_message "ERROR: Python3 not found in PATH"
    exit 1
fi

# Run the backup script with a descriptive message
log_message "Executing backup script..."
python3 "$PROJECT_ROOT/scripts/backup_ice_storage.py" backup \
    --description "Automated daily backup via cron" \
    >> "$LOG_FILE" 2>&1

# Check exit status
if [ $? -eq 0 ]; then
    log_message "✅ Backup completed successfully"

    # Run cleanup to remove old backups (older than 30 days)
    log_message "Running cleanup for old backups..."
    python3 "$PROJECT_ROOT/scripts/backup_ice_storage.py" cleanup >> "$LOG_FILE" 2>&1

    if [ $? -eq 0 ]; then
        log_message "✅ Cleanup completed successfully"
    else
        log_message "⚠️ Cleanup failed (non-critical)"
    fi
else
    log_message "❌ Backup failed with exit code $?"
    exit 1
fi

# Optional: Send notification (uncomment and configure as needed)
# Example for macOS notification:
# osascript -e 'display notification "ICE daily backup completed" with title "ICE Backup"'

# Example for email notification (requires mail command configured):
# echo "ICE backup completed at $(date)" | mail -s "ICE Backup Success" your-email@example.com

log_message "Automated backup process finished"
log_message "========================================="

exit 0