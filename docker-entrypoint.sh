#!/bin/bash
set -e

if [ "$1" = 'test' ]; then
    bin/wait-for-it.sh postgres:5432
    exec python3 manage.py test
fi

if [ "$1" = 'runserver' ]; then
    bin/wait-for-it.sh postgres:5432 -- python3 manage.py migrate --noinput
    exec python3 manage.py runserver 0:8000
fi

if [ "$1" = 'gunicorn' ]; then
    bin/wait-for-it.sh postgres:5432 -- python3 manage.py migrate --noinput
    python3 manage.py collectstatic --noinput
    exec gunicorn mlb.wsgi
fi

if [ "$1" = 'celery' ]; then
    exec bin/wait-for-it.sh postgres:5432 -- celery -A mlb worker -l info -B
fi

if [ "$1" = 'shell' ]; then
    exec /bin/bash
fi

if [ "$1" = 'ipython' ]; then
    exec python3 manage.py shell
fi

exec "$@"
