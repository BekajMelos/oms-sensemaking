# 40_enable-extensions.sh
# --- Enable ATOMS's WFS to use hash store for Attributes
# --- Enable ATOMS to match on Trigrams
# --- Enable Postgres performance extension pg_stat_statements
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

# Configure pg_stat_statements
echo "shared_preload_libraries = 'pg_stat_statements'" >> "$PGDATA/postgresql.conf"
echo "pg_stat_statements.max = 10000" >> "$PGDATA/postgresql.conf"
echo "pg_stat_statements.track = all" >> "$PGDATA/postgresql.conf"

# Enable pg_stat_statements in the sensemaking database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname="$DB_NAME" <<-EOSQL
  CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
EOSQL
echo "==> [EXTENSIONS] pg_stat_statements extension enabled in $DB_NAME."