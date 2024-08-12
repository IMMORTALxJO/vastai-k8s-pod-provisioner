#!/bin/sh
set -e
python3 ./main.py
exec nginx -g "daemon off;"
