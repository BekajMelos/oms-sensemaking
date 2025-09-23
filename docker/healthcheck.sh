#!/bin/sh
# healthcheck --- Simple healthcheck for Postgres.

if ! pg_isready; then
  exit $?
fi

exit 0
