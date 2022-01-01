#!/bin/bash

# always provide valid host header
HOST="${ALLOWED_HOSTS%%,*}"
[ -z "$HOST" ] && HOST="127.0.0.1"
[ "$HOST" = "*" ] && HOST="127.0.0.1"

exec wget -o /dev/null -O /dev/null --header "Host: $HOST" "http://127.0.0.1:$PORT/healthz/?format=json"
