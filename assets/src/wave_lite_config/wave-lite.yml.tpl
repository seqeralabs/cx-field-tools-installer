wave:
  debug: false
  server:
    url: "${wave_server_url}"
  tokens:
    cache:
      duration: "36h"
  metrics:
    enabled: true
  db:
    uri : "jdbc:postgresql://${wave_lite_db_url}/wave"
    user : "${wave_lite_db_limited_user}"  # "postgres"
    password : "${wave_lite_db_limited_password}"  # "mypass"
redis:
  uri: "${wave_lite_redis_url}"    # Protocol (redis vs rediss) will come from var. Local container cant support SSL.
  password: "${wave_lite_redis_auth}"
mail:
  from: "${tower_contact_email}"    # not required since no build opttion
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
    url: 'https://licenses.seqera.io'
micronaut:
  netty:
    event-loops:
      default:
        num-threads: 64
  http:
    services:
      stream-client:
        read-timeout: '30s'
        read-idle-timeout: '5m'
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
