#!/bin/sh
# healthcheck --- A script to run more than one healtcheck for the container.

# 1. Check postgres connection
if ! pg_isready; then
  exit $?
fi

# 2. Check AWS/localstack connection
if [ -n "$AWS_ENDPOINT_URL" ]; then
  localstack_status=$(curl -s -f "$AWS_ENDPOINT_URL/_localstack/health")
  localstack_retval=$?

  if [ "$localstack_retval" -ne 0 ]; then
    echo "Unable to connect to AWS/localstack" 1>&2
    exit $localstack_retval
  else
    echo "$localstack_status" | jq 'all(.services | to_entries | .[] .value; . as $a | ["running", "available"] | index($a))'
  fi
fi

exit 0
