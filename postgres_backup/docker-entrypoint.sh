#!/bin/sh
set -e
export POSTGRES_PASSWORD=`cat /run/secrets/POSTGRES_PASSWORD`
export S3_SECRET_ACCESS_KEY=`cat /run/secrets/S3_SECRET_ACCESS_KEY`
export S3_ACCESS_KEY_ID=`cat /run/secrets/S3_ACCESS_KEY_ID`

if [ "$1" = 'run' ]; then
    sh run.sh
fi

exec "$@"
