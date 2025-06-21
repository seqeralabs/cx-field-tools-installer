#!/bin/bash

echo "generate_core_data.sh: Current directory is $PWD"

# Generate core data
echo "Generating core file."
touch terraform.tfvars

cat << 'EOF' > terraform.tfvars

aws_account                                     = "128997144437"
aws_region                                      = "us-east-1"
aws_profile                                     = "development"

EOF