#!/bin/bash

echo "generate_override_data.sh: Current directory is $PWD"

# Generate override data
## ------------------------------------------------------------------------------------
## New RDS
## ------------------------------------------------------------------------------------
echo "Generating external_db_new"
cat << 'EOF' > test_module_connection_stringsexternal_db_new.auto.tfvars

flag_create_external_db                 = true
flag_use_existing_external_db           = false
flag_use_container_db                   = false
EOF


## ------------------------------------------------------------------------------------
## Existing RDS
## ------------------------------------------------------------------------------------
echo "Generating external_db_existing"
cat << 'EOF' > test_module_connection_strings/external_db_existing.auto.tfvars

flag_create_external_db                 = false
flag_use_existing_external_db           = true
flag_use_container_db                   = false

tower_db_url =                          "mock-existing-tower-db.example.com"
EOF

## ------------------------------------------------------------------------------------
## New Redis
## ------------------------------------------------------------------------------------
echo "Generating external_redis_new"
cat << 'EOF' > test_module_connection_strings/external_redis_new.auto.tfvars

flag_create_external_redis                      = true
flag_use_container_redis                        = false
EOF


## ------------------------------------------------------------------------------------
## Asset URLS - Static
## ------------------------------------------------------------------------------------
echo "Generating assets_urls_static"
cat << 'EOF' > test_module_connection_strings/assets_urls_static.auto.tfvars

tower_server_url                                = "mock-tower-base-static.example.com"
flag_use_container_redis                        = false
EOF


## ------------------------------------------------------------------------------------
## Asset URLS - Secure
## ------------------------------------------------------------------------------------
echo "Generating assets_urls_secure"
cat << 'EOF' > test_module_connection_strings/assets_urls_secure.auto.tfvars

tower_server_url                                = "mock-tower-base.example.com"
flag_use_container_redis                        = false
EOF