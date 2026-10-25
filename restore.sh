#!/bin/sh
# Restore: deploy/restore.sh backups/db_YYYYMMDD_HHMM.dump backups/media_YYYYMMDD_HHMM.tar.gz
# Run on the host from the project folder. Stops the web service while restoring.
set -e
[ -f "$1" ] || { echo "Usage: $0 <db_dump> [media_tar]"; exit 1; }
. ./.env
docker compose stop web
docker compose exec -T db pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists < "$1"
if [ -n "$2" ]; then
  docker compose run --rm -v "$(pwd)/$(dirname "$2")":/restore --entrypoint sh web -c "rm -rf /data/media/* && tar -xzf /restore/$(basename "$2") -C /data"
fi
docker compose start web
echo "Restore complete."
