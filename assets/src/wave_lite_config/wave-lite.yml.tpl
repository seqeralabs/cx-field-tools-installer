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
    user : "postgres"
    password : "postgres"
redis:
  uri: "redis://${wave_lite_redis_url}"    # rediss://
  # password: "abc" #AUTH equivalent  # figure out what to do with container
mail:
  from: "${tower_contact_email}"    # not required since no build opttion
tower:
  endpoint:
    url: "${tower_server_url}/api"
rate-limit:
  build:
    anonymous: 25/1d
    authenticated: 100/1h
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
