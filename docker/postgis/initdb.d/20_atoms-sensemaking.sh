# 20_oms-sensemaking.sh --- Create databases and database user for ATOMS Sensemaking.

#!/bin/bash
set -e

# Create application user
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname=postgres <<-EOSQL
  CREATE USER $DB_USER WITH ENCRYPTED PASSWORD '$DB_PASSWORD';
EOSQL
echo "==> [Init] User $DB_USER created."

# Create main application database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname=postgres <<-EOSQL
  CREATE DATABASE $DB_NAME TEMPLATE $DB_TEMPLATE;
  GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOSQL
echo "==> [Init] Main application database $DB_NAME created and privileges granted."

# Grant schema permissions
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname="$DB_NAME" <<-EOSQL
  GRANT ALL ON SCHEMA public TO $DB_USER;
EOSQL
echo "==> [Init] Schema permissions granted to $DB_USER on $DB_NAME."

# Create test database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
  CREATE DATABASE ${DB_NAME}_test TEMPLATE $DB_TEMPLATE;
  GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME}_test TO $DB_USER;
EOSQL
echo "==> [Init] Test database ${DB_NAME}_test created and privileges granted."

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname="${DB_NAME}_test" <<-EOSQL
  GRANT ALL ON SCHEMA public TO $DB_USER;
EOSQL
echo "==> [Init] Schema permissions granted to $DB_USER on ${DB_NAME}_test."

# Create OMSB database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
  CREATE DATABASE ${DB_NAME_OMSB} TEMPLATE $DB_TEMPLATE;
  GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME_OMSB} TO $DB_USER;
EOSQL
echo "==> [Init] OMSB database $DB_NAME_OMSB created and privileges granted."


psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname=${DB_NAME_OMSB} <<-EOSQL
  GRANT ALL ON SCHEMA public TO $DB_USER;
EOSQL
echo "==> [Init] Schema permissions granted to $DB_USER on $DB_NAME_OMSB."