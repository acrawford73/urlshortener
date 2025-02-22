#!/bin/bash

# Set backup directory
BACKUP_DIR="/home/django/backups"

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d%H%M")

# Run Django dumpdata
python /path/to/your/project/manage.py dumpdata > "$BACKUP_DIR/$TIMESTAMP.json"

# Remove JSON files older than 30 days
find "$BACKUP_DIR" -type f -name "*.json" -mtime +30 -exec rm {} \;

# Optional: Log cleanup actions
echo "$(date +"%Y-%m-%d %H:%M:%S") - Backup created: $TIMESTAMP.json" >> "$BACKUP_DIR/backup.log"
echo "$(date +"%Y-%m-%d %H:%M:%S") - Old backups deleted" >> "$BACKUP_DIR/backup.log"
