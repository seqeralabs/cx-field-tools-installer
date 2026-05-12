CREATE DATABASE tower;
ALTER DATABASE tower CHARACTER SET utf8 COLLATE utf8_bin;
CREATE USER "tower_test_user" IDENTIFIED BY "tower_test_password";
GRANT ALL PRIVILEGES ON tower.* TO tower_test_user@"%";
