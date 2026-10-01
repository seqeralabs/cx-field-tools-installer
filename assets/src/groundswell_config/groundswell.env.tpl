# Tower settings
TOWER_DB_URL=${tower_db_url}
TOWER_DB_USER=${db_tower_user}
TOWER_DB_PASSWORD=${db_tower_password}

# Server settings
SWELL_SERVER_HOST=0.0.0.0
SWELL_SERVER_PORT=8090

# API settings
SWELL_API_TRAIN_TIMEOUT=60
SWELL_API_TRAIN_BATCH_SIZE=1000
SWELL_API_PREDICT_FRACTIONAL_CPUS=false

# Database settings
# NOTE: DO NOT ADD *jdbc* at the front (breaks migration)
SWELL_DB_URL=${swell_db_url}
SWELL_DB_USER=${swell_db_user}
SWELL_DB_PASSWORD=${swell_db_password}
SWELL_DB_DIALECT=mysql

# Database TLS. Groundswell ignores the JDBC options in TOWER_DB_URL, so it has its own settings.
%{ if db_tls_verify_active ~}
# RDS: verify the certificate chain and hostname against the Amazon RDS CA bundle.
TOWER_DB_SSL_CA=/rds-ca/global-bundle.pem
SWELL_DB_SSL_CA=/rds-ca/global-bundle.pem
%{ else ~}
%{ if db_tls_active ~}
# Container DB: encrypted, certificate not verified (self-signed certificate).
TOWER_DB_SSL_NOVERIFY=true
SWELL_DB_SSL_NOVERIFY=true
%{ else ~}
# TOWER_DB_SSL_NOT_ACTIVE=DO_NOT_UNCOMMENT
%{ endif ~}
%{ endif ~}
