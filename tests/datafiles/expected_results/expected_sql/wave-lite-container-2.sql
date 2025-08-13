-- Postgres / gexec NEEDS single quotes in commands. Terraform tpl files strip them. This is a problem.
-- I abandoned the .tpl appraoch and wrote straight SQL with some placeholder values. These are replaced via `sed` in  010_prepare_config_files.tf
-- Solution is hacky but best I can come up with right now.

-- This file will be run with `wave` as the current DB
GRANT ALL PRIVILEGES ON DATABASE wave TO wave_lite_test_limited;


-- Connect to the wave DB first
\c wave

-- Grant usage and privileges on schemas/tables
GRANT ALL ON SCHEMA public TO wave_lite_test_limited;
GRANT ALL ON ALL TABLES IN SCHEMA public TO wave_lite_test_limited;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO wave_lite_test_limited;
