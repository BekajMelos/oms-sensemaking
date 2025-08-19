# 30_enable-ssl.sql --- Enable SSL with custom keypair.

#!/bin/bash
set -e

# Copy certs to a writable directory and set ownership/permissions
if [ -f "$UVICORN_SSL_CERTFILE" ] && [ -f "$UVICORN_SSL_KEYFILE" ]; then
  # explicitly set ownership to match the user running postgresql/postgis
  chown postgres: "$UVICORN_SSL_CERTFILE"
  chown postgres: "$UVICORN_SSL_KEYFILE"

  # set file permissions
  chmod 600 "$UVICORN_SSL_KEYFILE"
  chmod 640 "$UVICORN_SSL_CERTFILE"
  echo "==> [SSL] Ownership and file permissions set on certificate and key files."

  # configure and enable SSL
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname=postgres <<-EOSQL
    ALTER SYSTEM SET ssl_cert_file TO '$UVICORN_SSL_CERTFILE';
    ALTER SYSTEM SET ssl_key_file TO '$UVICORN_SSL_KEYFILE';
    ALTER SYSTEM SET ssl TO 'ON';
EOSQL
  echo "==> [SSL] SSL configuration applied."
else
  echo "==> [SSL] ERROR: Missing SSL configuration." 1>&2
  echo "    UVICORN_SSL_CERTFILE: ${UVICORN_SSL_CERTFILE:-<empty>}" 1>&2
  echo "    UVICORN_SSL_KEYFILE: ${UVICORN_SSL_KEYFILE:-<empty>}" 1>&2
fi