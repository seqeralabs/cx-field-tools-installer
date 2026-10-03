CREATE DATABASE IF NOT EXISTS tower;
ALTER DATABASE tower CHARACTER SET utf8 COLLATE utf8_bin;
-- Create the user only when it is missing. MySQL 8.4 checks for view definers before it honours
-- IF NOT EXISTS, and that check needs ALLOW_NONEXISTENT_DEFINER (sql_user.cc; the refman also names
-- SET_ANY_DEFINER, but the code does not check it). The RDS master user lacks it, so an existing user
-- that owns a view fails with ERROR 4006. The new user starts locked with no password; ALTER USER below
-- sets the password and unlocks it, so the password never appears in dynamic SQL.
-- No single quotes in this file: it is written by a single-quoted echo.
-- See documentation/setup/upgrade_mysql_8_4.md, "Why the database setup scripts changed for MySQL 8.4".
SET @user_missing = (SELECT COUNT(*) = 0 FROM mysql.user WHERE user = "tower_test_user" AND host = "%");
SET @create_user = IF(@user_missing, CONCAT("CREATE USER ", QUOTE("tower_test_user"), "@", QUOTE("%"), " ACCOUNT LOCK"), "DO 0");
PREPARE create_user_stmt FROM @create_user;
EXECUTE create_user_stmt;
DEALLOCATE PREPARE create_user_stmt;
ALTER USER "tower_test_user"@"%" IDENTIFIED BY "tower_test_password" ACCOUNT UNLOCK;
GRANT ALL PRIVILEGES ON tower.* TO tower_test_user@"%";