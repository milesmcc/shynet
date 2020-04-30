#!/bin/bash
# Check if Setup is necessary, do setup as needed
sanity_results=( $(python manage.py sanity_checks) )
if [[ ${sanity_results[0]} == True ]]; then
  echo "Running Migrations..."
  {
    python manage.py migrate && echo "Migrations Done"
  } || {
    echo "Failed Migrations, exiting" && exit 1
  }
  else
  echo "Migrations Unecessary, skipping"
fi
if [[ ${sanity_results[1]} == True ]]; then
  echo "Running CreateAdmin..."
  {
    temppwd=$( python manage.py registeradmin $SHYNET_EMAIL ) && echo "Admin Created, password $temppwd"
  } || {
    echo "Failed CreateAdmin, exiting" & exit 1
  }
  else
  echo "CreateAdmin Unecessary, skipping"
fi
if [[ ${sanity_results[2]} == True ]]; then
  echo "Setting Hostname..."
  {
    python manage.py hostname $SHYNET_HOST && echo "Host Set"
  } || {
    echo "Failed setting Hostname, exiting" & exit 1
  }
  else
  echo "Hostname Unecessary, skipping"
fi
if [[ ${sanity_results[3]} == True ]]; then
  echo "Setting Hostname..."
  {
    python manage.py whitelabel $SHYNET_NAME && echo "WhiteLabel Set"
  } || {
    echo "Failed Migrations, exiting" & exit 1
  }
  else
  echo "WhiteLabel Unecessary, skipping"
fi
./webserver.sh
