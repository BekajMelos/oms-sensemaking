# 40_enable-hstore.sh --- Enable OMS's WFS to use hash store for Attributes
# !/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname="$DB_NAME_OMSB" <<-EOSQL
  CREATE EXTENSION IF NOT EXISTS hstore;
EOSQL

echo "==> [HSTORE] hstore extension enabled in $DB_NAME_OMSB."