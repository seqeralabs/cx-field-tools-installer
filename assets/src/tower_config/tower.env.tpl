# ------------------------------------------------
# Generic Tower configuration values
# ------------------------------------------------
TOWER_ENABLE_AWS_SSM=true

LICENSE_SERVER_URL=https://licenses.seqera.io

TOWER_SERVER_URL=${tower_server_url}
TOWER_CONTACT_EMAIL=${tower_contact_email}
TOWER_ENABLE_PLATFORMS=${tower_enable_platforms}

%{ if flag_allow_aws_instance_credentials == true ~}
TOWER_ALLOW_INSTANCE_CREDENTIALS=true
%{ else ~}
TOWER_ALLOW_INSTANCE_CREDENTIALS=false
%{ endif ~}


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
# ENABLE OpenAPI
# Set this variable to enable the OpenAPI documentation endpoint
# ------------------------------------------------
%{ if tower_enable_openapi == true }
TOWER_ENABLE_OPENAPI=true
%{ else ~}
TOWER_ENABLE_OPENAPI=false
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
%{ else ~}
# TOWER_DATA_STUDIO_ALLOWED_WORKSPACES=DO_NOT_UNCOMMENT
%{ endif }

TOWER_DATA_STUDIO_CONNECT_URL=${tower_connect_server_url}
TOWER_OIDC_PEM_PATH=/data-studios-rsa.pem
TOWER_OIDC_REGISTRATION_INITIAL_ACCESS_TOKEN="ipsemlorem"

TOWER_DATA_STUDIO_DEFAULT_LIFESPAN=${data_studio_default_lifespan}
TOWER_DATA_STUDIO_PRIVATE_STUDIO_BY_DEFAULT=${flag_studio_private_by_default}
#-------------------------------------------------
# DATA STUDIO - METRICS
# ------------------------------------------------
%{ if data_studio_metrics_eligible_workspaces != "" ~}
TOWER_STUDIO_METRICS_ENABLED_WORKSPACES="${data_studio_metrics_eligible_workspaces}"
%{ else ~}
# TOWER_STUDIO_METRICS_ENABLED_WORKSPACES_NOT_SET=DO_NOT_UNCOMMENT
%{ endif ~}

%{ for ds in data_studio_options ~}
TOWER_DATA_STUDIO_TEMPLATES_${ds.qualifier}_ICON="${ds.icon}"
TOWER_DATA_STUDIO_TEMPLATES_${ds.qualifier}_REPOSITORY="${ds.container}"
TOWER_DATA_STUDIO_TEMPLATES_${ds.qualifier}_TOOL="${ds.tool != null ? ds.tool : ""}"
TOWER_DATA_STUDIO_TEMPLATES_${ds.qualifier}_STATUS="${ds.status != null ? ds.status : ""}"
%{ endfor ~}

%{ if flag_use_wave == true ~}

#-------------------------------------------------
# DATA STUDIO - WAVE INTEGRATION
# ------------------------------------------------
TOWER_DATA_STUDIO_WAVE_DISALLOWED_REGISTRIES=${data_studio_wave_disallowed_registries}
%{ if data_studio_wave_custom_image_registry != "" ~}
TOWER_DATA_STUDIO_WAVE_CUSTOM_IMAGE_REGISTRY=${data_studio_wave_custom_image_registry}
%{ else ~}
# TOWER_DATA_STUDIO_WAVE_CUSTOM_IMAGE_REGISTRY_NOT_SET=DO_NOT_UNCOMMENT
%{ endif ~}
%{ if data_studio_wave_custom_image_repository != "" ~}
TOWER_DATA_STUDIO_WAVE_CUSTOM_IMAGE_REPOSITORY=${data_studio_wave_custom_image_repository}
%{ else ~}
# TOWER_DATA_STUDIO_WAVE_CUSTOM_IMAGE_REPOSITORY_NOT_SET=DO_NOT_UNCOMMENT
%{ endif ~}

%{ endif ~}

%{ if flag_enable_data_studio_ssh == true ~}

#-------------------------------------------------
# DATA STUDIO - SSH ACCESS
# ------------------------------------------------
TOWER_SSH_KEYS_MANAGEMENT_ENABLED=true
CONNECT_SSH_ENABLED=true
TOWER_DATA_STUDIO_CONNECT_SSH_PORT=2222
%{ if flag_limit_data_studio_ssh_to_some_workspaces == true ~}
TOWER_DATA_STUDIO_SSH_ALLOWED_WORKSPACES="${data_studio_ssh_eligible_workspaces}"
%{ else ~}
TOWER_DATA_STUDIO_SSH_ALLOWED_WORKSPACES=
%{ endif ~}
TOWER_DATA_STUDIO_CONNECT_SSH_ADDRESS=${data_studio_ssh_address}
TOWER_DATA_STUDIO_CONNECT_SSH_KEY_FINGERPRINT=${connect_ssh_fingerprint}
TOWER_SSH_KEYS_SUPPORTED_TYPES=ssh-rsa,ssh-ed25519,ecdsa-sha2-nistp256,ecdsa-sha2-nistp384,ecdsa-sha2-nistp521

%{ else ~}

#-------------------------------------------------
# DATA STUDIO - SSH ACCESS (NOT ENABLED)
# ------------------------------------------------
# TOWER_SSH_KEYS_MANAGEMENT_ENABLED=DO_NOT_UNCOMMENT
# CONNECT_SSH_ENABLED=DO_NOT_UNCOMMENT
# TOWER_DATA_STUDIO_CONNECT_SSH_PORT=DO_NOT_UNCOMMENT
# TOWER_DATA_STUDIO_SSH_ALLOWED_WORKSPACES=DO_NOT_UNCOMMENT
# TOWER_DATA_STUDIO_CONNECT_SSH_ADDRESS=DO_NOT_UNCOMMENT
# TOWER_DATA_STUDIO_CONNECT_SSH_KEY_FINGERPRINT=DO_NOT_UNCOMMENT
# TOWER_SSH_KEYS_SUPPORTED_TYPES=DO_NOT_UNCOMMENT

%{ endif ~}

%{ else ~}
# STUDIOS_NOT_ENABLED=DO_NOT_UNCOMMENT
%{ endif }


#-------------------------------------------------
# PIPELINE VERSIONING
# ------------------------------------------------
%{ if tower_enable_pipeline_versioning == true ~}
TOWER_PIPELINE_VERSIONING_ALLOWED_WORKSPACES=${pipeline_versioning_eligible_workspaces}
%{ else ~}
# TOWER_PIPELINE_VERSIONING_NOT_ENABLED=DO_NOT_UNCOMMENT
%{ endif }


#-------------------------------------------------
# DATA LINEAGE (v26.1.0+)
# ------------------------------------------------
%{ if flag_enable_data_lineage == true ~}
TOWER_LINEAGE_ALLOWED_WORKSPACES=${data_lineage_allowed_workspaces}
%{ else ~}
# TOWER_LINEAGE_NOT_ENABLED=DO_NOT_UNCOMMENT
%{ endif }


#-------------------------------------------------
# COMPUTE ENVIRONMENT CLEANUP (v26.1.0+)
# ------------------------------------------------
%{ if tower_compute_env_cleanup.enabled == true ~}
TOWER_COMPUTE_ENV_CLEANUP_ENABLED=true
TOWER_COMPUTE_ENV_CLEANUP_DELAY=${tower_compute_env_cleanup.delay}
TOWER_COMPUTE_ENV_CLEANUP_INTERVAL=${tower_compute_env_cleanup.interval}
TOWER_COMPUTE_ENV_CLEANUP_BATCH_SIZE=${tower_compute_env_cleanup.batch_size}
TOWER_COMPUTE_ENV_CLEANUP_TIME_OFFSET=${tower_compute_env_cleanup.time_offset}
TOWER_COMPUTE_ENV_CLEANUP_STUCK_CREATING_TIMEOUT=${tower_compute_env_cleanup.stuck_creating_timeout}
TOWER_COMPUTE_ENV_CLEANUP_STUCK_DELETING_TIMEOUT=${tower_compute_env_cleanup.stuck_deleting_timeout}
%{ else ~}
# TOWER_COMPUTE_ENV_CLEANUP_NOT_ENABLED=DO_NOT_UNCOMMENT
%{ endif }


# AUDIT LOG V2 (v26.1.0+)
# ------------------------------------------------
TOWER_AUDIT_LOG_V2_WRITE_MODE=${tower_audit_log_v2.write_mode}
TOWER_AUDIT_LOG_V2_CSV_EXPORT_MAX_LOGS=${tower_audit_log_v2.csv_export_max_logs}
TOWER_AUDIT_LOG_V2_PRE_POST_CHANGE_ENABLED=${tower_audit_log_v2.pre_post_change_enabled}


#-------------------------------------------------
# CRON AUDIT LOG CLEANUP (v26.1.0+)
# ------------------------------------------------
%{ if tower_audit_log_v2.cleanup.enabled == true ~}
TOWER_CRON_AUDIT_LOG_CLEAN_UP_ENABLED=true
TOWER_CRON_AUDIT_LOG_CLEAN_UP_INTERVAL=${tower_audit_log_v2.cleanup.interval}
TOWER_CRON_AUDIT_LOG_CLEAN_UP_DELAY=${tower_audit_log_v2.cleanup.delay}
TOWER_CRON_AUDIT_LOG_CLEAN_UP_CHUNK_SIZE=${tower_audit_log_v2.cleanup.chunk_size}
%{ else ~}
TOWER_CRON_AUDIT_LOG_CLEAN_UP_ENABLED=false
%{ endif ~}


# ------------------------------------------------
# TEMPORARY WORKAROUND FOR MIGRATION SCRIPT
#  - Need to add database creds here due to migration script limitation (Dec 2023)
# ------------------------------------------------
# DB credentials will be here
