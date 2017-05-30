#!/bin/bash

export PGPASSWORD='dbadmin'
psql -U dbadmin -d postgres < drop_db.sql
psql -U dbadmin -d postgres < init_db.sql
pg_restore -U dbadmin -d ibri $*
