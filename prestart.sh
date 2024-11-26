#!/bin/sh
# prestart.sh --- Initialize data stores. This script blocks application startup.
DB_MAX_CONNECTION_ATTEMPTS=10
DB_CONNECTION_ATTEMPT_INTERVAL=5

echo "Initializing database."

count=0
alembic_output=''
while [ ${count} -lt ${DB_MAX_CONNECTION_ATTEMPTS} ]; do
  count=$((count+1))

  set +e
  alembic_output=$(alembic upgrade head 2>&1)
  retval=$?
  set -e

  if [ $retval -eq 0 ]; then
    break
  fi

  sleep ${DB_CONNECTION_ATTEMPT_INTERVAL}
done

if [ $count -eq $DB_MAX_CONNECTION_ATTEMPTS ]; then
  echo "Unable to establish database connection, exiting."
  echo "$alembic_output" >&2
  exit 1
fi
echo "$alembic_output" >&2
