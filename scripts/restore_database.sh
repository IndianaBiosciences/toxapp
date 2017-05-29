#!/bin/bash

export PGPASSWORD='dbadmin'
pg_restore -U dbadmin -d ibri $*
