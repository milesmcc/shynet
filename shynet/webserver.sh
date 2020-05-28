#!/bin/bash
# Start Gunicorn processes
echo Launching Shynet web server...
exec gunicorn shynet.wsgi:application \
    --bind 0.0.0.0:${PORT:-8080} \
    --workers ${NUM_WORKERS:-1} \
    --timeout 100
