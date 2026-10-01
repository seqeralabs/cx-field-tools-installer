-- Groundswell database
CREATE DATABASE IF NOT EXISTS ${swell_database_name};
-- Create the user only when it is missing (same reason as in tower.sql.tpl).
SET @user_missing = (SELECT COUNT(*) = 0 FROM mysql.user WHERE user = "${swell_db_user}" AND host = "%");
SET @create_user = IF(@user_missing, CONCAT("CREATE USER ", QUOTE("${swell_db_user}"), "@", QUOTE("%"), " ACCOUNT LOCK"), "DO 0");
PREPARE create_user_stmt FROM @create_user;
EXECUTE create_user_stmt;
DEALLOCATE PREPARE create_user_stmt;
ALTER USER "${swell_db_user}"@"%" IDENTIFIED BY "${swell_db_password}" ACCOUNT UNLOCK;
GRANT ALL PRIVILEGES ON ${swell_database_name}.* TO ${swell_db_user}@"%";

FLUSH PRIVILEGES;
