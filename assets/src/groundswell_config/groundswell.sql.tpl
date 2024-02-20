-- Groundswell database
CREATE DATABASE IF NOT EXISTS ${swell_database_name};
CREATE USER "${swell_db_user}" IDENTIFIED BY "${swell_db_password}";
GRANT ALL PRIVILEGES ON ${swell_database_name}.* TO ${swell_db_user}@"%";

FLUSH PRIVILEGES;