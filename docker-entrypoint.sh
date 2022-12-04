#!/bin/sh

set -e

>&2 echo "Make Database migrations"
python manage.py makemigrations youtube
echo "-------------------------------------------------------------------------------------------\n"

>&2 echo "Run Database migrations"
python manage.py migrate
echo "-------------------------------------------------------------------------------------------\n"

# Collect static files
>&2 echo "Collect static"
python manage.py collectstatic --noinput

>&2 echo "Start Django Q task Scheduler"
python manage.py qcluster &
echo "-------------------------------------------------------------------------------------------\n"

>&2 echo "Starting Nginx..."
nginx

>&2 echo "Starting Daphne..."
exec "$@"
