version: "3"
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
    image: cr.seqera.io/public/redis:6.0
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
      - groundswell.env
    restart: always
%{ if flag_use_container_db == true ~}
    depends_on:
      - db
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
      - $HOME/tower.yml:/tower.yml
    env_file:
      # Seqera environment variables — see https://docs.seqera.io/platform/latest/enterprise/configuration/overview for details
      - tower.env
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
      - $HOME/tower.yml:/tower.yml
    env_file:
      # Seqera environment variables — see https://docs.seqera.io/platform/latest/enterprise/configuration/overview for details
      - tower.env
    environment:
      # Micronaut environments are required. Do not edit these value
      - MICRONAUT_ENVIRONMENTS=prod,redis,cron${auth_oidc}${auth_github}
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
      - $HOME/tower.yml:/tower.yml
    env_file:
      # Seqera environment variables — see https://docs.seqera.io/platform/latest/enterprise/configuration/overview for details
      - tower.env
    environment:
      # Micronaut environments are required. Do not edit these value
      - MICRONAUT_ENVIRONMENTS=prod,redis,cron${auth_oidc}${auth_github}
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
      - $HOME/tower.yml:/tower.yml
    env_file:
      - tower.env
    environment:
      - MICRONAUT_ENVIRONMENTS=prod,redis,ha${auth_oidc}${auth_github}
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
   image: cr.seqera.io/private/nf-tower-enterprise/data-studio/tower-connect-proxy:${data_studio_container_version}
   platform: linux/amd64
   env_file:
     - data-studios.env
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

 connect-server:
   image: cr.seqera.io/private/nf-tower-enterprise/data-studio/tower-connect-server:${data_studio_container_version}
   platform: linux/amd64
   env_file:
     - data-studios.env
   networks:
     - backend
   ports:
     - 7070:7070
   restart: always
%{ endif ~}

%{ if flag_use_custom_docker_compose_file == true ~}
  # Expectations: 
  #   - docker-compose.yml in `/home/ec2-user/``
  #   - All custom cert files present / generated in `/home/ec2-user/customcerts``
  reverseproxy:
    image: nginx:latest
    container_name: reverseproxy
    networks:
      - frontend
    ports:
      - 80:80
      - 443:443
    volumes:
      - $HOME/target/customcerts/custom_default.conf:/etc/nginx/conf.d/default.conf
      - $HOME/target/customcerts/REPLACE_CUSTOM_CRT:/etc/ssl/certs/REPLACE_CUSTOM_CRT
      - $HOME/target/customcerts/REPLACE_CUSTOM_KEY:/etc/ssl/private/REPLACE_CUSTOM_KEY
    restart: always
%{ endif ~}

networks:
  frontend: {}
  backend: {}