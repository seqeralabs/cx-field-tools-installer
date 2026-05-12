# Data studios settings
%{ if flag_enable_data_studio == true ~}

# IDENTICAL AS `TOWER_SERVER_URL` in `tower.env`
PLATFORM_URL=${tower_server_url}

CONNECT_HTTP_PORT=9090
CONNECT_TUNNEL_URL=connect-server:7070
CONNECT_PROXY_URL=${tower_connect_server_url}

CONNECT_REDIS_ADDRESS=${tower_redis_url}

# Use the same Redis as Tower but a different logical namespace
CONNECT_REDIS_DB=1

CONNECT_OIDC_CLIENT_REGISTRATION_TOKEN="ipsemlorem"

%{ if flag_enable_data_studio_ssh == true ~}
CONNECT_SSH_ENABLED=true
CONNECT_SSH_ADDR=:2222
CONNECT_SSH_KEY_PATH=${connect_ssh_key_path}
%{ else ~}
# CONNECT_SSH_ENABLED=DO_NOT_UNCOMMENT
# CONNECT_SSH_ADDR=DO_NOT_UNCOMMENT
# CONNECT_SSH_KEY_PATH=DO_NOT_UNCOMMENT
%{ endif ~}

CONNECT_LOG_LEVEL=debug

%{ else ~}
# STUDIOS_NOT_ENABLED=DO_NOT_UNCOMMENT
%{ endif ~}


