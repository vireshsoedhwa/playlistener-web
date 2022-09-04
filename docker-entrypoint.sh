#!/bin/sh

set -e

if [ -z "${DJANGO_SECRET_KEY}" ];then
  echo DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY >> .env
fi

if [ -z "${GO_PIPELINE_LABEL}" ];then
  echo GO_PIPELINE_LABEL=$GO_PIPELINE_LABEL >> .env
fi

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

>&2 echo "Starting supervisor..."
exec "$@"
