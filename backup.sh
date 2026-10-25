#!/bin/sh
# One backup: database dump + uploaded files. Keeps the last $BACKUP_KEEP_DAYS days.
set -e
STAMP=$(date +%Y%m%d_%H%M)
DEST=${BACKUP_DIR:-/backups}
mkdir -p "$DEST"
export PGPASSWORD="$POSTGRES_PASSWORD"
pg_dump -h "${POSTGRES_HOST:-db}" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f "$DEST/db_$STAMP.dump"
tar -czf "$DEST/media_$STAMP.tar.gz" -C /data media
find "$DEST" -name 'db_*.dump' -mtime +"${BACKUP_KEEP_DAYS:-30}" -delete
find "$DEST" -name 'media_*.tar.gz' -mtime +"${BACKUP_KEEP_DAYS:-30}" -delete
echo "Backup complete: $STAMP"
