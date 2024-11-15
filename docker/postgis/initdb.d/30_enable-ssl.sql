-- 30_enable-ssl.sql --- Enable SSL with custom cert/key.
ALTER SYSTEM SET ssl_cert_file TO '/opt/common/pki/server.public';
ALTER SYSTEM SET ssl_key_file TO '/opt/common/pki/server.private';
--ALTER SYSTEM SET ssl_ca_file TO '/opt/common/pki/trusted.crt';
ALTER SYSTEM SET ssl TO 'ON';
