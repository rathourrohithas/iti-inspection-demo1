#!/bin/sh
# Runs a backup every day at BACKUP_HOUR (server time, default 02).
while true; do
  if [ "$(date +%H)" = "${BACKUP_HOUR:-02}" ]; then
    /app/deploy/backup.sh || echo "BACKUP FAILED $(date)"
    sleep 3700
  fi
  sleep 600
done
