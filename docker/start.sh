#!/usr/bin/env sh
# start.sh --- Start script for FastAPI applications.
# Adapted from https://github.com/tiangolo/uvicorn-gunicorn-docker/blob/master/docker-images/start.sh
# This script will check for a script located at $APP_HOME/prestart.sh, which
# can be used to perform actions before uvicorn starts the application.
set -e

if [ -f /app/app/main.py ]; then
    DEFAULT_MODULE_NAME=app.main
elif [ -f /app/main.py ]; then
    DEFAULT_MODULE_NAME=main
fi
MODULE_NAME=${MODULE_NAME:-$DEFAULT_MODULE_NAME}
VARIABLE_NAME=${VARIABLE_NAME:-app}
export APP_MODULE=${APP_MODULE:-"$MODULE_NAME:$VARIABLE_NAME"}

# configure uvicorn
UVICORN_HOST=${UVICORN_HOST:-${HOST:-0.0.0.0}}
UVICORN_PORT=${UVICORN_PORT:-80}
UVICORN_ROOT_PATH=${UVICORN_ROOT_PATH:-}
UVICORN_LOG_LEVEL=${UVICORN_LOG_LEVEL:-error}

# If there's a prestart.sh script in the /app directory or other path specified, run it before starting
PRE_START_PATH=${PRE_START_PATH:-$APP_HOME/prestart.sh}
echo "Checking for script in $PRE_START_PATH"
if [ -f $PRE_START_PATH ] ; then
    echo "Running script $PRE_START_PATH"
    . "$PRE_START_PATH"
else
    echo "There is no script $PRE_START_PATH"
fi

cat /etc/motd

# if we do not have a root_path, we can't send an empty string as an arg
if [ -n "$UVICORN_ROOT_PATH" ]; then
  UVICORN_ROOT_PATH_ARG="--root-path $UVICORN_ROOT_PATH"
else
  UVICORN_ROOT_PATH_ARG=""
fi

# Start uvicorn - relies on env var configuration (see https://www.uvicorn.org/settings/)
if [ -z "$RELOAD_APP" ]; then
  exec uvicorn --host $UVICORN_HOST $APP_MODULE $UVICORN_ROOT_PATH_ARG
else
  exec uvicorn --host $UVICORN_HOST --reload $APP_MODULE $UVICORN_ROOT_PATH_ARG
fi
