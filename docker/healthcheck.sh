#!/bin/sh
# healthcheck --- A script to run more than one healtcheck for the container.
set -e

pg_isready

if [ -z "$AWS_ENDPOINT_URL" ]; then
  curl -s -f "$AWS_ENDPOINT_URL/_localstack/health" | jq 'all(.services | to_entries | .[] .value; . as $a | ["running", "available"] | index($a))'
fi

exit 0
