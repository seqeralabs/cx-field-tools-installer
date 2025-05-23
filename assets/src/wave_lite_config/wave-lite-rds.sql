-- Postgres / gexec NEEDS single quotes in commands. Terraform tpl files strip them. This is a problem.
-- I abandoned the .tpl appraoch and wrote straight SQL with some placeholder values. These are replaced via `sed` in  010_prepare_config_files.tf
-- Solution is hacky but best I can come up with right now.

SELECT 'CREATE ROLE replace_me_wave_lite_db_limited_user LOGIN PASSWORD ''replace_me_wave_lite_db_limited_password'''
WHERE NOT EXISTS (
  SELECT FROM pg_roles WHERE rolname = 'replace_me_wave_lite_db_limited_user'
)
\gexec

SELECT 'CREATE DATABASE wave'
WHERE NOT EXISTS (
  SELECT FROM pg_database WHERE datname = 'wave'
)
\gexec

GRANT ALL PRIVILEGES ON DATABASE wave TO replace_me_wave_lite_db_limited_user;


-- Connect to the wave DB first
\c wave

-- Grant usage and privileges on schemas/tables
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO replace_me_wave_lite_db_limited_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO replace_me_wave_lite_db_limited_user;
GRANT USAGE, CREATE ON SCHEMA public TO replace_me_wave_lite_db_limited_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL PRIVILEGES ON TABLES TO replace_me_wave_lite_db_limited_user;
