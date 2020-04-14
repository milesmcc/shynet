#!/bin/bash

# Start Gunicorn processes
echo Launching Shynet web server...
exec gunicorn shynet.wsgi:application \
    --bind 0.0.0.0:8080 \
    --workers 3 \
    --timeout 100