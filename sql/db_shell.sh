#!/bin/bash

export PGPASSWORD='toxapp'
psql -h 127.0.0.1 -U django_user -d ibri
