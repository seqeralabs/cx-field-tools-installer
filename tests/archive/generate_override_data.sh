#!/bin/bash

echo "generate_override_data.sh: Current directory is $PWD"



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