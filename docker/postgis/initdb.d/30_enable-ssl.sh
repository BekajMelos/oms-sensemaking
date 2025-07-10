# 30_enable-ssl.sql --- Enable SSL with custom keypair.

# Copy certs to a writable directory and set ownership/permissions
if [ -f /opt/common/pki/server.public ] && [ -f /opt/common/pki/server.private ]; then

  # explicitly set ownership to match the user running postgresql/postgis
  chown postgres: /opt/common/pki/server.public
  chown postgres: /opt/common/pki/server.private

  # set file permissions
  chmod 600 /opt/common/pki/server.private
  chmod 640 /opt/common/pki/server.public

  # configure and enable SSL
  psql << EOF
ALTER SYSTEM SET ssl_cert_file TO '/opt/common/pki/server.public';
ALTER SYSTEM SET ssl_key_file TO '/opt/common/pki/server.private';
ALTER SYSTEM SET ssl TO 'ON';
EOF
else
  echo "Both service /opt/common/pki/server.public and /opt/common/pki/server.private are required for SSL" 1>&2;
fi
