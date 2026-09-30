wave:
  debug: false
  server:
    url: "${wave_server_url}"
  tokens:
    cache:
      duration: "36h"
  # Capability toggles (Wave 1.37.0+). All default to true, which is the pre-1.37 behaviour.
  # Set one to false to lock that capability down. Adding `strict` to MICRONAUT_ENVIRONMENTS
  # (docker-compose.yml) turns all of them off at once.
  capabilities:
    # false: every client call must carry a Platform token. Needs tower.endpoint.url (set below).
    anonymous-access: false
    # false: no image augmentation or pass-through pulls; clients must use `wave.freeze = true`.
    ephemeral-token: true
    # false: Wave cannot use registry credentials to pull manifests (public registries only).
    credentials-federation: true
    # false: the /view/** HTML pages (build and inspect views) return 404.
    web-views: true
  metrics:
    enabled: true
  db:
    uri: "${wave_lite_db_url}"
    user: "${wave_lite_db_limited_user}" # "postgres"
    password: "${wave_lite_db_limited_password}" # "mypass"
  # Authenticating egress proxy (Wave 1.38.0+) for outbound HTTP from Wave itself: registry calls and
  # Platform API calls. Unset means direct egress. The HTTPS_PROXY/NO_PROXY environment variables
  # apply the proxy JVM-wide instead, including AWS SDK (ECR/S3) traffic.
  # httpclient:
  #   proxy:
  #     uri: "http://proxy.example.com:3128"   # [http://][user:pass@]host[:port]
  #     username: ""                           # overrides credentials in the URI
  #     password: ""
  #     no-proxy: ".example.com,.amazonaws.com" # hosts reached directly; localhost always bypasses
redis:
  uri: "${wave_lite_redis_url}" # Protocol (redis vs rediss) will come from var. Local container cant support SSL.
  password: "${wave_lite_redis_auth}"
mail:
  from: "${tower_contact_email}" # not required since no build opttion
tower:
  endpoint:
    url: "${tower_server_url}/api"
rate-limit:
  pull:
    anonymous: 250/1h
    authenticated: 2000/1m
  timeout-errors:
    max-rate: 100/1m
license:
  server:
    url: "https://licenses.seqera.io"
micronaut:
  # Dedicated pool for blob streaming, so large layer transfers cannot starve the default event loop.
  executors:
    stream-executor:
      type: FIXED
      number-of-threads: 16
  netty:
    event-loops:
      default:
        num-threads: 64
      stream-pool:
        executor: stream-executor
  http:
    services:
      stream-client:
        read-timeout: "30s"
        read-idle-timeout: "5m"
        event-loop-group: stream-pool
endpoints:
  env:
    enabled: false
  bean:
    enabled: false
  caches:
    enabled: false
  refresh:
    enabled: false
  loggers:
    enabled: false
  info:
    enabled: false
  metrics:
    enabled: true
  health:
    enabled: true
    disk-space:
      enabled: false
    jdbc:
      enabled: false
logger:
  levels:
    # Wave 1.38 logs slow-method traces at DEBUG ("Slow method detected - elapsed time: …").
    io.seqera.util.trace: INFO
    io.seqera.wave.cron.ThreadMonitorCron: INFO
