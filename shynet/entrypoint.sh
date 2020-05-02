#!/bin/bash

if [[ $PERFORM_CHECKS_AND_SETUP == True ]]; then
  ./startup_checks.sh
fi

./webserver.sh
