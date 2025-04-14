# Data studios settings
# IDENTICAL AS `TOWER_SERVER_URL` in `tower.env`
PLATFORM_URL=${tower_server_url}

CONNECT_HTTP_PORT=9090
CONNECT_TUNNEL_URL=connect-server:7070
CONNECT_PROXY_URL=${tower_connect_server_url}

CONNECT_REDIS_ADDRESS=${tower_redis_url}

# Use the same Redis as Tower but a different logical namespace
CONNECT_REDIS_DB=1

CONNECT_OIDC_CLIENT_REGISTRATION_TOKEN="ipsemlorem"

%{ if studio_uses_distroless == true ~}
CONNECT_LOG_LEVEL=debug
%{ else}
CONNECT_SERVER_LOG_LEVEL=debug
%{ endif ~}


