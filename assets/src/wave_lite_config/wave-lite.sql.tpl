-- Postgres db population

CREATE DATABASE wave;
CREATE USER postgres WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE wave TO postgres;
