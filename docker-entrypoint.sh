#!/bin/sh

set -e

echo DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY >> .env

>&2 echo "Run Database migrations"
python manage.py migrate
echo "-------------------------------------------------------------------------------------------\n"

# Collect static files
>&2 echo "Collect static"
python manage.py collectstatic --noinput

# >&2 echo "Create temporary superuser"
# echo "from django.contrib.auth.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com','admin')" | python manage.py shell

# echo "-------------------------------------------------------------------------------------------\n"

>&2 echo "Starting supervisor..."
exec "$@"
