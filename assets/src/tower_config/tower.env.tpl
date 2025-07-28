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
TOWER_DB_URL=${tower_db_url}

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
%{ if flag_use_aws_ses_iam_integration == true ~}
TOWER_ENABLE_AWS_SES=true
%{ else ~}
TOWER_ENABLE_AWS_SES=false
%{ endif ~}

%{ if flag_use_existing_smtp == true ~}
TOWER_SMTP_HOST=${tower_smtp_host}
TOWER_SMTP_PORT=${tower_smtp_port}

# TOWER_SMTP_USER sourced from SSM.
# TOWER_SMTP_PASSWORD sourced from SSM.
%{ endif ~}


# ------------------------------------------------
# HTTP vs HTTPS
# Set this variable explicitly based on certificate usage.
# ------------------------------------------------
%{ if flag_do_not_use_https == true }
TOWER_ENABLE_UNSAFE_MODE=true
%{ else ~}
TOWER_ENABLE_UNSAFE_MODE=false
%{ endif ~}


# ------------------------------------------------
# Wave & Fusion v2
# ------------------------------------------------
WAVE_SERVER_URL=${wave_server_url}
%{ if flag_use_wave == true ~}
TOWER_ENABLE_WAVE=true
%{ else ~}
TOWER_ENABLE_WAVE=false
%{ endif ~}


# ------------------------------------------------
# Groundswell
# Pipeline resource optimization service.
# ------------------------------------------------
%{ if flag_enable_groundswell == true ~}
GROUNDSWELL_SERVER_URL="http://groundswell:8090"
TOWER_ENABLE_GROUNDSWELL=true
%{ else ~}
TOWER_ENABLE_GROUNDSWELL=false
%{ endif ~}


# ------------------------------------------------
# Data Explorer
# ------------------------------------------------
%{ if flag_data_explorer_enabled == true ~}
TOWER_DATA_EXPLORER_ENABLED=true
TOWER_DATA_EXPLORER_CLOUD_DISABLED_WORKSPACES="${data_explorer_disabled_workspaces}"
%{ else ~}
TOWER_DATA_EXPLORER_ENABLED=false
%{ endif ~}



# ------------------------------------------------
# OIDC
# ------------------------------------------------
# OIDC configuration activated via docker-compose.yml MICRONAUT_ENVIRONMENTS variable.


#-------------------------------------------------
# DATA STUDIO
# ------------------------------------------------
%{ if flag_enable_data_studio == true ~}

%{ if flag_studio_enable_path_routing == true ~}
TOWER_DATA_STUDIO_ENABLE_PATH_ROUTING=true
%{ else ~}
TOWER_DATA_STUDIO_ENABLE_PATH_ROUTING=false
%{ endif }

%{ if flag_limit_data_studio_to_some_workspaces == true ~}
TOWER_DATA_STUDIO_ALLOWED_WORKSPACES="${data_studio_eligible_workspaces}"
%{ endif }

TOWER_DATA_STUDIO_CONNECT_URL=${tower_connect_server_url}
TOWER_OIDC_PEM_PATH=/data-studios-rsa.pem
TOWER_OIDC_REGISTRATION_INITIAL_ACCESS_TOKEN="ipsemlorem"

%{ for ds in data_studio_options ~}
TOWER_DATA_STUDIO_TEMPLATES_${ds.qualifier}_ICON="${ds.icon}"
TOWER_DATA_STUDIO_TEMPLATES_${ds.qualifier}_REPOSITORY="${ds.container}"
TOWER_DATA_STUDIO_TEMPLATES_${ds.qualifier}_TOOL="${ds.tool != null ? ds.tool : ""}"
TOWER_DATA_STUDIO_TEMPLATES_${ds.qualifier}_STATUS="${ds.status != null ? ds.status : ""}"
%{ endfor ~}

%{ endif }


# ------------------------------------------------
# TEMPORARY WORKAROUND FOR MIGRATION SCRIPT
#  - Need to add database creds here due to migration script limitation (Dec 2023)
# ------------------------------------------------
# DB credentials will be here
