#!/bin/bash
#has to use Unix line encoding to execute properly, the commands will be visible in database log when executed
set -e

psql -v ON_ERROR_STOP=1 --username postgres --dbname postgres <<-EOSQL
    CREATE USER admin WITH ENCRYPTED PASSWORD 'admin';
    CREATE DATABASE db;
    GRANT ALL PRIVILEGES ON DATABASE db TO admin;
EOSQL
psql -v ON_ERROR_STOP=1 --username admin --password admin --dbname db <<-EOSQL
	\connect db
  CREATE SCHEMA data;
	\exit
EOSQL