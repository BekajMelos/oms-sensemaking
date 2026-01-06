#!/bin/sh
# prestart.sh --- Initialize data stores. This script blocks application startup.
DB_MAX_CONNECTION_ATTEMPTS=10
DB_CONNECTION_ATTEMPT_INTERVAL=5

echo "Initializing database."
sleep 3
count=0
alembic_output=''
while [ ${count} -lt ${DB_MAX_CONNECTION_ATTEMPTS} ]; do
  count=$((count+1))

  set +e
  alembic_output=$(alembic upgrade head 2>&1)
  retval=$?
  set -e

  if [ ${retval} -eq 0 ]; then
    echo "Database initialized successfully."
    break
  fi

  if echo $alembic_output | grep -q "ALEMBIC_FAIL:AUTH_ISSUE"; then
    echo "Incorrect database credentials."
    echo "$alembic_output" >&2
    exit 1
  elif echo $alembic_output | grep -q "ALEMBIC_FAIL:HOST/PORT ISSUE"; then
    echo "HOST or PORT issues."
  elif echo $alembic_output | grep -q "ALEMBIC_FAIL:NETWORK ISSUE"; then
    echo "Connection time out."
  fi

  echo "Attempting connection in ${DB_CONNECTION_ATTEMPT_INTERVAL} seconds (${count}/${DB_MAX_CONNECTION_ATTEMPTS})..."
  sleep ${DB_CONNECTION_ATTEMPT_INTERVAL}
  if [ ${count} -eq ${DB_MAX_CONNECTION_ATTEMPTS} ]; then
    echo "Unable to establish database connection. Exiting."
    echo "$alembic_output" >&2
    sleep 100000
    exit 1
  fi
done
echo "$alembic_output" >&2

