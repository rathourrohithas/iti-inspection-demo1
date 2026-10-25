#!/bin/sh
# Start command for the Render practice site.
set -e
python manage.py migrate --noinput
python manage.py createcachetable
if [ "$DEMO_MODE" = "1" ]; then
  python manage.py seed_demo --if-empty
fi
exec gunicorn portal.wsgi:application --bind "0.0.0.0:${PORT:-10000}" --workers 2 --timeout 120 --access-logfile -
