#!/bin/bash
echo "STARTING DEV SERVER"
./manage.py migrate && echo "Migrations complete!"
./manage.py runserver 0.0.0.0:8000