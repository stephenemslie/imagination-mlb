#!/bin/bash
set -e

if [ "$1" = 'test' ]; then
    exec python3 manage.py test
fi

if [ "$1" = 'runserver' ]; then
    python3 manage.py migrate --noinput
    exec bin/wait-for-it.sh postgres:5432 -- python3 manage.py runserver 0:8000
fi

if [ "$1" = 'gunicorn' ]; then
    python3 manage.py migrate --noinput
    python3 manage.py collectstatic --noinput
    exec bin/wait-for-it.sh postgres:5432 -- gunicorn mlb.wsgi
fi

if [ "$1" = 'shell' ]; then
    exec /bin/bash
fi

if [ "$1" = 'db-backup' ]; then
    echo foo
fi

if [ "$1" = 'ipython' ]; then
    exec python3 manage.py shell
fi

exec "$@"
