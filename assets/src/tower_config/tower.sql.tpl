CREATE DATABASE IF NOT EXISTS ${db_database_name};
ALTER DATABASE ${db_database_name} CHARACTER SET utf8 COLLATE utf8_bin;
CREATE USER IF NOT EXISTS "${db_tower_user}" IDENTIFIED BY "${db_tower_password}";
GRANT ALL PRIVILEGES ON ${db_database_name}.* TO ${db_tower_user}@"%";
