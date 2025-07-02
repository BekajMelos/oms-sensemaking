# 30_enable-ssl.sql --- Enable SSL with custom keypair.


# Copy certs to a writable directory and set ownership/permissions
if [ -f /opt/common/pki/server.public ] && [ -f /opt/common/pki/server.private ]; then
  # ensure target dir exists
  mkdir -p /var/lib/postgresql

  # copy files to writable directory inside the container
  cp /opt/common/pki/server.public /var/lib/postgresql/data/server.crt
  cp /opt/common/pki/server.private /var/lib/postgresql/data/server.key

  # explicitly set ownership to match the user running postgresql/postgis
  chown postgres: /var/lib/postgresql/data/server.crt
  chown postgres: /var/lib/postgresql/data/server.key

  # set file permissions
  chmod 600 /var/lib/postgresql/data/server.key
  chmod 640 /var/lib/postgresql/data/server.crt

  # configure and enable SSL
  psql << EOF
ALTER SYSTEM SET ssl_cert_file TO '/var/lib/postgresql/data/server.crt';
ALTER SYSTEM SET ssl_key_file TO '/var/lib/postgresql/data/server.key';
ALTER SYSTEM SET ssl TO 'ON';
EOF
else
  echo "Both service /opt/common/pki/server.public and /opt/common/pki/server.private are required for SSL" 1>&2;
fi
