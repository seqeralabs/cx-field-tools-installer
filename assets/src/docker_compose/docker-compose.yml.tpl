# `version: "3"` causes problems with the native compose feature in Docker (i.e. not the separate docker-compose extension)
services:

%{ if flag_use_container_db == true ~}
  db:
    image: ${db_container_engine}:${db_container_engine_version} #mysql:8.0  #mysql:5.7
    networks:
      - backend
    expose:
      - 3306
    environment:
      MYSQL_ALLOW_EMPTY_PASSWORD: "yes"
      MYSQL_USER: ${db_tower_user}
      MYSQL_PASSWORD: ${db_tower_password}
      MYSQL_DATABASE: ${db_database_name}
    restart: always
    healthcheck:
      test: ["CMD", "mysqladmin" ,"ping", "-h", "localhost"]
      timeout: 20s
      retries: 10
    volumes:
      # Store the MySQL data in a directory on the host
      - $HOME/.tower/db/mysql:/var/lib/mysql
%{ if flag_enable_groundswell == true ~}
      - $HOME/target/groundswell_config/groundswell.sql:/docker-entrypoint-initdb.d/init.sql
%{ endif ~}
%{ endif ~}


%{ if flag_use_container_redis == true ~}
  redis:
    image: 
%{ if updated_redis_version ~}
      cr.seqera.io/public/redis:7
%{ else ~}
      cr.seqera.io/public/redis:6.0
%{ endif ~}
    networks:
      - backend
    expose:
      - 6379
    command: --appendonly yes
    restart: always
    volumes:
      # Store the Redis data in a directory on the host
      - $HOME/.tower/db/redis:/data
%{ endif ~}


%{ if flag_enable_groundswell == true ~}
  groundswell:
    image: cr.seqera.io/private/nf-tower-enterprise/groundswell:${swell_container_version}
%{ if flag_use_container_db == true ~}
    command: bash -c "pip install cryptography; bin/wait-for-it.sh db:3306 -t 60; bin/migrate-db.sh; bin/serve.sh"
%{ else ~}
    command: bash -c "pip install cryptography; bin/migrate-db.sh; bin/serve.sh"
%{ endif }
    networks:
      - backend
    ports:
      - 8090:8090
    env_file:
      - $HOME/target/groundswell_config/groundswell.env
    restart: always
%{ if flag_use_container_db == true ~}
    depends_on:
      - backend
%{ endif ~}
%{ endif ~}


%{ if flag_new_enough_for_migrate_db == true ~}
  migrate:
    image: cr.seqera.io/private/nf-tower-enterprise/migrate-db:${docker_version}
    platform: linux/amd64
    #command: -c "echo 'hello'; sleep 30; /migrate-db.sh"
    command: -c "/migrate-db.sh"
    networks:
      - backend
    volumes:
      - $HOME/target/tower_config/tower.yml:/tower.yml
    env_file:
      # Seqera environment variables — see https://docs.seqera.io/platform/latest/enterprise/configuration/overview for details
      - $HOME/target/tower_config/tower.env
    restart: no
%{ if flag_use_container_db == true ~}
    depends_on:
      db:
        condition: service_healthy
%{ endif ~}
%{ endif ~}


%{ if flag_new_enough_for_migrate_db == true ~}
  cron:
    image: cr.seqera.io/private/nf-tower-enterprise/backend:${docker_version}
    command: -c "/tower.sh"
    networks:
      - frontend
      - backend
    volumes:
      - $HOME/target/tower_config/tower.yml:/tower.yml
%{ if flag_enable_data_studio == true ~}
      - $HOME/target/tower_config/data-studios-rsa.pem:/data-studios-rsa.pem
%{ endif ~}
    env_file:
      # Seqera environment variables — see https://docs.seqera.io/platform/latest/enterprise/configuration/overview for details
      - $HOME/target/tower_config/tower.env
    environment:
      # Micronaut environments are required. Do not edit these value
      - MICRONAUT_ENVIRONMENTS=prod,redis,cron,${oidc_consolidated}
    restart: always
    depends_on:
      migrate:
        condition: service_completed_successfully
%{ else ~}
  cron:
    image: cr.seqera.io/private/nf-tower-enterprise/backend:${docker_version}
%{ if flag_use_container_db == true ~}
    command: -c "/wait-for-it.sh db:3306 -t 60; /migrate-db.sh; /tower.sh"
%{ else ~}
    command: -c "/migrate-db.sh; /tower.sh"
%{ endif }
    networks:
      - frontend
      - backend
    volumes:
      - $HOME/target/tower_config/tower.yml:/tower.yml
%{ if flag_enable_data_studio == true ~}
      - $HOME/target/tower_config/data-studios-rsa.pem:/data-studios-rsa.pem
%{ endif ~}
    env_file:
      # Seqera environment variables — see https://docs.seqera.io/platform/latest/enterprise/configuration/overview for details
      - $HOME/target/tower_config/tower.env
    environment:
      # Micronaut environments are required. Do not edit these value
      - MICRONAUT_ENVIRONMENTS=prod,redis,cron,${oidc_consolidated}
    restart: always
%{ if flag_use_container_db == true || flag_use_container_redis == true ~}
    depends_on:
%{ if flag_use_container_db == true ~}
      - db
%{ endif ~}
%{ if flag_use_container_redis == true ~}
      - redis
%{ endif ~}
%{ endif ~}
%{ endif ~}


  backend:
    image: cr.seqera.io/private/nf-tower-enterprise/backend:${docker_version}
%{ if flag_use_container_db == true ~}
    command: -c "/wait-for-it.sh db:3306 -t 60; /tower.sh"
%{ else ~}
    command: -c "/tower.sh"
%{ endif }
    networks:
      - frontend
      - backend
    expose:
      - 8080
    volumes:
      - $HOME/target/tower_config/tower.yml:/tower.yml
%{ if flag_enable_data_studio == true ~}
      - $HOME/target/tower_config/data-studios-rsa.pem:/data-studios-rsa.pem
%{ endif ~}
    env_file:
      - $HOME/target/tower_config/tower.env
    environment:
      - MICRONAUT_ENVIRONMENTS=prod,redis,ha,${oidc_consolidated}
    restart: always
    depends_on:
%{ if flag_use_container_db == true ~}
      - db
%{ endif ~}
%{ if flag_use_container_redis == true ~}
      - redis
%{ endif ~}
      - cron


  frontend:
    image: cr.seqera.io/private/nf-tower-enterprise/frontend:${docker_version}
    networks:
      - frontend
    ports:
      - 8000:80
    restart: always
    depends_on:
      - backend

%{ if flag_enable_data_studio == true ~}
  connect-proxy:
    image: cr.seqera.io/private/nf-tower-enterprise/data-studio/connect-proxy:${data_studio_container_version}
    platform: linux/amd64
%{ if studio_uses_distroless == true ~}
    user: 65532:65532
%{ endif ~}
    env_file:
      - $HOME/target/tower_config/data-studios.env
    networks:
      - frontend
      - backend
    ports:
      - 9090:9090
    restart: always
%{ if flag_use_container_redis == true ~}
    depends_on:
      - redis
%{endif ~}
    volumes:
      # DEPENDENCY: July 22/25 -- remove in subsequent release when fixed upstream in Studios.
      - $HOME/.tower/connect:/data


  connect-server:
    image: cr.seqera.io/private/nf-tower-enterprise/data-studio/connect-server:${data_studio_container_version}
    platform: linux/amd64
%{ if studio_uses_distroless == true ~}
    user: 65532:65532
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
%{ endif ~}
    env_file:
      - $HOME/target/tower_config/data-studios.env
    networks:
      - backend
    ports:
      - 7070:7070
    restart: always
%{ endif ~}

%{ if flag_use_private_cacert == true ~}
  # Expectations: 
  #   - docker-compose.yml in `/home/ec2-user/``
  #   - All custom cert files present / generated in `/home/ec2-user/customcerts``
  reverseproxy:
    image: nginx:latest
    container_name: reverseproxy
    networks:
      - frontend
      - backend
    ports:
      - 80:80
      - 443:443
    volumes:
      - $HOME/target/customcerts/custom_default.conf:/etc/nginx/conf.d/default.conf
      - $HOME/target/customcerts/${private_ca_cert}:/etc/ssl/certs/${private_ca_cert}
      - $HOME/target/customcerts/${private_ca_key}:/etc/ssl/private/${private_ca_key}
    restart: always
    depends_on:
%{ if flag_use_wave_lite == true ~}
      - wave-lite-reverse-proxy
%{ endif ~}
%{ if flag_enable_data_studio == true ~}
      - connect-proxy
%{ endif ~}
%{ endif ~}

%{ if flag_use_wave_lite == true ~}
  wave-lite:
    image: hrma017/app:1.20.0-B1   # TODO: swap with real image later.
    # ports:
    #   - 9099:9090
    expose:
      - 9090
    volumes:
      - $HOME/target/wave_lite_config/wave-lite.yml:/work/config.yml
    #env_file:
    #  - wave-lite.env
    environment:
      - MICRONAUT_ENVIRONMENTS=lite,rate-limit,redis,prometheus,postgres
      - WAVE_JVM_OPTS=-Djdk.traceVirtualThreadInThreadDump=full -XX:InitialRAMPercentage=65 -XX:MaxRAMPercentage=65 -XX:+HeapDumpOnOutOfMemoryError -XX:MaxDirectMemorySize=200m -Dio.netty.maxDirectMemory=0 -Djdk.httpclient.keepalive.timeout=10 -Djdk.tracePinnedThreads=short
    networks:
      - frontend
      - backend
    working_dir: /work
    restart: always
    deploy:
      mode: replicated
      replicas: ${num_wave_lite_replicas}

  wave-lite-reverse-proxy:
    image: nginx:latest
    ports:
      - "9099:80"
    volumes:
      - $HOME/target/wave_lite_config/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - wave-lite
    networks:
      - backend
%{ endif ~}

%{ if wave_lite_db_container == true ~}
  wave-db:
    image: postgres:latest
    platform: linux/amd64
    expose:
      - 5432:5432
    volumes:
      - $HOME/.wave/db/postgresql:/var/lib/postgresql/data
      - $HOME/target/wave_lite_config/wave-lite-container-1.sql:/docker-entrypoint-initdb.d/01-init.sql
      - $HOME/target/wave_lite_config/wave-lite-container-2.sql:/docker-entrypoint-initdb.d/02-permissions.sql
    environment:
      - POSTGRES_USER=${wave_lite_db_master_user}
      - POSTGRES_PASSWORD=${wave_lite_db_master_password}
      - POSTGRES_DB=wave
    networks:
      - backend
    restart: always
%{ endif ~}

%{ if wave_lite_redis_container == true ~}
  wave-redis:
    image: cr.seqera.io/public/redis:7.0.10
    platform: linux/amd64
    expose:
      - 6380:6379
    command: ["redis-server", "--requirepass", "${wave_lite_redis_auth}"]
    restart: always
    volumes:
      - $HOME/.wave/db/wave-lite-redis:/data
    networks:
      - backend
%{ endif ~}


networks:
  frontend: {}
  backend: {}
