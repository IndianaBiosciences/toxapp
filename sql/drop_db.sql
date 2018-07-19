DROP SCHEMA toxapp CASCADE;
-- drop all active connections
SELECT
    pg_terminate_backend(pid)
FROM
    pg_stat_activity
WHERE
    -- don't kill my own connection!
    pid <> pg_backend_pid()
    -- don't kill the connections to other databases
    AND datname = 'ibri'
    ;

DROP DATABASE ibri;
DROP USER django_user;
DROP USER toxapp; 
DROP ROLE toxapp_user;
DROP ROLE toxapp_reader;
