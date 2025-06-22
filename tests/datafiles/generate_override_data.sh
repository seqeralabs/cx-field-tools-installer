#!/bin/bash

echo "generate_override_data.sh: Current directory is $PWD"

# Generate override data
## ------------------------------------------------------------------------------------
## New RDS
## ------------------------------------------------------------------------------------
echo "Generating external_db_new"
cat << 'EOF' > external_db_new.auto.tfvars

flag_create_external_db                 = true
flag_use_existing_external_db           = false
flag_use_container_db                   = false
EOF


## ------------------------------------------------------------------------------------
## Existing RDS
## ------------------------------------------------------------------------------------
echo "Generating external_db_existing"
cat << 'EOF' > external_db_existing.auto.tfvars

flag_create_external_db                 = false
flag_use_existing_external_db           = true
flag_use_container_db                   = false

tower_db_url =                          "mock-existing-tower-db.example.com"
EOF

## ------------------------------------------------------------------------------------
## New Redis
## ------------------------------------------------------------------------------------
echo "Generating external_redis_new"
cat << 'EOF' > external_redis_new.auto.tfvars

flag_create_external_redis                      = true
flag_use_container_redis                        = false
EOF