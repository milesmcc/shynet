#!/bin/bash
# Check if setup is necessary, do setup as needed
echo "Performing startup checks..."
sanity_results=( $(./manage.py startup_checks) )
if [[ ${sanity_results[0]} == True ]]; then
  echo "Running migrations (setting up DB)..."
  {
    ./manage.py migrate && echo "Migrations complete!"
  } || {
    echo "Migrations failed, exiting" && exit 1
  }
  else
  echo "Database is ready to go."
fi
if [[ -n $SHYNET_ADMIN_EMAIL && ${sanity_results[1]} == True ]]; then
  echo "Creating an admin user..."
  {
    temppwd=$( ./manage.py registeradmin $SHYNET_ADMIN_EMAIL ) && echo "Admin user ($SHYNET_ADMIN_EMAIL) created! Password: $temppwd"
  } || {
    echo "Failed to create admin, exiting" & exit 1
  }
  else
  echo "Making no changes to admin user."
fi
if [[ -n $SHYNET_HOST && ${sanity_results[2]} == True ]]; then
  echo "Setting hostname..."
  {
    ./manage.py hostname $SHYNET_HOST && echo "Hostname set to $SHYNET_HOST!"
  } || {
    echo "Failed setting hostname, exiting" & exit 1
  }
  else
  echo "Making no changes to hostname."
fi
if [[ -n $SHYNET_WHITELABEL && ${sanity_results[3]} == True ]]; then
  echo "Setting whitelabel..."
  {
    ./manage.py whitelabel "$SHYNET_WHITELABEL" && echo "Whitelabel set! Whitelabel: $SHYNET_WHITELABEL"
  } || {
    echo "Failed to set whitelabel, exiting" & exit 1
  }
  else
  echo "Making no changes to whitelabel."
fi
echo "Startup checks complete!"
