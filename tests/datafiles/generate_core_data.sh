#!/bin/bash

# NOTE: This script expects to be run from ROOT/tests/datafiles/
# Ensure we are in that folder.
echo $(dirname $0)
cd $(dirname $0)

echo "generate_core_data.sh: Current directory is $PWD"

# Removing existing files
echo "Removing existing files."
rm -f *.tfvars
rm -f secrets/ssm_sensitive_values_*_testing.json

# Generate core terraform.tfvars file from template
echo "Generating base terraform.tfvars file from templates/TEMPLATE_terraform.tfvars"
cp ../../templates/TEMPLATE_terraform.tfvars terraform.tfvars


# Create a `base-overrides.auto.tfvars` file. This replaces the REPLACE_ME values in the base file,
# but will still lose out lexically to the override.auto.tfvars file created in each pytest test case.
# See: https://developer.hashicorp.com/terraform/language/values/variables#variable-definition-precedence
# NOTE: Due to how terraform orders layering, if this name is changed to something like `terraform.auto.tfvars`
# then the test-level override needs to be lexically after it.
cat << 'EOF' > base-overrides.auto.tfvars
## ------------------------------------------------------------------------------------
## Testing
## ------------------------------------------------------------------------------------
# Use mock values to emulate to-be-created resources.
use_mocks = true


## ------------------------------------------------------------------------------------
## Testing - Core Override
## ------------------------------------------------------------------------------------
app_name = "tower-testing"

secrets_bootstrap_tower       = "/seqera/sensitive-values/tower-testing/tower"
secrets_bootstrap_seqerakit   = "/seqera/sensitive-values/tower-testing/seqerakit"
secrets_bootstrap_groundswell = "/seqera/sensitive-values/tower-testing/groundswell"
secrets_bootstrap_wave_lite   = "/seqera/sensitive-values/tower-testing/wave-lite"

aws_account = "128997144437"
aws_region  = "us-east-1"
aws_profile = "development"

tower_container_version                 = "v25.3.0"


## ------------------------------------------------------------------------------------
## Flags - Custom Naming
## ------------------------------------------------------------------------------------
flag_use_custom_resource_naming_prefix = true
custom_resource_naming_prefix          = "tfpytest"


## ------------------------------------------------------------------------------------
## Flags - Infrastructure
## ------------------------------------------------------------------------------------
flag_create_new_vpc                     = false
flag_use_existing_vpc                   = true


## ------------------------------------------------------------------------------------
## Wave Service
## ------------------------------------------------------------------------------------
flag_use_wave          = false
flag_use_wave_lite     = true

num_wave_lite_replicas = 2
wave_server_url        = "wave.autodc.dev-seqera.net"


## ------------------------------------------------------------------------------------
## Flags - DNS
## ------------------------------------------------------------------------------------
new_route53_private_zone_name = "dev-seqera-private-sage.net"
existing_route53_public_zone_name  = "dev-seqera.net"


## ------------------------------------------------------------------------------------
## Custom Private CA
## ------------------------------------------------------------------------------------
# IF creating a new Private CA, stash generated cert to accessible S3 bucket.
# Include s3:// and omit trailing slash
private_cacert_bucket_prefix = "s3://nf-nvirginia/seqerakittesting"


## ------------------------------------------------------------------------------------
## VPC (Existing)
## - If using existing IP, ensure ec2 subnet has public IP via auto-assignment (current as of Nov 16/23).
## ------------------------------------------------------------------------------------
vpc_existing_id            = "vpc-0fd280748c05b375b"
vpc_existing_ec2_subnets   = ["10.0.3.0/24"]
vpc_existing_batch_subnets = ["10.0.3.0/24"]
vpc_existing_db_subnets    = ["10.0.4.0/24"]
vpc_existing_redis_subnets = ["10.0.4.0/24"]

# Must be >= 2, in different AZs. Ensure EC2 subnet included.
vpc_existing_alb_subnets = ["10.0.1.0/24", "10.0.2.0/24"]


## ------------------------------------------------------------------------------------
## Groundswell
## ------------------------------------------------------------------------------------
flag_enable_groundswell = true


## ------------------------------------------------------------------------------------
## Data Studio - Feature Gated (24.1.0+)
## ------------------------------------------------------------------------------------
flag_enable_data_studio = true


## ------------------------------------------------------------------------------------
## Database (Generic)
## Values that apply to both the containerized and RDS DBs
## ------------------------------------------------------------------------------------
db_database_name = "tower"

## ------------------------------------------------------------------------------------
## Database (External)
## Specify the details of the external database to create or reuse
## ------------------------------------------------------------------------------------
db_instance_class    = "db.t4g.medium"
db_deletion_protection = false
skip_final_snapshot    = true

wave_lite_db_instance_class      = "db.t4g.micro"
wave_lite_db_deletion_protection = false
wave_lite_skip_final_snapshot    = true


## ------------------------------------------------------------------------------------
## Elasticache (External)
## Specify the details of the external database to create or reuse
## ------------------------------------------------------------------------------------


## ------------------------------------------------------------------------------------
## IAM
## - Note this is an INSTANCE ROLE ARN, not normal Role.
## ------------------------------------------------------------------------------------
# iam_prexisting_instance_role_arn = "TBD"


## ------------------------------------------------------------------------------------
## EC2 Host
## ------------------------------------------------------------------------------------
ec2_host_instance_type = "m4.large"

flag_encrypt_ebs     = false
flag_use_kms_key     = false
ec2_ebs_kms_key      = "arn:aws:kms:us-east-1:128997144437:key/c53459b5-44ee-4351-a2d1-64fd2fce17d0"
ec2_root_volume_size = 8

ec2_require_imds_token = true

ec2_update_ami_if_available = false


## ------------------------------------------------------------------------------------
## ALB
## ------------------------------------------------------------------------------------
# *.autodc.dev-seqera.net
alb_certificate_arn = "arn:aws:acm:us-east-1:128997144437:certificate/58c948c6-e65f-4bbc-8cd6-53391fa1d3cc"


## ------------------------------------------------------------------------------------
## TOWER CONFIGURATION
## ------------------------------------------------------------------------------------
tower_server_url  = "autodc.dev-seqera.net"

# This must be a verified identity / domain.
tower_contact_email    = "graham.wright@seqera.io" #"daniel.wood@seqera.io"
tower_enable_platforms = "awsbatch-platform,slurm-platform"


tower_smtp_host = "email-smtp.us-east-1.amazonaws.com"
tower_smtp_port = "587"

tower_root_users          = "graham.wright@seqera.io,gwright99@hotmail.com"
tower_email_trusted_orgs  = "*@abc.com, *@def.com"
tower_email_trusted_users = "123@abc.com, 456@def.com"

tower_enable_openapi = true

tower_enable_pipeline_versioning        = true
pipeline_versioning_eligible_workspaces = ""


## ------------------------------------------------------------------------------------
## TOWER CONFIGURATION - OIDC
## ------------------------------------------------------------------------------------
flag_oidc_use_generic = true
flag_oidc_use_google  = true
flag_oidc_use_github  = true

flag_disable_email_login = false

# ------------------------------------------------------------------------------------
# TOWER CONFIGURATION - Credentials
# ------------------------------------------------------------------------------------

flag_allow_aws_instance_credentials = true

## ------------------------------------------------------------------------------------
## Seqerakit
# graham.wright@seqera.io
## ------------------------------------------------------------------------------------
flag_run_seqerakit = false

seqerakit_org_name     = "SampleOrg3"
seqerakit_org_fullname = "SampleOrgFullName"
seqerakit_org_url      = "https://www.example.com"

seqerakit_team_name    = "SampleTeam"
seqerakit_team_members = "daniel.wood@seqera.io,graham.wright+001@seqera.io"

seqerakit_workspace_name     = "SampleWorkspace"
seqerakit_workspace_fullname = "SampleWorkspaceFullName"

seqerakit_compute_env_name   = "MyComputeEnvironment"
seqerakit_compute_env_region = "us-east-1"

seqerakit_root_bucket = "s3://nf-nvirginia"
seqerakit_workdir     = "s3://nf-nvirginia/seqerakittesting"
seqerakit_outdir      = "s3://nf-nfvirginia/sk_outdir"

seqerakit_aws_use_fusion_v2 = false
seqerakit_aws_use_forge     = false
seqerakit_aws_use_batch     = true

seqerakit_aws_fusion_instances = "c6id,r6id,m6id"
seqerakit_aws_normal_instances = "optimal"

seqerakit_aws_manual_head_queue    = "TowerForge-4rp223pYWe8kQ5LWtcYVz6-head"
seqerakit_aws_manual_compute_queue = "TowerForge-4rp223pYWe8kQ5LWtcYVz6-work"


## ------------------------------------------------------------------------------------
## Seqerakit - Credentials
## ------------------------------------------------------------------------------------
seqerakit_flag_credential_create_aws        = true
seqerakit_flag_credential_create_github     = true
seqerakit_flag_credential_create_docker     = false
seqerakit_flag_credential_create_codecommit = false

seqerakit_flag_credential_use_aws_role           = true
seqerakit_flag_credential_use_codecommit_baseurl = false
EOF


# # Move override file to PROJ_ROOT
# echo "Relocating terraform test files to PROJ_ROOT."
# cp ../../templates/TEMPLATE_terraform.tfvars terraform.tfvars


## ------------------------------------------------------------------------------------
## CREATE TESTING SECRETS / WRITE TO SSM
## ------------------------------------------------------------------------------------
echo "Creating omnibus testing secrets."
python3 generate_testing_secrets.py

# Function to create or update SSM parameter with hash comparison
update_ssm_parameter() {
    local param_name="$1"
    local local_file="$2"
    
    echo "Processing parameter: $param_name"
    
    # Try to get current value (single call)
    current_value=$(aws ssm get-parameter --name "$param_name" --with-decryption --query 'Parameter.Value' --output text 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        echo "Parameter $param_name exists, checking if update is needed..."
        
        # Hash the current value
        current_hash=$(echo -n "$current_value" | sha256sum | cut -d' ' -f1)
        
        # Get local file content and hash it
        local_content=$(cat "$local_file")
        local_hash=$(echo -n "$local_content" | sha256sum | cut -d' ' -f1)
        
        # Compare hashes
        if [ "$current_hash" = "$local_hash" ]; then
            echo "Parameter $param_name is up to date (hash match)"
            return 0
        else
            echo "Parameter $param_name needs update (hash mismatch)"
        fi
    else
        echo "Parameter $param_name does not exist, creating..."
    fi
    
    # Create or update parameter
    aws ssm put-parameter \
        --name "$param_name" \
        --value "$(cat "$local_file")" \
        --type "SecureString" \
        --overwrite
        
    echo "Parameter $param_name updated successfully"
}

# Update all SSM parameters
# if [ "$CX_SKIP_SSM" != "true" ]; then
#     update_ssm_parameter "/seqera/sensitive-values/tower-testing/tower" "ssm_sensitive_values_tower_testing.json"
#     update_ssm_parameter "/seqera/sensitive-values/tower-testing/groundswell" "ssm_sensitive_values_groundswell_testing.json"
#     update_ssm_parameter "/seqera/sensitive-values/tower-testing/seqerakit" "ssm_sensitive_values_seqerakit_testing.json"
#     update_ssm_parameter "/seqera/sensitive-values/tower-testing/wave-lite" "ssm_sensitive_values_wave_lite_testing.json"
# else
#     echo "Skipping SSM parameter updates (CX_SKIP_SSM=true)"
# fi

# Skipping SSM check since this handles local testing.
echo "Skipping SSM parameter updates (CX_SKIP_SSM=true)"


# Delete test log file
echo '{"message": "Cleansing content for new test loop."}' > ../logs/pytest_structured.log || true


## ------------------------------------------------------------------------------------
## Create test-specific outputs (e.g. tf locals needed for assertions)
## ------------------------------------------------------------------------------------
cat << 'EOF' > 012_testing_outputs.tf
## ------------------------------------------------------------------------------------
## Write local values to output for testing purposes
## Keep name of local the same; prefix with 'local_' for easy conversion
## ------------------------------------------------------------------------------------
output local_wave_enabled {
    value = local.wave_enabled
} 
EOF
