# 40_enable-extensions.sh
# --- Enable OMS's WFS to use hash store for Attributes
# --- Enable OMS to match on Trigrams
# !/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname="$DB_NAME_OMSB" <<-EOSQL
  CREATE EXTENSION IF NOT EXISTS hstore;
EOSQL

echo "==> [EXTENSIONS] hstore extension enabled in $DB_NAME_OMSB."


psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname="$DB_NAME_OMSB" <<-EOSQL
  CREATE EXTENSION IF NOT EXISTS pg_trgm;
EOSQL

echo "==> [EXTENSIONS] pg_trgm extension enabled in $DB_NAME_OMSB."