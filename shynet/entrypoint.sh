#!/bin/bash

if [[ ! $PERFORM_CHECKS_AND_SETUP == False ]]; then
  ./startup_checks.sh && exec ./webserver.sh
  else
  exec ./webserver.sh
fi