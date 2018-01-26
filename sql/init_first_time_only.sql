-- this script only to be used for first time setup on a native postgres install
-- for backup/restore use the backup_database.sh and restore_database.sh scripts
-- steps below require manual login to the sql shell and execution of commands

-- log in via: psql -U postgres on windows; sudo -i psql -U postgres on ubuntu
create role dbadmin with superuser login password 'dbadmin';
-- log in via psql -U dbadmin -d postgres
drop schema public;
