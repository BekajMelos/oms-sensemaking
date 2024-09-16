#!/bin/sh
#
# Initialize users after the application has started up.
#

aac2_ready() {
    curl http://localhost:3000 &> /dev/null
    return $?
}

initialize_users() {
  while ! aac2_ready; do
      echo "Waiting for AAC2 to initialize..."
      sleep 5
  done

  echo "Initializing users..."
  for user_file in ./users/*.json; do
    echo "Loading user file: ${user_file}"
    curl -v -k --location \
      --request PUT 'http://localhost:3000/caches' \
      --header 'Content-Type: application/json' \
      --data "@${user_file}"
  done
}

# Start up initialize user in the background.
# Users will be initialized after app has started.
initialize_users &

# Start up the app
echo "Starting AAC2"
exec /app/ent-aac-service
