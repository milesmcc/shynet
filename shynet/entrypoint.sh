#!/bin/bash

if [[ ! $PERFORM_CHECKS_AND_SETUP == False ]]; then
  ./startup_checks.sh
fi

./webserver.sh
