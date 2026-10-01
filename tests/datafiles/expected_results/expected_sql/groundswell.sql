-- Groundswell database
CREATE DATABASE IF NOT EXISTS swell;
-- Create the user only when it is missing (same reason as in tower.sql.tpl).
SET @user_missing = (SELECT COUNT(*) = 0 FROM mysql.user WHERE user = "swell_test_user" AND host = "%");
SET @create_user = IF(@user_missing, CONCAT("CREATE USER ", QUOTE("swell_test_user"), "@", QUOTE("%"), " ACCOUNT LOCK"), "DO 0");
PREPARE create_user_stmt FROM @create_user;
EXECUTE create_user_stmt;
DEALLOCATE PREPARE create_user_stmt;
ALTER USER "swell_test_user"@"%" IDENTIFIED BY "swell_test_password" ACCOUNT UNLOCK;
GRANT ALL PRIVILEGES ON swell.* TO swell_test_user@"%";

FLUSH PRIVILEGES;
