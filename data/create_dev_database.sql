SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'edu'
AND pid <> pg_backend_pid();
CREATE DATABASE edu_dev
WITH TEMPLATE edu
OWNER postgres;