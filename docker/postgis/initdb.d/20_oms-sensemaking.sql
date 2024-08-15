-- 20_db-user.sql --- Create databases and database user for OMS Sensemaking.
CREATE USER appuser WITH ENCRYPTED PASSWORD 'password';

--------------------
-- App Database
--------------------
-- create application database
CREATE DATABASE oms_sensemaking TEMPLATE template_postgis;

-- grant privileges
GRANT ALL PRIVILEGES ON DATABASE oms_sensemaking TO appuser;
\c oms_sensemaking postgres
GRANT ALL ON SCHEMA public TO appuser;


--------------------
-- Test Database
--------------------
-- create application database
CREATE DATABASE oms_sensemaking_test TEMPLATE template_postgis;

-- grant privileges
GRANT ALL PRIVILEGES ON DATABASE oms_sensemaking_test TO appuser;
\c oms_sensemaking_test postgres
GRANT ALL ON SCHEMA public TO appuser;
