#!/usr/bin/bash

echo "Running Migrations"
alembic upgrade head

echo "Starting Backend"
exec gunicorn 'gamecafe:create_app()' \
    --bind '0.0.0.0:80'
    --workers 4
