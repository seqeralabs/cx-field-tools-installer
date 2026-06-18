# Data studios settings
%{ if flag_enable_data_studio == true ~}

# IDENTICAL AS `TOWER_SERVER_URL` in `tower.env`
PLATFORM_URL=${tower_server_url}

CONNECT_HTTP_PORT=9090
CONNECT_TUNNEL_URL=connect-server:7070
CONNECT_PROXY_URL=${tower_connect_server_url}
CONNECT_LISTENER_PORT=${connect_listener_port}
CONNECT_TUNNEL_PORT=${connect_tunnel_port}
CONNECT_STORAGE_ROOT=${connect_storage_root}
%{ if connect_host_domain != "" ~}
CONNECT_HOST_DOMAIN=${connect_host_domain}
%{ else ~}
# CONNECT_HOST_DOMAIN_NOT_SET=DO_NOT_UNCOMMENT
%{ endif ~}
%{ if connect_management_port != "" ~}
CONNECT_MANAGEMENT_PORT=${connect_management_port}
%{ else ~}
# CONNECT_MANAGEMENT_PORT_NOT_SET=DO_NOT_UNCOMMENT
%{ endif ~}
%{ if connect_management_auth_key != "" ~}
CONNECT_MANAGEMENT_AUTH_KEY=${connect_management_auth_key}
%{ else ~}
# CONNECT_MANAGEMENT_AUTH_KEY_NOT_SET=DO_NOT_UNCOMMENT
%{ endif ~}

CONNECT_REDIS_ADDRESS=${tower_redis_url}

# Use the same Redis as Tower but a different logical namespace
CONNECT_REDIS_DB=1
# CONNECT_REDIS_USER sourced from SSM (optional; only required if Redis auth is enabled).
# CONNECT_REDIS_PASSWORD sourced from SSM (optional; only required if Redis auth is enabled).
CONNECT_REDIS_PREFIX=${connect_redis_prefix}
%{ if connect_redis_tls_enable == true ~}
CONNECT_REDIS_TLS_ENABLE=true
CONNECT_REDIS_TLS_SKIP_VERIFY=${connect_redis_tls_skip_verify}
%{ if connect_redis_tls_key_file != "" ~}
CONNECT_REDIS_TLS_KEY_FILE=${connect_redis_tls_key_file}
%{ else ~}
# CONNECT_REDIS_TLS_KEY_FILE_NOT_SET=DO_NOT_UNCOMMENT
%{ endif ~}
%{ if connect_redis_tls_cert_file != "" ~}
CONNECT_REDIS_TLS_CERT_FILE=${connect_redis_tls_cert_file}
%{ else ~}
# CONNECT_REDIS_TLS_CERT_FILE_NOT_SET=DO_NOT_UNCOMMENT
%{ endif ~}
%{ else ~}
# CONNECT_REDIS_TLS_NOT_ENABLED=DO_NOT_UNCOMMENT
%{ endif ~}

CONNECT_OIDC_CLIENT_REGISTRATION_TOKEN="ipsemlorem"
CONNECT_CLIENT_NAME=${connect_client_name}
CONNECT_GRANT_TYPE=${connect_grant_type}

%{ if flag_enable_data_studio_ssh == true ~}
CONNECT_SSH_ENABLED=true
CONNECT_SSH_ADDR=:2222
CONNECT_SSH_KEY_PATH=${connect_ssh_key_path}
%{ if connect_ssh_key_value_base64 != "" ~}
CONNECT_SSH_KEY_VALUE_BASE64=${connect_ssh_key_value_base64}
%{ else ~}
# CONNECT_SSH_KEY_VALUE_BASE64_NOT_SET=DO_NOT_UNCOMMENT
%{ endif ~}
CONNECT_SSH_MAX_CONNECTIONS=${connect_ssh_max_connections}
CONNECT_SSH_MAX_CONN_CHANNELS=${connect_ssh_max_conn_channels}
CONNECT_SSH_HANDSHAKE_TIMEOUT=${connect_ssh_handshake_timeout}
%{ else ~}
# CONNECT_SSH_ENABLED=DO_NOT_UNCOMMENT
# CONNECT_SSH_ADDR=DO_NOT_UNCOMMENT
# CONNECT_SSH_KEY_PATH=DO_NOT_UNCOMMENT
# CONNECT_SSH_MAX_CONNECTIONS=DO_NOT_UNCOMMENT
# CONNECT_SSH_MAX_CONN_CHANNELS=DO_NOT_UNCOMMENT
# CONNECT_SSH_HANDSHAKE_TIMEOUT=DO_NOT_UNCOMMENT
%{ endif ~}

CONNECT_LOG_LEVEL=${connect_log_level}

%{ else ~}
# STUDIOS_NOT_ENABLED=DO_NOT_UNCOMMENT
%{ endif ~}


