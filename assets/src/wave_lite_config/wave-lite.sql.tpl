-- 1. Create the user
-- WARNING: Postgres wants values in single quotes. However, terraform templatefile method breaks when they are used.
-- Hacky workaround is to use placeholder string representing the char and I replace with sed when the payload is actually emitted to file.
DO
$$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE rolname = SINGLEQUOTEREPLACEME${wave_lite_db_limited_user}SINGLEQUOTEREPLACEME ) THEN
      CREATE ROLE ${wave_lite_db_limited_user} LOGIN PASSWORD SINGLEQUOTEREPLACEME${wave_lite_db_limited_password}SINGLEQUOTEREPLACEME;
   END IF;
END
$$;

-- 2. Create the database
DO
$$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_database
      WHERE datname = SINGLEQUOTEREPLACEMEwaveSINGLEQUOTEREPLACEME) THEN
      CREATE DATABASE wave;
   END IF;
END
$$;

-- 3. Grant all privileges on the database
-- (must be done after DB is created, so we connect to it and run GRANT separately)
