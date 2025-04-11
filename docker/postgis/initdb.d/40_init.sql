-- 40_init.sql --- Enable OMS's WFS to use hash store for Attributes

\connect omsb_db
CREATE EXTENSION hstore;
