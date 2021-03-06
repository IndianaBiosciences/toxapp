#!/usr/bin/env bash

sudo apt-get install postgresql
sudo apt-get install python-psycopg2
sudo apt-get install libpq-dev
sudo apt-get install python3-dev
sudo apt-get install pgloader
sudo apt-get install bblas-dev
sudo apt-get install liblapack-dev
sudo apt-get install r-base
sudo apt-get install libxml2-dev
sudo apt-get install libcurl4-openssl-dev
sudo pip3 install -r requirements.txt

# run the database setup scripts; could vary depending on other postgres databases already running
psql -U postgres -d postgres < sql/init_first_time_only.sql
psql -U dbadmin -d postgres <sql/init_db.sql

# location where celery will store communication files
sudo mkdir -p /tmp/celery/results
sudo chmod 777 /tmp/celery/results

sudo mkdir -p /var/www/toxapp/leiden_exports
sudo chmod 777 /var/www/toxapp/leiden_exports
sudo mkdir -p /var/www/toxapp/bm2_files
sudo chmod 777 /var/www/toxapp/bm2_files

sudo mkdir -p toxapp/tp/static/site_media

# set up R dependencies
R --vanilla < scripts/setup.R

# install BMD Express
sudo rpm -i https://github.com/auerbachs/BMDExpress-2/releases/download/untagged-aaff85c25413660b98ac/BMDExpress2_2_for_Linux.rpm

# build the database from scratch; alternative is to use the restore_database.sh script
python3 ./manage.py migrate
python3 ./manage.py makemigrations tp
python3 ./manage.py sqlmigrate tp 0001
python3 ./manage.py migrate

# create logfile directory and initial log - not under source code control
mkdir logfile
touch logfile/toxapp.log

# long running process to setup database with DM/TG data
python3 ./scripts/init_database.py > init_db.log 2>&1
