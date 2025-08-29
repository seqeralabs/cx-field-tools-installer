-- Postgres / gexec NEEDS single quotes in commands. Terraform tpl files strip them. This is a problem.
-- I abandoned the .tpl appraoch and wrote straight SQL with some placeholder values. These are replaced via `sed` in  010_prepare_config_files.tf
-- Solution is hacky but best I can come up with right now.

SELECT 'CREATE ROLE wave_lite_test_limited LOGIN PASSWORD ''wave_lite_test_limited_password'''
WHERE NOT EXISTS (
  SELECT FROM pg_roles WHERE rolname = 'wave_lite_test_limited'
)
\gexec

SELECT 'CREATE DATABASE wave'
WHERE NOT EXISTS (
  SELECT FROM pg_database WHERE datname = 'wave'
)
\gexec

GRANT ALL PRIVILEGES ON DATABASE wave TO wave_lite_test_limited;


-- Connect to the wave DB first
\c wave

-- Grant usage and privileges on schemas/tables
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO wave_lite_test_limited;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO wave_lite_test_limited;
GRANT USAGE, CREATE ON SCHEMA public TO wave_lite_test_limited;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL PRIVILEGES ON TABLES TO wave_lite_test_limited;
