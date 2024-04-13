# ------------------------------------------------
# Generic Tower configuration values
# ------------------------------------------------
TOWER_ENABLE_AWS_SSM=true
LICENSE_SERVER_URL=https://licenses.seqera.io

TOWER_SERVER_URL=${tower_server_url}
TOWER_CONTACT_EMAIL=${tower_contact_email}
TOWER_ENABLE_PLATFORMS=${tower_enable_platforms}


# ------------------------------------------------
# Add Tower root users
# ------------------------------------------------
TOWER_ROOT_USERS=${tower_root_users}


# ------------------------------------------------
# DB settings
# ------------------------------------------------
# MySQL8 needs extra connection modifiers for most clients.
%{ if flag_use_container_db == false && startswith(db_engine_version, "8") == false ~}
TOWER_DB_URL=jdbc:mysql://${tower_db_url}/tower
%{~ else ~}
TOWER_DB_URL=jdbc:mysql://${tower_db_url}/tower?allowPublicKeyRetrieval=true&useSSL=false
%{ endif }
TOWER_DB_DRIVER=${tower_db_driver}
TOWER_DB_DIALECT=${tower_db_dialect}
TOWER_DB_MIN_POOL_SIZE=${tower_db_min_pool_size}
TOWER_DB_MAX_POOL_SIZE=${tower_db_max_pool_size}
TOWER_DB_MAX_LIFETIME=${tower_db_max_lifetime}
FLYWAY_LOCATIONS=${flyway_locations}
# TOWER_DB_USER sourced from SSM.
# TOWER_DB_PASSWORD sourced from SSM.


# ------------------------------------------------
# Redis settings
# ------------------------------------------------
TOWER_REDIS_URL=${tower_redis_url}


# ------------------------------------------------
# SMTP settings
# ------------------------------------------------
%{ if flag_use_aws_ses_iam_integration == true && flag_new_enough_for_ses_iam == true ~}
TOWER_ENABLE_AWS_SES=true
%{~ else ~}
TOWER_ENABLE_AWS_SES=false
%{~ endif ~}

%{ if flag_use_existing_smtp == true || flag_new_enough_for_ses_iam == false }
TOWER_SMTP_HOST=${tower_smtp_host}
TOWER_SMTP_PORT=${tower_smtp_port} 
# TOWER_SMTP_USER sourced from SSM.
# TOWER_SMTP_PASSWORD sourced from SSM.
%{ endif ~}


# ------------------------------------------------
# HTTP vs HTTPS
# Set this variable explicitly based on certificate usage.
# ------------------------------------------------

%{~ if flag_do_not_use_https == true }
TOWER_ENABLE_UNSAFE_MODE=true
%{~ else ~}
TOWER_ENABLE_UNSAFE_MODE=false
%{ endif ~}


# ------------------------------------------------
# Wave & Fusion v2
# ------------------------------------------------
WAVE_SERVER_URL=https://wave.seqera.io
%{~ if flag_use_wave == true }
TOWER_ENABLE_WAVE=true
%{~ else }
TOWER_ENABLE_WAVE=false
%{ endif ~}


# ------------------------------------------------
# Groundswell
# ------------------------------------------------
%{ if flag_enable_groundswell == true && flag_new_enough_for_groundswell}
GROUNDSWELL_SERVER_URL="http://groundswell:8090"
TOWER_ENABLE_GROUNDSWELL=true
%{~ endif ~}


# ------------------------------------------------
# Data Explorer
# ------------------------------------------------
%{ if flag_data_explorer_enabled == true}
TOWER_DATA_EXPLORER_ENABLED=true
%{~ else }
TOWER_DATA_EXPLORER_ENABLED=false
%{ endif }
TOWER_DATA_EXPLORER_CLOUD_DISABLED_WORKSPACES="${data_explorer_disabled_workspaces}"

# ------------------------------------------------
# OIDC
# OIDC configuration activated via docker-compose.yml MICRONAUT_ENVIRONMENTS variable.
# ------------------------------------------------


# ------------------------------------------------
# TEMPORARY WORKAROUND FOR MIGRATION SCRIPT
#  - Need to add database creds here due to migration script limitation (Dec 2023)
# ------------------------------------------------