#!/bin/bash
# Check if setup is necessary, do setup as needed
echo "Performing startup checks..."
startup_results=( $(./manage.py startup_checks) )
if [[ ${startup_results[0]} == True ]]; then
  echo "Running migrations (setting up DB)..."
  {
    ./manage.py migrate && echo "Migrations complete!"
  } || {
    echo "Migrations failed, exiting" && exit 1
  }
  else
  echo "Database is ready to go."
fi
if [[ ${startup_results[1]} == True ]]; then
  echo "Warning: no admin user available. Consult docs for instructions."
fi
if [[ ${startup_results[2]} == True ]]; then
  echo "Warning: Shynet's whitelabel is not set. Consult docs for instructions."
fi
echo "Startup checks complete!"
