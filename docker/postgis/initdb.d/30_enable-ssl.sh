# 30_enable-ssl.sql --- Enable SSL with custom keypair.

#!/bin/bash
set -e

# Copy certs to a writable directory and set ownership/permissions
if [ -f "$HOST_TLS_CERT_FILE" ] && [ -f "$HOST_TLS_KEY_FILE" ]; then
  # explicitly set ownership to match the user running postgresql/postgis
  chown postgres: "$HOST_TLS_CERT_FILE"
  chown postgres: "$HOST_TLS_KEY_FILE"

  # set file permissions
  chmod 600 "$HOST_TLS_KEY_FILE"
  chmod 640 "$HOST_TLS_CERT_FILE"
  echo "==> [SSL] Ownership and file permissions set on certificate and key files."

  # configure and enable SSL
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname=postgres <<-EOSQL
    ALTER SYSTEM SET ssl_cert_file TO '$HOST_TLS_CERT_FILE';
    ALTER SYSTEM SET ssl_key_file TO '$HOST_TLS_KEY_FILE';
    ALTER SYSTEM SET ssl TO 'ON';
EOSQL
  echo "==> [SSL] SSL configuration applied."
else
  echo "==> [SSL] ERROR: Both $HOST_TLS_CERT_FILE and $HOST_TLS_KEY_FILE are required for SSL" 1>&2
fi