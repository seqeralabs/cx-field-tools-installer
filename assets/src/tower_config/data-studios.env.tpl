# Data studios settings
# IDENTICAL AS `TOWER_SERVER_URL` in `tower.env`
PLATFORM_URL=${tower_server_url}

CONNECT_HTTP_PORT=9090
CONNECT_TUNNEL_URL=connect-server:7070

# TOWER_CONNECT_ADDRESS=connect-proxy:9090


CONNECT_REDIS_ADDRESS=${tower_redis_url}

# Must be subdomain of your tower domain (example: https://connect.tower.io).
# Tool hardcodes `connect` as the subdomain.
CONNECT_PROXY_URL=${tower_connect_server_url}

# Should match AS `TOWER_OIDC_REGISTRATION_INITIAL_ACCESS_TOKEN` in `tower.env`>
CONNECT_OIDC_CLIENT_REGISTRATION_TOKEN="ipsemlorem"

TOWER_DATA_STUDIO_CONNECT_URL=${tower_connect_server_url}