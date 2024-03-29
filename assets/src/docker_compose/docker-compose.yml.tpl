version: "3"
services:

%{~ if flag_use_container_db == true }
  db:
    image: mysql:8.0  #mysql:5.7  #mysql:8.0
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
      - $HOME/.tower/db/mysql:/var/lib/mysql
%{~ if flag_enable_groundswell == true }
      - $HOME/target/groundswell_config/groundswell.sql:/docker-entrypoint-initdb.d/init.sql
%{~ endif ~}

%{~ endif ~}

%{ if flag_use_container_redis == true }
  redis:
    image: cr.seqera.io/public/redis:6.0
    networks:
      - backend
    expose:
      - 6379
    command: --appendonly yes
    restart: always
    volumes:
      - $HOME/.tower/db/redis:/data
%{ endif ~}

%{ if flag_enable_groundswell == true }
  groundswell:
    image: cr.seqera.io/private/nf-tower-enterprise/groundswell:${swell_container_version}
    command: bash -c "pip install cryptography; bin/wait-for-it.sh db:3306 -t 60; bin/migrate-db.sh; bin/serve.sh"
    networks:
      - backend
    ports:
      - 8090:8090
    env_file:
      - groundswell.env
    restart: always
%{~ if flag_use_container_db == true }
    depends_on:
      - db
%{~ endif ~}
%{ endif }

  migrate:
    image: cr.seqera.io/private/nf-tower-enterprise/migrate-db:${docker_version}
    platform: linux/amd64
    #command: -c "echo 'hello'; sleep 30; /migrate-db.sh"
    command: -c "echo 'hello'; cat /tower.yml; /migrate-db.sh"
    networks:
      - backend
    volumes:
      - $HOME/tower.yml:/tower.yml
    env_file:
      - tower.env
    restart: no
%{~ if flag_use_container_db == true }
    depends_on:
      db:
        condition: service_healthy
%{ endif }

  cron:
    image: cr.seqera.io/private/nf-tower-enterprise/backend:${docker_version}
    command: -c "/tower.sh"
    networks:
      - frontend
      - backend
    volumes:
      - $HOME/tower.yml:/tower.yml
    env_file:
      - tower.env
    environment:
      - MICRONAUT_ENVIRONMENTS=prod,redis,cron${auth_oidc}${auth_github}
    restart: always
    depends_on:
      migrate:
        condition: service_completed_successfully

  backend:
    image: cr.seqera.io/private/nf-tower-enterprise/backend:${docker_version}
    command: -c "/wait-for-it.sh db:3306 -t 60; /tower.sh"
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
%{~ if flag_use_container_db == true }
      - db
%{ endif }
%{~ if flag_use_container_redis == true }
      - redis
%{ endif }
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

%{~ if flag_use_custom_docker_compose_file == true }
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
%{ endif }

networks:
  frontend: {}
  backend: {}