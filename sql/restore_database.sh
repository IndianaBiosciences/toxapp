#!/bin/bash

export PGPASSWORD='dbadmin'
psql -h 127.0.0.1 -U dbadmin -d postgres < drop_db.sql
psql -h 127.0.0.1 -U dbadmin -d postgres < init_db.sql
echo 'pg_restore will warn about shema toxapp already existing; ignore the warning; 2 related errors are anticipated'
pg_restore -h 127.0.0.1 -U dbadmin -d ibri $*
