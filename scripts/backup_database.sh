#!/bin/bash

export DTE=`date +'%Y-%m-%d_%H%M%S'`
export PGPASSWORD='dbadmin'
pg_dump -U dbadmin -d ibri -Fc  > ibri_db_$DTE.dump
