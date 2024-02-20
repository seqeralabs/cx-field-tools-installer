# Tower settings
%{ if flag_use_container_db == false && startswith(db_engine_version, "8") == false ~}
TOWER_DB_URL=jdbc:mysql://${tower_db_url}/${db_database_name}
%{~ else ~}
TOWER_DB_URL=jdbc:mysql://${tower_db_url}/${db_database_name}?allowPublicKeyRetrieval=true&useSSL=false
%{ endif }
TOWER_DB_USER=${db_tower_user}
TOWER_DB_PASSWORD=${db_tower_password}

# Server settings
SWELL_SERVER_HOST=0.0.0.0
SWELL_SERVER_PORT=8090

# API settings
SWELL_API_TRAIN_TIMEOUT=60
SWELL_API_TRAIN_BATCH_SIZE=1000
SWELL_API_PREDICT_FRACTIONAL_CPUS=false

# Database settings
%{ if flag_use_container_db == false && startswith(db_engine_version, "8") == false ~}
SWELL_DB_URL=jdbc:mysql://${tower_db_url}/${swell_database_name}
%{~ else ~}
SWELL_DB_URL=jdbc:mysql://${tower_db_url}/${swell_database_name}?allowPublicKeyRetrieval=true&useSSL=false
%{ endif }
SWELL_DB_USER=${swell_db_user}
SWELL_DB_PASSWORD=${swell_db_password}
SWELL_DB_DIALECT=mysql