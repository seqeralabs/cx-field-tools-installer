# https://stackoverflow.com/questions/45717835/docker-proxy-pass-to-another-container-nginx-host-not-found-in-upstream
upstream frontend {
    server frontend:80;
}

server {
    listen       80;
    listen  [::]:80;

    server_name  REPLACE_TOWER_URL;

    location / {
        proxy_pass http://frontend;
    }

    error_page   500 502 503 504  /50x.html;
    location = /50x.html {
        root   /usr/share/nginx/html;
    }
}

server {
    listen 443 ssl;

    server_name REPLACE_TOWER_URL;

    ssl_certificate /etc/ssl/certs/PLACEHOLDER_CRT;
    ssl_certificate_key /etc/ssl/private/PLACEHOLDER_KEY;

    location / {
        proxy_pass http://frontend;
        proxy_set_header        Host $host;
        proxy_set_header        X-Real-IP $remote_addr;
        proxy_set_header        X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header        X-Forwarded-Proto $scheme;

        # Needed to support live status update of workflows in Seqera Platform
        proxy_pass_request_headers on;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
    }
}

%{ if flag_enable_data_studio == true ~}
server {
    listen 443 ssl;

    server_name ${tower_connect_server_url};

    ssl_certificate /etc/ssl/certs/PLACEHOLDER_CRT;
    ssl_certificate_key /etc/ssl/private/PLACEHOLDER_KEY;

    location / {
        proxy_pass http://connect-proxy:9090;
        proxy_set_header        Host $host;
        proxy_set_header        X-Real-IP $remote_addr;
        proxy_set_header        X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header        X-Forwarded-Proto $scheme;

        # Needed to support live status update of workflows in Seqera Platform
        proxy_pass_request_headers on;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
    }
}
%{ endif ~}

%{ if flag_use_wave_lite == true ~}
server {
    listen 443 ssl;

    server_name ${tower_wave_url};

    ssl_certificate /etc/ssl/certs/PLACEHOLDER_CRT;
    ssl_certificate_key /etc/ssl/private/PLACEHOLDER_KEY;

    location / {
        proxy_pass http://wave-lite-reverse-proxy:9099;
        proxy_set_header        Host $host;
        proxy_set_header        X-Real-IP $remote_addr;
        proxy_set_header        X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header        X-Forwarded-Proto $scheme;

        # Needed to support live status update of workflows in Seqera Platform
        proxy_pass_request_headers on;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
    }
}
%{ endif ~}
