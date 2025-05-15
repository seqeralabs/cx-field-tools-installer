
# Terraform templatefile refuses to keep singlequotes in it. Unfortunately, commands to feed into postgres via
# docker CLI need the single quotes (and double single quotes for escaping).
# My old technique of a placeholder value for `'` replaced by sed wont work -- to verbose.
# Ive inverted the approach: Ditched the .tpl file, put in placeholders for the username/password, kept 
# the `'` and then sed username/password instead.
# This has `code smell` written all over it, but I need to get e2e working now and will figure out clean
# implementation afterwards.

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
