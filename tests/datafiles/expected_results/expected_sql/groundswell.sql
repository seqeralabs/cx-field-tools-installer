-- Groundswell database
CREATE DATABASE IF NOT EXISTS swell;
CREATE USER "swell_test_user" IDENTIFIED BY "swell_test_password";
GRANT ALL PRIVILEGES ON swell.* TO swell_test_user@"%";

FLUSH PRIVILEGES;
