-- This file will be run with `wave` as the current DB
GRANT ALL PRIVILEGES ON DATABASE wave TO ${wave_lite_db_limited_user};


-- Connect to the wave DB first
\c wave

-- Grant usage and privileges on schemas/tables
GRANT ALL ON SCHEMA public TO ${wave_lite_db_limited_user};
GRANT ALL ON ALL TABLES IN SCHEMA public TO ${wave_lite_db_limited_user};
GRANT ALL ON ALL PRIVILEGES IN SCHEMA public TO ${wave_lite_db_limited_user};
