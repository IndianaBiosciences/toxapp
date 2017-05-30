#!/usr/bin/env bash

sudo apt-get install postgresql
sudo apt-get install python-psycopg2
sudo apt-get install libpq-dev
sudo apt-get install python3-dev
sudo apt-get install pgloader

# location where celery will store communication files
sudo mkdir -p /tmp/celery/results
sudo chmod 777 /tmp/celery/results
