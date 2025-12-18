#!/bin/sh
# prestart.sh --- Initialize data stores. This script blocks application startup.
DB_MAX_CONNECTION_ATTEMPTS=10
DB_CONNECTION_ATTEMPT_INTERVAL=5

echo "Initializing database."

count=0
alembic_output=''
while [ ${count} -lt ${DB_MAX_CONNECTION_ATTEMPTS} ]; do
  # count=$((count+1))

  set +e
  alembic_output=$(alembic upgrade head 2>&1)
  retval=$?
  set -e

  if [ ${retval} -eq 0 ]; then
    echo "Database initialized successfully."
    break
  fi
  count=$((count+1))
  echo "Error: Alembic failed with exit code ${retval}."
  echo "Attempting connection in ${DB_CONNECTION_ATTEMPT_INTERVAL} seconds (${count}/${DB_MAX_CONNECTION_ATTEMPTS})..."
  
  sleep ${DB_CONNECTION_ATTEMPT_INTERVAL}
done

if [ ${count} -eq ${DB_MAX_CONNECTION_ATTEMPTS} ]; then
  echo "Error: Unable to establish database connection, exiting."
  echo "$alembic_output" >&2
  sleep 100000
  exit 1
fi
echo "$alembic_output" >&2
