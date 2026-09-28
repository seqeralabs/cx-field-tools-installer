-- Groundswell database
CREATE DATABASE IF NOT EXISTS swell;
CREATE USER IF NOT EXISTS "swell_test_user" IDENTIFIED BY "swell_test_password";
ALTER USER "swell_test_user" IDENTIFIED BY "swell_test_password";
GRANT ALL PRIVILEGES ON swell.* TO swell_test_user@"%";

FLUSH PRIVILEGES;
