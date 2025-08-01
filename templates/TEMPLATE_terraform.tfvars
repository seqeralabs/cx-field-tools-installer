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
app_name = "tower-template"

secrets_bootstrap_tower       = "/seqera/sensitive-values/tower-template/tower"
secrets_bootstrap_seqerakit   = "/seqera/sensitive-values/tower-template/seqerakit"
secrets_bootstrap_groundswell = "/seqera/sensitive-values/tower-template/groundswell"
secrets_bootstrap_wave_lite   = "/seqera/sensitive-values/tower-template/wave-lite"


aws_account = "REPLACE_ME"
aws_region  = "REPLACE_ME"
aws_profile = "REPLACE_ME"

tower_container_version = "v25.2.0"


/*
## ------------------------------------------------------------------------------------
## SSM
## ------------------------------------------------------------------------------------
Activate this setting to allow n+1 deployments to overwrite SSM keys if they were not 
generated by your own Terraform project (can be useful to set this to true if running 2+ 
instances off of the same configuration, otherwise you will get errors at the end of the
`apply` cycle.

Note! 
 - 1) Terraform will show a deprecation warning -- there is no better option than this
 however, so we continue to use this option for now).
 - 2) Setting this value to `false` will not prevent overrwrites if SSM entries are
  tracked within your own project state.
*/
flag_overwrite_ssm_keys = true


/*
## ------------------------------------------------------------------------------------
## Tags -- Default
## ------------------------------------------------------------------------------------
Default tags to put on every generated resource.
*/
default_tags = {
  Terraform   = "true"
  Environment = "dev"
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
flag_create_new_vpc   = true
flag_use_existing_vpc = false

# Only one of these can be true.
# NOTE: If using pre-existing RDS instance, ensure it accepts traffic from whole VPC on 3306.
flag_create_external_db       = false
flag_use_existing_external_db = false
flag_use_container_db         = true

# Only one of these can be true.
# NOTE: Redis versions and ports are hard-coded in their respective files (docker-compose.yaml &
#  003-database.tf)
flag_create_external_redis = false
flag_use_container_redis   = true

# Only one of these can true.
# NOTE: If using `flag_use_private_cacert = true` flag, read Custom Private CA section for full instructions on private cert set-up.
flag_create_load_balancer = true
flag_use_private_cacert   = false
flag_do_not_use_https     = false


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
# flag_make_instance_private or flag_private_tower_without_eice = true makes ALB internal-facing
# flag_make_instance_private_behind_public_alb = true makes ALB internet-facing
flag_make_instance_public                    = false
flag_make_instance_private                   = false
flag_make_instance_private_behind_public_alb = true
flag_private_tower_without_eice              = false

# Manage how to talk to VM for config file transfer.
flag_vm_copy_files_to_instance = true


/*
## ------------------------------------------------------------------------------------
## Wave Service
## ------------------------------------------------------------------------------------
Enable Tower to connect to the Wave service.

To connect the Seqera-hosted Wave Service, set `flag_use_wave` to true.
To connect to a self-hosted Wave Lite instance instead, set `flag_use_wave_lite` to true.

You should not need to modify the URL of the Seqera-hosted wave.

If you are deploying a Wave-LIte instance, you will need to make a decision re: DNS. Seqera recommends exposing 
the service as a subdomain of your `tower_server_url` value (see entry in section further below). This pattern works 
well because you can reuse this pattern if/when you enable the Studios feature. e.g:
    - wave.myseqeraplatform.example.com

If you organization cannot support subdomains, you will need to deply a peer record so that DNS population logic continues 
to work. e.g:
    - myseqeraplatform.example.com
    - mywavelite.example.com

*/
flag_use_wave          = false
flag_use_wave_lite     = false
num_wave_lite_replicas = 2
wave_server_url        = "https://wave.seqera.io"
wave_lite_server_url   = "https://REPLACE_ME_IF_NEEDED"

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
flag_create_route53_private_zone       = true
flag_use_existing_route53_public_zone  = false
flag_use_existing_route53_private_zone = false
flag_create_hosts_file_entry           = false

# Populate this field if creating a new private hosted zone
new_route53_private_zone_name = "REPLACE_ME_IF_NEEDED"

# Only populate if flag set above to use existing hosted zone.
existing_route53_public_zone_name  = "REPLACE_ME_IF_NEEDED"
existing_route53_private_zone_name = "REPLACE_ME_IF_NEEDED"


/*
## ------------------------------------------------------------------------------------
## Custom Private CA
## ------------------------------------------------------------------------------------
Do not use this option unless absolutely necessary. In general, your pipeline maintenance 
obligations will be easier if you use a public certificate (e.g. issued by AWS) on an ALB.
See: https://docs.seqera.io/platform/latest/enterprise/configuration/ssl_tls

If you choose to generate a new private CA, please following the instructions in 
`documentation/setup/optional_private_certificates.md`
*/

# Include s3:// and omit trailing slash
private_cacert_bucket_prefix = "REPLACE_ME_IF_NEEDED"


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

vpc_new_cidr_range = "10.0.0.0/16"
vpc_new_azs        = ["REPLACE_ME_IF_NEEDED-1a", "REPLACE_ME_IF_NEEDED-1b"]

vpc_new_public_subnets  = ["10.0.1.0/24", "10.0.2.0/24"]
vpc_new_private_subnets = ["10.0.3.0/24", "10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24"]

# Ensure these subnet ranges align to what's created above. 
vpc_new_ec2_subnets   = ["10.0.3.0/24"] # Can only 1 for EICE to work.
vpc_new_batch_subnets = ["10.0.3.0/24"]
vpc_new_db_subnets    = ["10.0.3.0/24", "10.0.4.0/24"]
vpc_new_redis_subnets = ["10.0.5.0/24"]


# Must be >= 2, in different AZs. Ensure only public subnets (nothing needs to be in these).
vpc_new_alb_subnets = ["10.0.1.0/24", "10.0.2.0/24"]

# Specify is VPC flow logs should be enabled or not. Have cost implication.
enable_vpc_flow_logs = false


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

vpc_existing_id            = "REPLACE_ME_IF_NEEDED"
vpc_existing_ec2_subnets   = ["10.0.1.0/24"]
vpc_existing_batch_subnets = ["10.0.2.0/24", "10.0.3.0/24"]
vpc_existing_db_subnets    = ["10.0.4.0/24", "10.0.5.0/24"]
vpc_existing_redis_subnets = ["10.0.6.0/24"]

# Must be >= 2, in different AZs. Ensure only public subnets (nothing needs to be in these).
vpc_existing_alb_subnets = ["10.0.1.0/24", "10.0.2.0/24"]

/*
## ------------------------------------------------------------------------------------
## VPC Endpoints
## ------------------------------------------------------------------------------------
All endpoint options can be found here: https://docs.aws.amazon.com/vpc/latest/privatelink/aws-services-privatelink-support.html
Only include the service-specific portion of the name. 
Eg. For EC2, use "ec2" rather than `com.amazonaws.region.ec2`
*/
vpc_gateway_endpoints_all = ["s3"]

vpc_interface_endpoints_tower = []
vpc_interface_endpoints_batch = []


/*
## ------------------------------------------------------------------------------------
## Security Group - Transaction Sources
## ------------------------------------------------------------------------------------
These settings control which IPs are allowed to call the VM / ALB. For ease of initial setup
these are *very* loose. Consider tightening if your deployment model allows it. The arrays can 
contain multiple entries if necessary (e.g. you might wish to both your VPN CIDR and home IP to
be able to make HTTPS calls / SSH connections).

If using EICE, please note that individuals must have IAM rights to interact with the endpoint 
prior to any SSH transaction being allowed against the VM. 

Egress is open by default given variability of client implementations. Can be tightened if need be.
See: https://github.com/terraform-aws-modules/terraform-aws-security-group/blob/master/rules.tf
*/

sg_ingress_cidrs = ["0.0.0.0/0"]
sg_ssh_cidrs     = ["0.0.0.0/0"]

sg_egress_eice               = ["all-all"]
sg_egress_tower_ec2          = ["all-all"]
sg_egress_tower_alb          = ["all-all"]
sg_egress_batch_ec2          = ["all-all"]
sg_egress_interface_endpoint = ["all-all"]

/*
## ------------------------------------------------------------------------------------
## Groundswell
## ------------------------------------------------------------------------------------
Enable to allow pipeline optimization.
*/

flag_enable_groundswell = true

swell_container_version = "0.4.0"
swell_database_name     = "swell"
## swell_db_user                        = "DO_NOT_UNCOMMENT_ME"
## swell_db_password                    = "DO_NOT_UNCOMMENT_ME"


/*
## ------------------------------------------------------------------------------------
## Data Explorer - Feature Gated (23.4.3+)
## ------------------------------------------------------------------------------------
Enable to allow Data Explorer functionality. See https://docs.seqera.io/platform/latest/data/data-explorer for details.
*/
flag_data_explorer_enabled        = true
data_explorer_disabled_workspaces = ""


/*
## ------------------------------------------------------------------------------------
## Data Studio - Feature Gated (24.1.0+)
## ------------------------------------------------------------------------------------
Enable to allow Data Studio functionality. Note, this requires several modifications to your instance.
Please check Release Notes and documentation to ensure this its your regulatory compliance needs.

Must use numeric id of target workspaces when populating `data_studio_eligible_workspaces`.

NOTES: 

1. If upgrading from a pre-24.1 installation, it is likely the existing certificate arn 
  provided to the `alb_certificate_arn` entry needs to be replaced with a new cert with more entries. 

2. If path-based routing (available as of v25.2.0), your ensure you certificate supports the domain
  specified in `data_studio_path_routing_url`.

3. The `data_studio_path_routing_url` should be a **bare domain** — do not include 
   protocol prefixes like `https://` or path components. Example: `autoconnect.autodc.dev-seqera.net`  
*/
flag_enable_data_studio         = true
flag_studio_enable_path_routing = false
data_studio_path_routing_url    = "REPLACE_ME_IF_NECESSARY"
data_studio_container_version   = "0.8.2"

flag_limit_data_studio_to_some_workspaces = false
data_studio_eligible_workspaces           = ""

# For full list of images Seqera makes available, please see: https://public.cr.seqera.io/
# NOTE!! 
#  1. Current as of v24.1.x, only images from publicly-available repositories can be used.
#     Private repositories will be supported in a future iteration.
#  2. `qualifier` values MUST use hyphens (`-`), NOT underscores (`_`).
#  3. Versioning Strategy (See Design Decisions for more details.)
#     - Major and minor versions are pinned explicitly (e.g., `1.83.0-0.7.1` and `1.83.0-0.8.0`).  
#     - Preference for clients v0.7 with a sliding patch version can be achieved by omitting the patch (e.g., use "0.7" instead of "0.7.1") to always get the latest patch update.
#   4. For the use of custom data studio images, ensure flag_use_wave = true. 
#   5. Acceptable status values are: "recommended", "deprecated", and "experimental". Anything will be displayed as "unsupported".
#   6. Current as of Platform v25.2.0, only VSCode, Jupyter, and R will work with path-based Studio routing (not Xpra). This must also be the 0.8.4 client version.

data_studio_options = {
  # DEPENDENCY
  # DEPRECATION NOTICE (July 22/25): Future versions of the installer will no longer include entries for connect-client v0.8.0. 
  #  Please update entries accordingly ahead of the a future version where the commented content will be removed. The most up-to-date version of connect-client is v0.8.0.

  vscode-1-83-0-0-8-0 = {
    qualifier = "VSCODE-1-83-0-0-8-0"
    icon      = "vscode"
    tool      = "vscode"
    status    = "deprecated"
    container = "public.cr.seqera.io/platform/data-studio-vscode:1.83.0-0.8.0"
  },
  jupyter-4-2-5-0-8-0 = {
    qualifier = "JUPYTER-4-2-5-0-8-0"
    icon      = "jupyter"
    tool      = "jupyter"
    status    = "deprecated"
    container = "public.cr.seqera.io/platform/data-studio-jupyter:4.2.5-0.8.0"
  },
  rstudio-4-4-1-0-8-0 = {
    qualifier = "RSTUDIO-4-4-1-0-8-0"
    icon      = "rstudio"
    tool      = "rstudio"
    status    = "deprecated"
    container = "public.cr.seqera.io/platform/data-studio-rstudio:4.4.1-0.8.0"
  },
  xpra-6-0-R0-0-8-0 = {
    qualifier = "XPRA-6-0-R0-0-8-0"
    icon      = "xpra"
    tool      = "xpra"
    status    = "recommended"
    container = "public.cr.seqera.io/platform/data-studio-xpra:6.0-r0-1-0.8.0"
  },
  vscode-1-101-2-0-8-4 = {
    qualifier = "VSCODE-1-101-2-0-8-4"
    icon      = "vscode"
    tool      = "vscode"
    status    = "recommended"
    container = "public.cr.seqera.io/platform/data-studio-vscode:1.101.2-0.8.4"
  },
  jupyter-4-2-5-0-8-4 = {
    qualifier = "JUPYTER-4-2-5-0-8-4"
    icon      = "jupyter"
    tool      = "jupyter"
    status    = "recommended"
    container = "public.cr.seqera.io/platform/data-studio-jupyter:4.2.5-0.8.4"
  },
  ride-2025-04-1-0-8-4 = {
    qualifier = "RIDE-2025-04-1-0-8-4"
    icon      = "rstudio"
    tool      = "rstudio"
    status    = "recommended"
    container = "public.cr.seqera.io/platform/data-studio-ride:2025.04.1-0.8.4"
  },
}

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

db_database_name = "tower"


/*
## ------------------------------------------------------------------------------------
## Database (Container)
## Specify the details of the external database to create (if applicable)
## ------------------------------------------------------------------------------------
This section added to handle new connection string requirements for Tower v24.1.0+
*/
db_container_engine         = "mysql"
db_container_engine_version = "8.0"

/*
## ------------------------------------------------------------------------------------
## Database (External)
## ------------------------------------------------------------------------------------
The official Seqera reference architecture advises using an RDS instance as your Seqera 
Platform's database. As of May 21/25 this section is augmented with settings for the
Wave-Lite feature (Release > 1.5.0).

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

db_engine            = "mysql"
db_engine_version    = "8.0"
db_param_group       = "mysql8.0"
db_instance_class    = "db.m5.large"
db_allocated_storage = 30

db_deletion_protection = true
skip_final_snapshot    = false

db_backup_retention_period  = 7
db_enable_storage_encrypted = true


wave_lite_db_engine            = "postgres"
wave_lite_db_engine_version    = "17.5"
wave_lite_db_param_group       = "postgres17"
wave_lite_db_instance_class    = "db.t4g.micro" #"db.m5.large"
wave_lite_db_allocated_storage = 10

wave_lite_db_deletion_protection      = false
wave_lite_skip_final_snapshot         = true
wave_lite_db_backup_retention_period  = 7
wave_lite_db_enable_storage_encrypted = true


/*
## ------------------------------------------------------------------------------------
## Elasticache (External)
## Specify the details of the external database to create or reuse
## ------------------------------------------------------------------------------------
This is a compound object designed to facilated passing of values to the underlying 
Elasticache module. 

The module supports both singleton (unclustered) and clusterd mode.
Unclustered & clustered modes are mutually exclusive; if the `unclustered` block's
`num_cache_nodes` is non-zero, the `clustered` block must keep its null values.
*/

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


/*
## ------------------------------------------------------------------------------------
## IAM
## ------------------------------------------------------------------------------------
By default, the installer will create an IAM Instance Role for the Seqera Platform VM. 

In the event that your AWS Account is locked down and access to IAM is restricted, you 
may override this process and supply a pre-generated entity. 

NOTE: Remember that this is an INSTANCE role arn, not a normal Role.
*/

flag_iam_use_prexisting_role_arn = false
iam_prexisting_instance_role_arn = "REPLACE_ME_IF_NEEDED"


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
flag_use_aws_ses_iam_integration = true
flag_use_existing_smtp           = false


/*
## ------------------------------------------------------------------------------------
## EC2 Host
## ------------------------------------------------------------------------------------
We generally advise implementing EBS encryption at an AWS Account level, but provide options
for a target encryption of the Seqera Platform VM only.

Some Amazon Linux 2023 AMIs (e.g. minimal) changed default boot size in late 2024. Starting
disk size can now be explicitly specified (in GiB).
*/

ec2_host_instance_type = "c5.2xlarge"

flag_encrypt_ebs     = true
flag_use_kms_key     = true
ec2_ebs_kms_key      = "REPLACE_ME_IF_NEEDED"
ec2_root_volume_size = 8

ec2_require_imds_token = true

ec2_update_ami_if_available = true


/* 
## ------------------------------------------------------------------------------------
## ALB
## ------------------------------------------------------------------------------------
This must be a TLS certificate stored in the Amazon Certificate Manager.

If you have an already-issued cert from a public CA, consider storing it in ACM and using 
an ALB to serve or else you will need to use the custom docker-compose file option with
a local nginx container acting as the TLS termination point.

NOTE: If upgrading from a pre-24.1 installation, it is likely the existing certificate arn 
provided must be replaced with a new cert with more entries. 
Please see https://docs.seqera.io for specific Data Studio cert guidance. 
*/

alb_certificate_arn = "REPLACE_ME_IF_NEEDED"


/*
## ------------------------------------------------------------------------------------
## TOWER CONFIGURATION
## ------------------------------------------------------------------------------------
Please consult https://docs.seqera.io/platform/latest/enterprise/configuration/overview for
detailed configuration guidance.
*/

# Ensure this aligns with the values specified in `Flags - DNS` section above.
# Do not include http prefix. e.g. `autodc.dev-seqera.net`. 
tower_server_url  = "REPLACE_ME"
tower_server_port = "8000"

# This must be a verified identity / domain.
tower_contact_email = "REPLACE_ME"

# See full list of compute environment options at: https://docs.seqera.io/platform-enterprise/latest/enterprise/configuration/overview#compute-environments
tower_enable_platforms = "awsbatch-platform,k8s-platform,slurm-platform"

## tower_jwt_secret                      = "DO_NOT_UNCOMMENT_ME"
## tower_crypto_secretkey                = "DO_NOT_UNCOMMENT_ME"
## tower_license                         = "DO_NOT_UNCOMMENT_ME"

# Do not include 'jdbc:mysql://`. 
# If using container db: use `db:3306`
# If using pre-existing external RDS instance, include the RDS Endpoint string only (no port or /xxx... URI modifier)
tower_db_url           = "db:3306"
tower_db_driver        = "org.mariadb.jdbc.Driver"
tower_db_dialect       = "io.seqera.util.MySQL55DialectCollateBin"
tower_db_min_pool_size = 5
tower_db_max_pool_size = 10
tower_db_max_lifetime  = 18000000
flyway_locations       = "classpath:db-schema/mysql"
## tower_db_user                         = "DO_NOT_UNCOMMENT_ME"
## tower_db_password                     = "DO_NOT_UNCOMMENT_ME"

## tower_redis_url                       = "DO_NOT_UNCOMMENT_ME"
## tower_redis_password                  = "DO_NOT_UNCOMMENT_ME"

tower_smtp_host = "REPLACE_ME"
tower_smtp_port = "REPLACE_ME"
## tower_smtp_user                      = "REPLACE_ME_IF_NEEDED"
## tower_smtp_password                  = "REPLACE_ME_IF_NEEDED"
tower_smtp_auth              = true
tower_smtp_starttls_enable   = true
tower_smtp_starttls_required = true
tower_smtp_ssl_protocols     = "TLSv1.2"

tower_root_users          = "REPLACE_ME"
tower_email_trusted_orgs  = "REPLACE_ME"
tower_email_trusted_users = "REPLACE_ME"

tower_audit_retention_days = 1095 # 3 years (value in days)


/*
## ------------------------------------------------------------------------------------
## TOWER CONFIGURATION - OIDC
## ------------------------------------------------------------------------------------
Enable these settings to activate the OIDC login flow on the Seqera Platform landing page.

Please note that you must supply your OIDC secrets in the `ssm_sensitive_values_tower.json`
and have a pre-configured OIDC IDP ready to accept requests.
*/

flag_oidc_use_generic = false
flag_oidc_use_google  = false
flag_oidc_use_github  = false

flag_disable_email_login = false


/*
## ------------------------------------------------------------------------------------
## EC2 - Docker Configuration
## ------------------------------------------------------------------------------------
# https://docs.docker.com/config/containers/logging/local/

CIDR Range -- docker's default CIDR ranges can often collide with CIDRs allocated to VPNs.
The generation of docker networks via docker-compose and cause VPN-based SSH access to 
fail due to the sudden introduction of conflicting CIDR ranges. Please see 
https://www.heuristic42.com/blog/59/on-docker-stealing-routes-and-breaking-the-internet for
more details.
*/

flag_docker_logging_local    = false
flag_docker_logging_journald = true
flag_docker_logging_jsonfile = false

docker_cidr_range = "172.80.0.0/16"


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

flag_run_seqerakit = false

seqerakit_org_name     = "SampleOrg"
seqerakit_org_fullname = "SampleOrgFullName"
seqerakit_org_url      = "https://www.example.com"

seqerakit_team_name    = "SampleTeam"
seqerakit_team_members = "REPLACE_ME,REPLACE_ME"

seqerakit_workspace_name     = "SampleWorkspace"
seqerakit_workspace_fullname = "SampleWorkspaceFullName"

seqerakit_compute_env_name   = "MyComputeEnvironment"
seqerakit_compute_env_region = "REPLACE_ME"

seqerakit_root_bucket = "s3://REPLACE_ME"
seqerakit_workdir     = "s3://REPLACE_ME"
seqerakit_outdir      = "s3://REPLACE_ME"

seqerakit_aws_use_fusion_v2 = true
seqerakit_aws_use_forge     = true
seqerakit_aws_use_batch     = true

seqerakit_aws_fusion_instances = "c6id,r6id,m6id"
seqerakit_aws_normal_instances = "optimal"

seqerakit_aws_manual_head_queue    = "REPLACE_ME_IF_NEEDED"
seqerakit_aws_manual_compute_queue = "REPLACE_ME_IF_NEEDED"


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

seqerakit_flag_credential_use_aws_role           = true
seqerakit_flag_credential_use_codecommit_baseurl = true
