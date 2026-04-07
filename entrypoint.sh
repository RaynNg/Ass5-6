#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate --run-syncdb

echo "Starting server..."
exec python manage.py runserver 0.0.0.0:8000
