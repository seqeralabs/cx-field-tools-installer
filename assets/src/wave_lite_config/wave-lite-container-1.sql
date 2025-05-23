-- Postgres / gexec NEEDS single quotes in commands. Terraform tpl files strip them. This is a problem.
-- I abandoned the .tpl appraoch and wrote straight SQL with some placeholder values. These are replaced via `sed` in  010_prepare_config_files.tf
-- Solution is hacky but best I can come up with right now.

-- 1. Create the user
DO
$$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE rolname = 'replace_me_wave_lite_db_limited_user' ) THEN
      CREATE ROLE replace_me_wave_lite_db_limited_user LOGIN PASSWORD 'replace_me_wave_lite_db_limited_password';
   END IF;
END
$$;

-- 2. Create the database
DO
$$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_database
      WHERE datname = 'wave') THEN
      CREATE DATABASE wave;
   END IF;
END
$$;

-- 3. Grant all privileges on the database
-- (must be done after DB is created, so we connect to it and run GRANT separately)
