#!/bin/bash

export PGPASSWORD='dbadmin'
psql -h 127.0.0.1 -U dbadmin -d postgres < drop_db.sql
psql -h 127.0.0.1 -U dbadmin -d postgres < init_db.sql
pg_restore -h 127.0.0.1 -U dbadmin -d ibri $*
