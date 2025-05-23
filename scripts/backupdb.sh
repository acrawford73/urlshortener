#!/bin/bash
DB_NAME="psinergydb"
DB_USER="django"
BACKUP_DIR="/home/django/backups"
TIMESTAMP=$(date +"%Y%m%d%H%M")

export PGPASSFILE=/home/django/.pgpass
export PGDATA=/var/lib/postgresql/14/main

# Dump the database with pg_dump and compress the output
pg_dump -U $DB_USER $DB_NAME -F c -b | gzip > "$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz"

# Delete backup files older than 15 days
find $BACKUP_DIR -type f -name "${DB_NAME}_*.sql.gz" -mtime +15 -exec rm {} \;