
# docker run --rm -t -v /home/ec2-user/target/wave_lite_config/wave-lite.sql:/tmp/wave.sql -e POSTGRES_PASSWORD=masterpassword --entrypoint /bin/bash postgres:latest -c "PGPASSWORD='masterpassword' psql -h tf-tower-dev-native-mutt-db-wave-lite.cushz2sgcalb.us-east-1.rds.amazonaws.com -p 5432 -U masteruser -d postgres < /tmp/wave.sql"

#SQL1
SELECT 'CREATE ROLE postgresuser LOGIN PASSWORD ''postgrespass'''
WHERE NOT EXISTS (
  SELECT FROM pg_roles WHERE rolname = 'postgresuser'
)
\gexec

SELECT 'CREATE DATABASE wave'
WHERE NOT EXISTS (
  SELECT FROM pg_database WHERE datname = 'wave'
)
\gexec



# SQL2
-- This file will be run with `wave` as the current DB
GRANT ALL PRIVILEGES ON DATABASE wave TO postgresuser;


-- Connect to the wave DB first
\c wave

-- Grant usage and privileges on schemas/tables
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgresuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgresuser;
GRANT USAGE, CREATE ON SCHEMA public TO postgresuser;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL PRIVILEGES ON TABLES TO postgresuser;
