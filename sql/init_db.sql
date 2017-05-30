-- log in via psql -U dbadmin -d postgres
create database ibri;
create role toxapp_user;
create role toxapp_reader;
create user django_user password 'toxapp';
grant toxapp_user to django_user;
create user toxapp nologin;
create schema toxapp authorization toxapp;
grant all on schema toxapp to toxapp_user;
grant usage on schema toxapp to toxapp_reader;
alter DATABASE ibri SET search_path TO toxapp;
