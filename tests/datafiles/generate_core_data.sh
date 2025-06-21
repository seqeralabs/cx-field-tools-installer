#!/bin/bash

echo "generate_core_data.sh: Current directory is $PWD"

# Generate core data
echo "Generating core file."
touch terraform.tfvars

cat << 'EOF' > terraform.tfvars
/*
## ------------------------------------------------------------------------------------
## Testing
## ------------------------------------------------------------------------------------
Use mock values to emulate to-be-created resources.
*/
use_mocks = true

## ------------------------------------------------------------------------------------
## Mandatory Bootstrap Values
## ------------------------------------------------------------------------------------
app_name                                = "tower-dev"  # NOTE: must use hyphen (not underscore) or breaks ALB name.

# These values must match the parameters you have created in the AWS SSM Parameter Store
secrets_bootstrap_tower                 = "/seqera/sensitive-values/tower-dev/tower"
secrets_bootstrap_seqerakit             = "/seqera/sensitive-values/tower-dev/seqerakit"
secrets_bootstrap_groundswell           = "/seqera/sensitive-values/tower-dev/groundswell"
secrets_bootstrap_wave_lite             = "/seqera/sensitive-values/tower-dev/wave-lite"
# secrets_bootstrap_tower                 = "/seqera/sensitive-values/fake/tower"
# secrets_bootstrap_seqerakit             = "/seqera/sensitive-values/fake/seqerakit"
# secrets_bootstrap_groundswell           = "/seqera/sensitive-values/fake/groundswell"


# # AWS Proper
aws_account                                     = "128997144437"
aws_region                                      = "us-east-1"
aws_profile                                     = "development" # "management"

# Localstack -- using us-east-1 seems to point back to Seqera dev
# aws_account                             = "000000000000"
# aws_region                              = "us-east-1"
# aws_profile                             = "localstack"


tower_container_version                         = "v25.1.1"  #"v24.2.5" # "v25.1.1" #"v25.1.1"  #"v25.1.1"


/*
## ------------------------------------------------------------------------------------
## SSM
## ------------------------------------------------------------------------------------
Activate this setting over allow n+1 deployments to overwrite your SSM keys.
(note: Terraform will show a deprecation warning -- there is no better option than this
 however, so we continue to use this option for now).
*/
flag_overwrite_ssm_keys                         = true


/*
## ------------------------------------------------------------------------------------
## Tags -- Default
## ------------------------------------------------------------------------------------
Default tags to put on every generated resource.
*/
default_tags  = {
      Terraform                                 = "true"
      Environment                               = "dev"
      CreatedBy                                 = "Graham Wright"
}


## ------------------------------------------------------------------------------------
## Flags - Custom Naming
## ------------------------------------------------------------------------------------
flag_use_custom_resource_naming_prefix          = false
custom_resource_naming_prefix                   = "tf-graham-prefix"


## ------------------------------------------------------------------------------------
## Flags - Infrastructure
## ------------------------------------------------------------------------------------
# Only one of these can true.
flag_create_new_vpc                             = true
flag_use_existing_vpc                           = false

# Only one of these can be true.
flag_create_external_db                         = true
flag_use_existing_external_db                   = false
flag_use_container_db                           = false

# Only one of these can be true.
flag_create_external_redis                      = false
flag_use_container_redis                        = true

# Only one of these can be true.
flag_create_load_balancer                       = true
flag_generate_private_cacert                    = false
flag_use_existing_private_cacert                = false
flag_do_not_use_https                           = false

# Only one of these can true.
flag_use_aws_ses_iam_integration                = true
flag_use_existing_smtp                          = false


## ------------------------------------------------------------------------------------
## Flags - Networking
## ------------------------------------------------------------------------------------
flag_make_instance_public                       = false
flag_make_instance_private                      = false
flag_make_instance_private_behind_public_alb    = true
flag_private_tower_without_eice                 = false

# Manage how to talk to VM for config file transfer & DNS
flag_vm_copy_files_to_instance                  = true

# If set to true, will include the custom block of the assets/src/docker_compose/docker-compose.yml.tpl file.
flag_use_custom_docker_compose_file             = false


## ------------------------------------------------------------------------------------
## Wave Service
## ------------------------------------------------------------------------------------
# Enable Tower to connect to the Wave service hosted by Seqera
flag_use_wave                             = false
flag_use_wave_lite                        = true
num_wave_lite_replicas                    = 3
wave_server_url                           = "https://wave.stage-seqera.io"
wave_lite_server_url                      = "https://wave.autodc.dev-seqera.net"


## ------------------------------------------------------------------------------------
## Flags - DNS
## ------------------------------------------------------------------------------------
# Only one can be true
flag_create_route53_private_zone        = false
flag_use_existing_route53_public_zone   = true
flag_use_existing_route53_private_zone  = false
flag_create_hosts_file_entry            = false

# Populate this field if creating a new private hosted zone
new_route53_private_zone_name           = "dev-seqera-private-sage.net"

# Only populate if flag set above to use existing hosted zone.
existing_route53_public_zone_name       = "dev-seqera.net"
existing_route53_private_zone_name      = "REPLACE_ME_IF_NEEDED"


## ------------------------------------------------------------------------------------
## Custom Private CA
## ------------------------------------------------------------------------------------
# IF creating a new Private CA, stash generated cert to accessible S3 bucket.
# Include s3:// and omit trailing slash
bucket_prefix_for_new_private_ca_cert   = "s3://nf-nvirginia/seqerakittesting"

# If using existing key/cert supplied via client (not on ALB) specify here so they are properly
# mounted into the custom Docker-Compose file. 
# Make sure these files are stored in `assets/customcerts/`

existing_ca_cert_file                   = "REPLACE_ME_IF_NEEDED.crt"
existing_ca_key_file                    = "REPLACE_ME_IF_NEEDED.key"


## ------------------------------------------------------------------------------------
## VPC (New)
## - Ensure `vpc_new_enable_nat_gateway` setting on if private subnets are non-zero.
## ------------------------------------------------------------------------------------
vpc_new_cidr_range                      = "10.0.0.0/16"
vpc_new_azs                             = ["us-east-1a", "us-east-1b", "us-east-1c"]

vpc_new_public_subnets                  = [ "10.0.1.0/24", "10.0.2.0/24" ]
vpc_new_private_subnets                 = [ "10.0.3.0/24", "10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24" ]

# Ensure these subnet ranges align to what's created above. 
vpc_new_ec2_subnets                     = [ "10.0.3.0/24" ]  # Can only 1 for EICE to work.
vpc_new_batch_subnets                   = [ "10.0.4.0/24" ]
vpc_new_db_subnets                      = [ "10.0.3.0/24", "10.0.5.0/24" ]
vpc_new_redis_subnets                   = [ "10.0.5.0/24" ]

# Must be >= 2, in different AZs. Ensure ALL provided CIDRS are PUBLIC.
vpc_new_alb_subnets                     = [ "10.0.1.0/24", "10.0.2.0/24" ]

enable_vpc_flow_logs                    = false


## ------------------------------------------------------------------------------------
## VPC (Existing)
## - If using existing IP, ensure ec2 subnet has public IP via auto-assignment (current as of Nov 16/23).
## ------------------------------------------------------------------------------------
vpc_existing_id                         = "vpc-0422bbbd952274e74"
vpc_existing_ec2_subnets                = [ "10.2.1.0/24" ]
vpc_existing_batch_subnets              = [ "10.2.1.0/24" ]
vpc_existing_db_subnets                 = [ "10.2.1.0/24" ]
vpc_existing_redis_subnets              = [ "10.2.1.0/24" ]

# Must be >= 2, in different AZs. Ensure EC2 subnet included.
# vpc_existing_alb_subnets                = [ "10.0.1.0/24", "10.0.2.0/24" ]
vpc_existing_alb_subnets                = [ "10.2.1.0/24", "10.2.3.0/24" ]
# Subnet names needed to be used for fixes to bugs in v1.2.1
# vpc_existing_alb_subnets = ["subnet-00fad764627895f33", "subnet-0f18039d5ffcf6cd3"]


## ------------------------------------------------------------------------------------
## VPC Endpoints
# https://docs.aws.amazon.com/vpc/latest/privatelink/aws-services-privatelink-support.html

# SES: email-smtp,  !! GOTCHA: https://docs.aws.amazon.com/ses/latest/dg/send-email-set-up-vpc-endpoints.html
# RDS: rds
# Cloudwatch: monitoring,logs
# Batch: batch
# ECR: ecr.dkr, ecr.api
# CodeCommit: codecommit,git-codecommit
# SecretsManager: secretsmanager
# SSM: ssm,ssmmessages
# ECS: ecs-agent,ecs-telemetry,ecs
# EC2: ec2, autoscaling
# ELB: elasticloadbalancing
# Elasticache: elasticache
## ------------------------------------------------------------------------------------
# Comment out for faster testing
# vpc_gateway_endpoints_all                 = ["s3"]

# vpc_interface_endpoints_tower             = [
#       "email-smtp","rds","monitoring","logs","batch","ecr.dkr","ecr.api","codecommit","git-codecommit",
#       "secretsmanager","ssm","ssmmessages","ecs","ecs-agent","ecs-telemetry","ec2", "autoscaling",
#       "elasticloadbalancing", "elasticache" ]
# vpc_interface_endpoints_batch             = ["codecommit","git-codecommit"]

vpc_gateway_endpoints_all                 = []

vpc_interface_endpoints_tower             = []
vpc_interface_endpoints_batch             = []



## ------------------------------------------------------------------------------------
## Security Group - Transaction Sources
## ------------------------------------------------------------------------------------
sg_ingress_cidrs                          = ["0.0.0.0/0"] # ["10.2.0.0/16"]
sg_ssh_cidrs                              = ["0.0.0.0/0"]

# See following link for port definitions:
# https://github.com/terraform-aws-modules/terraform-aws-security-group/blob/master/rules.tf
sg_egress_eice                            = ["all-all"]
sg_egress_tower_ec2                       = ["all-all"]
sg_egress_tower_alb                       = ["all-all"]
sg_egress_batch_ec2                       = ["all-all"]
sg_egress_interface_endpoint              = ["all-all"]


/*
## ------------------------------------------------------------------------------------
## Groundswell
## ------------------------------------------------------------------------------------
Enable to allow pipeline optimization.
*/

flag_enable_groundswell                 = false

swell_container_version                 = "0.4.0"
swell_database_name                     = "swell"
## swell_db_user                        = "DO_NOT_UNCOMMENT_ME"
## swell_db_password                    = "DO_NOT_UNCOMMENT_ME"


/*
## ------------------------------------------------------------------------------------
## Data Explorer - Feature Gated (23.4.3+)
## ------------------------------------------------------------------------------------
Enable to allow Data Explorer functionality.
*/
flag_data_explorer_enabled                = true
data_explorer_disabled_workspaces         = ""


/*
## ------------------------------------------------------------------------------------
## Data Studio - Feature Gated (24.1.0+)
## ------------------------------------------------------------------------------------
Enable to allow Data Studio functionality. Note, this requires several modifications to your instance.
Please check Release Notes and documentation to ensure this its your regulatory compliance needs.
*/
flag_enable_data_studio                   = false
data_studio_container_version             = "0.8.0" # "0.7.8" # "0.7.7" # "0.7.8-snapshot"

flag_limit_data_studio_to_some_workspaces = false
data_studio_eligible_workspaces           = ""

# https://public.cr.seqera.io/
data_studio_options = {
      vscode1_83_0-0_8_0 = {
            qualifier = "VSCODE-1-83-0-0-8-0"
            icon = "vscode"
            tool = "vscode"
            status = "recommended"
            container = "public.cr.seqera.io/platform/data-studio-vscode:1.83.0-0.8.0"
      },
      jupyter4_2_5-0_8_0 = {
            qualifier = "JUPYTER-4-2-5-0-8-0"
            icon = "jupyter"
            tool = "jupyter"
            status = "recommended"
            container = "public.cr.seqera.io/platform/data-studio-jupyter:4.2.5-0.8.0"
      },
      rstudio4_4_1-0_8_0 = {
            qualifier = "RSTUDIO-4-4-1-0-8-0"
            icon = "rstudio"
            tool = "rstudio"
            status = "recommended"
            container = "public.cr.seqera.io/platform/data-studio-rstudio:4.4.1-0.8.0"
      },
      xpra6_0_r0-0_8_0 = {
            qualifier = "XPRA-6-0-R0-0-8-0"
            icon = "xpra"
            tool = "xpra"
            status = "recommended"
            container = "public.cr.seqera.io/platform/data-studio-xpra:6.0-r0-1-0.8.0"
      }
}


## ------------------------------------------------------------------------------------
## Database (Generic)
## Values that apply to both the containerized and RDS DBs
## ------------------------------------------------------------------------------------
## db_root_user                         = "DO_NOT_UNCOMMENT_ME"
## db_root_password                     = "DO_NOT_UNCOMMENT_ME"
## tower_db_user                        = "DO_NOT_UNCOMMENT_ME"
## tower_db_password                    = "DO_NOT_UNCOMMENT_ME"

db_database_name                        = "tower"


## ------------------------------------------------------------------------------------
## Database (Container)
## Specify the details of the external database to create (if applicable)
## ------------------------------------------------------------------------------------
db_container_engine                               = "mysql"
db_container_engine_version                       = "8.0" # "8.0" #"8.0"


## ------------------------------------------------------------------------------------
## Database (External)
## Specify the details of the external database to create or reuse
## ------------------------------------------------------------------------------------
db_engine                               = "mysql"
db_engine_version                       = "8.0.42" # "8.0.37"   #9.0.42"
db_param_group                          = "mysql8.0"
# with module.rds[0].module.db_option_group.aws_db_option_group.this[0],
# Error: creating DB Option Group: InvalidParameterValue: Only the major engine version may be specified (e.g. 8.0), not the full engine version.
db_instance_class                       = "db.t4g.medium"   #"db.m5.large"  #Wont allow PerfInsight with .micro!
db_allocated_storage                    = 10

db_deletion_protection                  = false
skip_final_snapshot                     = true

db_backup_retention_period              = 7
db_enable_storage_encrypted             = true


wave_lite_db_engine                               = "postgres"
wave_lite_db_engine_version                       = "17.5"
wave_lite_db_param_group                          = "postgres17"
wave_lite_db_instance_class                       = "db.t4g.micro"   #"db.m5.large"
wave_lite_db_allocated_storage                    = 10

# Dont expect these need to change
wave_lite_db_deletion_protection                  = false
wave_lite_skip_final_snapshot                     = true
wave_lite_db_backup_retention_period              = 7
wave_lite_db_enable_storage_encrypted             = true


## ------------------------------------------------------------------------------------
## Elasticache (External)
## Specify the details of the external database to create or reuse
## ------------------------------------------------------------------------------------

# TODO - Add Seqera Platform core config in some release after Wave-Lite

wave_lite_elasticache = {
  apply_immediately = true

  engine         = "redis"
  engine_version = "7.1"
  node_type      = "cache.t4g.micro"
  port           = 6379

  security_group_ids = [] # Leave blank to use TF-generated SG.
  subnet_ids         = [] # Leave blank to use all private subnets.

  unclustered = {
    num_cache_nodes = 1
  }

  clustered = {
    multi_az_enabled           = false
    automatic_failover_enabled = false
    num_node_groups            = null
    replicas_per_node_group    = null
    parameter_group_name       = "default.redis7"
  }

  encryption = {
    at_rest_encryption_enabled = true
    transit_encryption_enabled = true
    #kms_key_id missing
  }
}


## ------------------------------------------------------------------------------------
## IAM
## - Note this is an INSTANCE ROLE ARN, not normal Role.
## ------------------------------------------------------------------------------------
flag_iam_use_prexisting_role_arn        = false
iam_prexisting_instance_role_arn        = "TowerForge-1er5NwO4MfPfD7A2R58dhe-InstanceRole"


## ------------------------------------------------------------------------------------
## EC2 Host
## ------------------------------------------------------------------------------------
ec2_host_instance_type                  = "m4.large"

flag_encrypt_ebs                        = false
flag_use_kms_key                        = false
ec2_ebs_kms_key                         = "arn:aws:kms:us-east-1:128997144437:key/c53459b5-44ee-4351-a2d1-64fd2fce17d0"
ec2_root_volume_size                    = 8

ec2_require_imds_token                  = true

ec2_update_ami_if_available             = false

## ------------------------------------------------------------------------------------
## ALB
## ------------------------------------------------------------------------------------
# *.autodc.dev-seqera.net
alb_certificate_arn = "arn:aws:acm:us-east-1:128997144437:certificate/58c948c6-e65f-4bbc-8cd6-53391fa1d3cc"

## ------------------------------------------------------------------------------------
## TOWER CONFIGURATION
## ------------------------------------------------------------------------------------
# Example: `autodc.dev-seqera.net` (not `http(s)`).
# If using a private hosted zone, please ensure the right-most part of the URL matches the value given above.
#tower_server_url                        = "autodc.dev-seqera.net"  # "autodc.dev-seqera-private.net" # "autodc.dev-seqera.net"
tower_server_url                        = "autodc.dev-seqera.net"
tower_server_port                       = "8000"

# This must be a verified identity / domain.
tower_contact_email                     = "graham.wright@seqera.io" #"daniel.wood@seqera.io"
tower_enable_platforms                  = "awsbatch-platform,azbatch-platform,googlebatch-platform,k8s-platform,slurm-platform,eks-platform"

## tower_jwt_secret                      = "DO_NOT_UNCOMMENT_ME"
## tower_crypto_secretkey                = "DO_NOT_UNCOMMENT_ME"
## tower_license                         = "DO_NOT_UNCOMMENT_ME"

# Do not include 'jdbc:mysql://`. Include databse is using existing external db (i.e. `/tower`). 
tower_db_url                            = "db:3306" #:3306"  #"db:3306"
tower_db_driver                         = "org.mariadb.jdbc.Driver"
tower_db_dialect                        = "io.seqera.util.MySQL55DialectCollateBin"
tower_db_min_pool_size                  = 5
tower_db_max_pool_size                  = 10
tower_db_max_lifetime                   = 18000000
flyway_locations                        = "classpath:db-schema/mysql"
## tower_db_user                         = "DO_NOT_UNCOMMENT_ME"
## tower_db_password                     = "DO_NOT_UNCOMMENT_ME"

## tower_redis_url                       = "DO_NOT_UNCOMMENT_ME"
## tower_redis_password                  = "DO_NOT_UNCOMMENT_ME"

tower_smtp_host                         = "email-smtp.us-east-1.amazonaws.com"  #"in-v3.mailjet.com"  # "
tower_smtp_port                         = "587"
## tower_smtp_user                      = "DO_NOT_UNCOMMENT_ME"
## tower_smtp_password                  = "DO_NOT_UNCOMMENT_ME"
tower_smtp_auth                         = true
tower_smtp_starttls_enable              = true
tower_smtp_starttls_required            = true
tower_smtp_ssl_protocols                = "TLSv1.2"

# tower_root_users                        = "gwright99@hotmail.com,graham.wright@seqera.io,daniel.wood@seqera.io"
tower_root_users                        = "graham.wright@seqera.io,gwright99@hotmail.com"
tower_email_trusted_orgs                = "*@abc.com, *@def.com"
tower_email_trusted_users               = "123@abc.com, 456@def.com"

tower_audit_retention_days              = 1095      # 3 years (value in days)


## ------------------------------------------------------------------------------------
## TOWER CONFIGURATION - OIDC
## ------------------------------------------------------------------------------------
flag_oidc_use_generic                  = true
flag_oidc_use_google                   = true
flag_oidc_use_github                   = true

flag_disable_email_login               = false


## ------------------------------------------------------------------------------------
## EC2 - Docker Configuration
# https://docs.docker.com/config/containers/logging/local/
# https://github.com/seqeralabs/cx-field-tools-installer/issues/58
## ------------------------------------------------------------------------------------
# docker info --format '{{ .LoggingDriver }}'
# sudo journalctl CONTAINER_NAME=ec2-user-backend-1
flag_docker_logging_local              = false
flag_docker_logging_journald           = true
flag_docker_logging_jsonfile           = false

docker_cidr_range                      = "172.80.0.0/16"

## ------------------------------------------------------------------------------------
## Seqerakit
# graham.wright@seqera.io,
## ------------------------------------------------------------------------------------
flag_run_seqerakit                      = true

seqerakit_org_name                      = "SampleOrg3"
seqerakit_org_fullname                  = "SampleOrgFullName"
seqerakit_org_url                       = "https://www.example.com"

seqerakit_team_name                     = "SampleTeam"
seqerakit_team_members                  = "daniel.wood@seqera.io,graham.wright+001@seqera.io"

seqerakit_workspace_name                = "SampleWorkspace"
seqerakit_workspace_fullname            = "SampleWorkspaceFullName"

seqerakit_compute_env_name              = "MyComputeEnvironment"
seqerakit_compute_env_region            = "us-east-1"

seqerakit_root_bucket                   = "s3://nf-nvirginia"
seqerakit_workdir                       = "s3://nf-nvirginia/seqerakittesting"
seqerakit_outdir                        = "s3://nf-nfvirginia/sk_outdir"

seqerakit_aws_use_fusion_v2             = false
seqerakit_aws_use_forge                 = false
seqerakit_aws_use_batch                 = true

seqerakit_aws_fusion_instances          = "c6id,r6id,m6id"
seqerakit_aws_normal_instances          = "optimal"

seqerakit_aws_manual_head_queue         = "TowerForge-4rp223pYWe8kQ5LWtcYVz6-head"
seqerakit_aws_manual_compute_queue      = "TowerForge-4rp223pYWe8kQ5LWtcYVz6-work"


## ------------------------------------------------------------------------------------
## Seqerakit - Credentials
## ------------------------------------------------------------------------------------
seqerakit_flag_credential_create_aws        = true
seqerakit_flag_credential_create_github     = true
seqerakit_flag_credential_create_docker     = false
seqerakit_flag_credential_create_codecommit = false

seqerakit_flag_credential_use_aws_role      = true
seqerakit_flag_credential_use_codecommit_baseurl = false



EOF