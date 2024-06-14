/*
## ------------------------------------------------------------------------------------
## Mandatory Bootstrap Values
## ------------------------------------------------------------------------------------
This is the most critical configuration section. 

If you intend to run multiple instances in the same account, you MUST ensure that each 
implementation has its own unique `app_name`. This name is used as a namespace isolator 
in the AWS SSM prefix and ensures the right configuration is pulled for the right stack.

Once you have created the omnibus secret objects in SSM (see `templates/ssm_*` files),
supply these values to the `secrets_bootstrap_*` parameters. During the deployment, these 
objects will be retrieved and created as individual key-value pairs in the SSM (in a way
that makes the values available to the Tower instance via its native SSM integration).

`aws_*` values are required to ensure Terraform is acting against the correct AWS target.
Client authentication regimes can vary (static keys, role assumption, credential process,
etc) and it is impossible to accommodate all scenarios OOTB. The values supplied here are 
used to configure the `aws provider` in `000-main.tf`. Adjust if necessary.

`tower_container_version` identifies the proprietary Seqera containers your Seqera Platform 
will use. While it is possible to bump/drop versions and successfully redeploy, be mindful
that each version has its expectations re: configuration settings and database migration.
Before changing this value, consider backing up your database and consulting Seqera Platform
Release Notes (https://docs.seqera.io/platform/latest/enterprise/release_notes/enterprise_latest)
for any notable breaking change.
*/

# Use hyphen as separator or else some AWS resource nameing breaks (e.g. ALB)
app_name                                = "tower-dev"

secrets_bootstrap_tower                 = "/seqera/sensitive-values/tower-dev/tower"
secrets_bootstrap_seqerakit             = "/seqera/sensitive-values/tower-dev/seqerakit"
secrets_bootstrap_groundswell           = "/seqera/sensitive-values/tower-dev/groundswell"

aws_account                             = "REPLACE_ME"
aws_region                              = "REPLACE_ME"
aws_profile                             = "REPLACE_ME"

tower_container_version                 = "v23.3.0"


/*
## ------------------------------------------------------------------------------------
## Tags -- Default
## ------------------------------------------------------------------------------------
Default tags to put on every generated resource.
*/
default_tags  = {
      Terraform                     = "true"
      Environment                   = "dev"
}


/*
## ------------------------------------------------------------------------------------
## Flags - Custom Naming
## ------------------------------------------------------------------------------------
Use these settings to forgo the default `tf-RANDOM-NAME-` resource name prefix.
Do not include hyphen at end (unless you want a double hyphen in the resulting name).
Use hyphen as separator.
*/
flag_use_custom_resource_naming_prefix = false
custom_resource_naming_prefix          = "REPLACE_ME_IF_NECESSARY"


/*
## ------------------------------------------------------------------------------------
## Flags - Infrastructure
## ------------------------------------------------------------------------------------
These flags control what infrastructure will be created new versus what already-in-place 
assets can be leveraged. The flags set here will require further changes in the sections below
(example: `flag_create_new_vpc = true` will require you to make decisions about subnets and CIDRs
in `VPC (New)` section). 

Related flags are grouped into a logical block. Only 1 entry in each block should be true.

We generally suggest clients deploy into a new VPC when possible. This minimizes blast-radius in the 
event of an error and allows you to focus on the stack itself rather than having to troubleshoot unexpected 
behaviours due to other assets in your pre-existing VPC. Once you are happy things are working properly, 
you can start to introduce pre-existing assets.

New VPC deployments may sometimes be inappropriate for your business reality (i.e. you have highly customized 
networking / firewall rules / restrictive policies on access to core services like email and DNS. In such cases,
deploying into an existing VPC should be the preferred option. 

Load-balancing can prove to be tricky due to its implications on networking and TLS certificates, and behaviour
assumptions we have made while building the tool. Please note:

  - If you want to use an ALB in your solution, it will be net new (we do not support using an existing instance).
  - If you use an ALB in your solution, it MUST serve a TLS certifcate stored in the AWS Certificate Manager.
  - If you need TLS but don't want an ALB, we supply a custom docker-compose file running an nginx reverse-proxy
    which can be loaded up with a CA certificate and key (we suggest using the ALB whenever possible, however).
      - This solution supports the use of pre-existing certificates & the creation of a brand new self-signed CA.
      - This flow has not been extensively tested and is commended only for highly specific circumstances.
  - Although *highly* unadvised (given the relative ease with which a TLS cert can be provisioned these days),
    you may also choose to run your instance in HTTP-only mode. Choosing this option will result in the addition of 
    the `TOWER_ENABLE_UNSAFE_MODE = TRUE` config setting to your Seqera Platform instance.
*/

# Only one of these can true.
flag_create_new_vpc                     = true
flag_use_existing_vpc                   = false

# Only one of these can be true.
flag_create_external_db                 = false
flag_use_existing_external_db           = false
flag_use_container_db                   = true

# Only one of these can be true.
flag_create_external_redis              = false
flag_use_container_redis                = true

# Only one of these can true.
flag_create_load_balancer               = true
flag_generate_private_cacert            = false
flag_use_existing_private_cacert        = false
flag_do_not_use_https                   = false


/*
## ------------------------------------------------------------------------------------
## Flags - Networking
## ------------------------------------------------------------------------------------
Your Seqera Platform instance needs to be reachable via http/https (for your users), and
via SSH (administrators/installer). Depending on users and corporate policies, your Tower 
instance may need to be directly accessible via the public internet, or locked to a limited 
subset of internal traffic only.

If you choose to make your instance public, it will reside in a public subnet with a public IP.
You can still place a load-balancer in front of the application, but SSH will occur by direclty 
calling the VM on port 22.

If you choose to make your Tower private, SSH networking becomes more difficult. By default, an
AWS Instance Connect Endpoint will be created and associated with the private subnet where your 
Tower instance resides. Access is controlled via a combination of SSH key and IAM permissions. 
This solution is good for green-field deployments into relatively open AWS accounts. 

If you make your Tower fully private, please note:

  1. The instance must still be capable of egressing to the public internet (i.e. NAT). If you 
     choose to create a new VPC, be advised that opinionated NAT-related decisions are hardcoded
    into the `001-vpc.tf` file.

  2. Making your instance fully private can cause downstream complications in the event your 
     compute environments reside in another AWS Account / cloud (the Nextflow head job needs to
     be able to establish a connection back to the Tower instance).

If deploying into an existing VPC with bespoke networking, the EICE may be inappropriate. In such
cases - if private networking already exists between your workstation and the VPC into which Tower 
is being installed, choose the `flag_private_tower_without_eice` option. This causes the generated 
ssh_config file to be populated with the VM's private IP, with any SSH connection being sent to the VM
directly.

The remaining entries in this section are present because they are affected by networking accessibility
decisions:

  - You can tell the installer to stop as soon as infrastructure is provisioned and 
    the `assets/target` folder has been created. We don't advise setting this to false, but it is available
    in the event your networking restrictions are so tight that a real-time SSH connection simply isn't possible.

  - The custom docker-compose file is partially affected by the TLS flag decision in the previous section but
    also because the `assets/customcerts/custom_default.conf` file may need to be adjusted.

  - Setting the Wave flag to true means the Wave Service will be available to your instance, but also relies on 
    the ability for the Seqera Platform instance to successfully establish a Websockets connection to the 
    `wave.seqera.io` endpoint.
*/

# Only one of these can true.
flag_make_instance_public                       = false
flag_make_instance_private                      = false
flag_make_instance_private_behind_public_alb    = true
flag_private_tower_without_eice                 = false

# Manage how to talk to VM for config file transfer.
flag_vm_copy_files_to_instance                  = true

# Indicate whether custom section of the docker-compose template file should be included in final render.
flag_use_custom_docker_compose_file             = false


/*
## ------------------------------------------------------------------------------------
## Wave Service
## ------------------------------------------------------------------------------------
*/
# Enable Tower to connect to the Wave service hosted by Seqera
flag_use_wave                      = false
wave_server_url                    = "https://wave.seqera.io"

/*
## ------------------------------------------------------------------------------------
## Flags - DNS
## ------------------------------------------------------------------------------------
DNS regimes can vary and the installer tries its best to be flexible. Several options are
available if you are able to limit the generation of A records within the AWS Account where
your Seqera Platform instance resides. If this is not possible, a workaround will be used
where the value of the TOWER_SERVER_URL value is written into the VM's `etc/hosts` 
file to support short-term installer needs while you update your external DNS independently 
(remember to remove the `/etc/hosts` entry once this offline process is complete!).

In our experience, clients have found it handy to purchase a domain within the AWS Account 
where the Seqera Platform instance will run. This allows the project team to quickly make
updates when necessary and avoid a dependency on potentially slower-moving elements in their
organization. The downside, however, is that this introduces shadow IT into the organization.
Choose the option that is appropriate for you.
*/

# Only one can be true
flag_create_route53_private_zone        = true
flag_use_existing_route53_public_zone   = false
flag_use_existing_route53_private_zone  = false
flag_create_hosts_file_entry            = false

# Populate this field if creating a new private hosted zone
new_route53_private_zone_name           = "REPLACE_ME_IF_NEEDED"

# Only populate if flag set above to use existing hosted zone.
existing_route53_public_zone_name       = "REPLACE_ME_IF_NEEDED"
existing_route53_private_zone_name      = "REPLACE_ME_IF_NEEDED"


/*
## ------------------------------------------------------------------------------------
## Custom Private CA
## ------------------------------------------------------------------------------------
Do not use this option unless absolutely necessary. In general, your pipeline maintenance 
obligations will be easier if you use a public certificate (e.g. issued by AWS) on an ALB.
See: https://docs.seqera.io/platform/latest/enterprise/configuration/ssl_tls

If you choose to generate a new private CA, the CA cert needs to be captured in a
centrally-available solution so that Nextflow head jobs can pull it dynamically at run time.

If you choose to use a pre-issued TLS certificate and not use an ALB, ensure the .crt and .key
files are places in `assets/src/customcerts` and specify the filenames here. These names are
automatically inserted into the generated configuration file.

REMINDER: If you choose either of these options, ensure the `flag_use_custom_docker_compose_file` 
flag is set to true.
*/

# Include s3:// and omit trailing slash
bucket_prefix_for_new_private_ca_cert   = "REPLACE_ME_IF_NEEDED"

# If using a preexisting key/cert, populate these with filename (stored in `assets/src/customcerts`).
existing_ca_cert_file                   = "REPLACE_ME_IF_NEEDED"
existing_ca_key_file                    = "REPLACE_ME_IF_NEEDED"


/*
## ------------------------------------------------------------------------------------
## VPC (New)
## ------------------------------------------------------------------------------------
Values here are placeholders only. Replace as necessary.
NOTES:
  - Ensure the region specified in `vpc_new_az` matches the region at top of file.
  - You must always have at least one public subnet (for NAT egress).
  - You must have at least 2 public subnets if using an internet-facing ALB.
  - There must only be a single EC2 subnet (to align with EICE quota limitations)
*/

vpc_new_cidr_range                      = "10.0.0.0/16"
vpc_new_azs                             = [ "REPLACE_ME_IF_NEEDED-1a", "REPLACE_ME_IF_NEEDED-1b" ]

vpc_new_public_subnets                  = [ "10.0.1.0/24", "10.0.2.0/24" ]
vpc_new_private_subnets                 = [ "10.0.3.0/24", "10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24" ]

# Ensure these subnet ranges align to what's created above. 
vpc_new_ec2_subnets                     = [ "10.0.3.0/24" ]  # Can only 1 for EICE to work.
vpc_new_batch_subnets                   = [ "10.0.3.0/24" ]
vpc_new_db_subnets                      = [ "10.0.3.0/24", "10.0.4.0/24" ]
vpc_new_redis_subnets                   = [ "10.0.5.0/24" ]


# Must be >= 2, in different AZs. Ensure only public subnets (nothing needs to be in these).
vpc_new_alb_subnets                     = [ "10.0.1.0/24", "10.0.2.0/24" ]

# Specify is VPC flow logs should be enabled or not. Have cost implication.
enable_vpc_flow_logs                    = false


/*
## ------------------------------------------------------------------------------------
## VPC (Existing)
## - If using existing IP, ensure ec2 subnet has public IP via auto-assignment (current as of Nov 16/23).
## ------------------------------------------------------------------------------------
Values here are placeholders only. Replace as necessary.
NOTES:
  - Ensure your private subnets have egress rights to the internet via NAT.
  - If your VM is in a public subnet, ensure the subnet auto-assigns a public IP.
  - You must have at least 2 public subnets if using an internet-facing ALB.
  - There must only be a single EC2 subnet (to align with EICE quota limitations)
*/

vpc_existing_id                         = "REPLACE_ME_IF_NEEDED"
vpc_existing_ec2_subnets                = [ "10.0.1.0/24" ]
vpc_existing_batch_subnets              = [ "10.0.2.0/24", "10.0.3.0/24" ]
vpc_existing_db_subnets                 = [ "10.0.4.0/24", "10.0.5.0/24" ]
vpc_existing_redis_subnets              = [ "10.0.6.0/24" ]

# Must be >= 2, in different AZs. Ensure only public subnets (nothing needs to be in these).
vpc_existing_alb_subnets                = [ "10.0.1.0/24", "10.0.2.0/24" ]

/*
## ------------------------------------------------------------------------------------
## VPC Endpoints
## ------------------------------------------------------------------------------------
All endpoint options can be found here: https://docs.aws.amazon.com/vpc/latest/privatelink/aws-services-privatelink-support.html
Only include the service-specific portion of the name. 
Eg. For EC2, use "ec2" rather than `com.amazonaws.region.ec2`
*/
vpc_gateway_endpoints_all                 = ["s3"]

vpc_interface_endpoints_tower             = []
vpc_interface_endpoints_batch             = []


/*
## ------------------------------------------------------------------------------------
## Security Group - Transaction Sources
## ------------------------------------------------------------------------------------
These settings control which IPs are allowed to call the VM / ALB. For ease of initial setup
these are *very* loose. Consider tightening if your deployment model allows it. 

If using EICE, please note that individuals must have IAM rights to interact with the endpoint 
prior to any SSH transaction being allowed against the VM. 

Egress is open by default given variability of client implementations. Can be tightened if need be.
See: https://github.com/terraform-aws-modules/terraform-aws-security-group/blob/master/rules.tf
*/

sg_ingress_cidrs                        = ["0.0.0.0/0"]
sg_ssh_cidrs                            = ["0.0.0.0/0"]

sg_egress_eice = ["all-all"]
sg_egress_tower_ec2 = ["all-all"]
sg_egress_tower_alb = ["all-all"]
sg_egress_batch_ec2 = ["all-all"]
sg_egress_interface_endpoint = ["all-all"]

/*
## ------------------------------------------------------------------------------------
## Groundswell
## ------------------------------------------------------------------------------------
Enable to allow pipeline optimization.
*/

flag_enable_groundswell                 = true

swell_container_version                 = "0.4.0"
swell_database_name                     = "swell"
## swell_db_user                        = "DO_NOT_UNCOMMENT_ME"
## swell_db_password                    = "DO_NOT_UNCOMMENT_ME"


/*
## ------------------------------------------------------------------------------------
## Data Explorer - Feature Gated (23.4.3+)
## ------------------------------------------------------------------------------------
Enable to allow Data Explorer functionality. See https://docs.seqera.io/platform/latest/data/data-explorer for details.
*/
flag_data_explorer_enabled                = true
data_explorer_disabled_workspaces         = ""


/*
## ------------------------------------------------------------------------------------
## Database (Generic)
## Values that apply to both the containerized and RDS DBs
## ------------------------------------------------------------------------------------
## db_root_user                         = "DO_NOT_UNCOMMENT_ME"
## db_root_password                     = "DO_NOT_UNCOMMENT_ME"
## tower_db_user                        = "DO_NOT_UNCOMMENT_ME"
## tower_db_password                    = "DO_NOT_UNCOMMENT_ME"

WARNING:
  - If you create a database as part of your deployment, it will be destroyed on teardown.
  - You must supply your own backup solution.
*/

db_database_name                        = "tower"


/*
## ------------------------------------------------------------------------------------
## Database (Container)
## Specify the details of the external database to create (if applicable)
## ------------------------------------------------------------------------------------
This section added to handle new connection string requirements for Tower v24.1.0+
*/
db_container_engine                               = "mysql"
db_container_engine_version                       = "8.0"


/*
## ------------------------------------------------------------------------------------
## Database (External)
## ------------------------------------------------------------------------------------
The official Seqera reference architecture advises using an RDS instance as your Seqera 
Platform's database. 

You may choose to forgo this in lower environments if you are cost-conscious. Additionally,
when conducting initial interative testing, you may wish to stick with the containerized 
database option as this avoids ~8 minutes of waiting for the RDS instance to instantiate 
during each deployment cycle.

Commented out settings with value "DO_NOT_UNCOMMENT_ME" exist solely as visual reminder that
these settings are being used, but the value is coming from the SSM secret source.

WARNING:
  - If you create a database as part of your deployment, it will be destroyed on teardown.
  - You must supply your own backup solution.
*/

db_engine                               = "mysql"
db_engine_version                       = "8.0"
db_instance_class                       = "db.m5.large"
db_allocated_storage                    = 30

db_deletion_protection                  = true
skip_final_snapshot                     = false

db_backup_retention_period              = 7
db_enable_storage_encrypted             = true


/*
## ------------------------------------------------------------------------------------
## IAM
## ------------------------------------------------------------------------------------
By default, the installer will create an IAM Instance Role for the Seqera Platform VM. 

In the event that your AWS Account is locked down and access to IAM is restricted, you 
may override this process and supply a pre-generated entity. 

NOTE: Remember that this is an INSTANCE role arn, not a normal Role.
*/

flag_iam_use_prexisting_role_arn        = false
iam_prexisting_instance_role_arn        = "REPLACE_ME_IF_NEEDED"


/*
## ------------------------------------------------------------------------------------
## SMTP
## ------------------------------------------------------------------------------------
Newer instances of Tower support native integration with SES, which foregoes long-lived
access keys in favour of an SES IAM permissions attached to the VM Instance Role. This is 
the default option given the streamlined security gain.

If you do not wish to use SES integration, you can set this to false but will need to 
uncomment and populate the `tower_smtp_user` and `tower_smtp_password` values in the TOWER
CONFIGURATION section below.
*/

# Only one of these can true.
flag_use_aws_ses_iam_integration        = true
flag_use_existing_smtp                  = false


/*
## ------------------------------------------------------------------------------------
## EC2 Host
## ------------------------------------------------------------------------------------
We generally advise implementing EBS encryption at an AWS Account level, but provide options
for a target encryption of the Seqera Platform VM only.
*/

ec2_host_instance_type                  = "c5.2xlarge"

flag_encrypt_ebs                        = true
flag_use_kms_key                        = true
ec2_ebs_kms_key                         = "REPLACE_ME_IF_NEEDED"

ec2_require_imds_token                  = true

ec2_update_ami_if_available             = true


/* 
## ------------------------------------------------------------------------------------
## ALB
## ------------------------------------------------------------------------------------
This must be a TLS certificate stored in the Amazon Certificate Manager.

If you have an already-issued cert from a public CA, consider storing it in ACM and using 
an ALB to serve or else you will need to use the custom docker-compose file option with
a local nginx container acting as the TLS termination point. 
*/

alb_certificate_arn                     = "REPLACE_ME_IF_NEEDED"


/*
## ------------------------------------------------------------------------------------
## TOWER CONFIGURATION
## ------------------------------------------------------------------------------------
Please consult https://docs.seqera.io/platform/latest/enterprise/configuration/overview for
detailed configuration guidance.
*/

# Ensure this aligns with the values specified in `Flags - DNS` section above.
# Do not include http prefix. e.g. `autodc.dev-seqera.net`. 
tower_server_url                        = "REPLACE_ME"
tower_server_port                       = "8000"

# This must be a verified identity / domain.
tower_contact_email                     = "REPLACE_ME"
tower_enable_platforms                  = "awsbatch-platform,k8s-platform,slurm-platform"

## tower_jwt_secret                      = "DO_NOT_UNCOMMENT_ME"
## tower_crypto_secretkey                = "DO_NOT_UNCOMMENT_ME"
## tower_license                         = "DO_NOT_UNCOMMENT_ME"

# Do not include 'jdbc:mysql://`. Include database if using existing external db (i.e. `/tower`). 
tower_db_url                            = "db:3306"
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

tower_smtp_host                         = "REPLACE_ME"
tower_smtp_port                         = "REPLACE_ME"
## tower_smtp_user                      = "REPLACE_ME_IF_NEEDED"
## tower_smtp_password                  = "REPLACE_ME_IF_NEEDED"
tower_smtp_auth                         = true
tower_smtp_starttls_enable              = true
tower_smtp_starttls_required            = true
tower_smtp_ssl_protocols                = "TLSv1.2"

tower_root_users                        = "REPLACE_ME"
tower_email_trusted_orgs                = "REPLACE_ME"
tower_email_trusted_users               = "REPLACE_ME"


/*
## ------------------------------------------------------------------------------------
## TOWER CONFIGURATION - OIDC
## ------------------------------------------------------------------------------------
Enable these settings to activate the OIDC login flow on the Seqera Platform landing page.

Please note that you must supply your OIDC secrets in the `ssm_sensitive_values_tower.json`
and have a pre-configured OIDC IDP ready to accept requests.
*/

flag_oidc_use_generic                  = false
flag_oidc_use_google                   = false
flag_oidc_use_github                   = false

flag_disable_email_login               = false


/*
## ------------------------------------------------------------------------------------
## EC2 - Docker Driver Logging
## ------------------------------------------------------------------------------------
# https://docs.docker.com/config/containers/logging/local/
*/
flag_docker_logging_local              = false
flag_docker_logging_journald           = true
flag_docker_logging_jsonfile           = false


/*
## ------------------------------------------------------------------------------------
## seqerakit
## ------------------------------------------------------------------------------------
This section is an optional post-configuration activity. Once infrastructure is provisioned
and the Seqera Platform instance is running, you can create a compute environment and execute 
a small pipeline run to verify if the environment is properly configured.

WARNING:

  - Terraform state is NOT aware of activities taken within your Seqera Platform instance. If
    you create compute environments via Tower Forge, please remember to purge these instances 
    prior to tearing down the Terraform project.
  - Please ensure the first entry of the `tower_root_users` field is added as a
    `seqerakit_team_members` entry -- this will ensure the seqerakit population calls can
    complete successfully. 
*/

flag_run_seqerakit                      = false

seqerakit_org_name                      = "SampleOrg"
seqerakit_org_fullname                  = "SampleOrgFullName"
seqerakit_org_url                       = "https://www.example.com"

seqerakit_team_name                     = "SampleTeam"
seqerakit_team_members                  = "REPLACE_ME,REPLACE_ME"

seqerakit_workspace_name                = "SampleWorkspace"
seqerakit_workspace_fullname            = "SampleWorkspaceFullName"

seqerakit_compute_env_name              = "MyComputeEnvironment"
seqerakit_compute_env_region            = "REPLACE_ME"

seqerakit_root_bucket                   = "s3://REPLACE_ME"
seqerakit_workdir                       = "s3://REPLACE_ME"
seqerakit_outdir                        = "s3://REPLACE_ME"

seqerakit_aws_use_fusion_v2             = true
seqerakit_aws_use_forge                 = true
seqerakit_aws_use_batch                 = true

seqerakit_aws_fusion_instances          = "c6id,r6id,m6id"
seqerakit_aws_normal_instances          = "optimal"

seqerakit_aws_manual_head_queue         = "REPLACE_ME_IF_NEEDED"
seqerakit_aws_manual_compute_queue      = "REPLACE_ME_IF_NEEDED"


/*
## ------------------------------------------------------------------------------------
## Seqerakit - Credentials
## ------------------------------------------------------------------------------------
By default, Seqerakit expects GitHub, Docker, and AWS to be defined in the `ssm_sensitive_values_seqera.json` 
secret object. These are not absolutely necessary for initial short-term testing (although useful) and can 
therefore be deactivated if not supplied.
*/

seqerakit_flag_credential_create_aws        = true
seqerakit_flag_credential_create_github     = true
seqerakit_flag_credential_create_docker     = true
seqerakit_flag_credential_create_codecommit = false

seqerakit_flag_credential_use_aws_role      = true
