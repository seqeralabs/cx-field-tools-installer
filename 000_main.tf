## ------------------------------------------------------------------------------------
## Provider & Backend
## ------------------------------------------------------------------------------------
terraform {
  required_version = ">= 1.1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.12.0"
    }
  }

  backend "local" {
    path = "DONTDELETE/terraform.tfstate"
  }

  # Uncomment to use S3 as backend. Consider use of DynamoDB as concurrency lock.
  # https://developer.hashicorp.com/terraform/language/settings/backends/configuration
  # backend "s3" {
  #   region                          = "us-east-1"  # No vars allowed
  #   bucket                          = "nf-nvirginia"
  #   key                             = "graham/terraform/terraform.tfstate"
  #   profile                         = "sts"
  #   shared_credentials_file         = "$HOME/.aws/credentials"
  # }
}


provider "aws" {
  region     = var.aws_region
  profile    = var.aws_profile
  retry_mode = "adaptive"

  default_tags {
    tags = var.default_tags
  }
}


## ------------------------------------------------------------------------------------
## Miscellaneous core resources and data
## ------------------------------------------------------------------------------------
# Generate unique namespace for this deployment (e.g "modern-sheep")
resource "random_pet" "stackname" {
  length = 2
}


data "aws_caller_identity" "current" {
  count = var.use_mocks ? 0 : 1
}



## ------------------------------------------------------------------------------------
## Omnibus Locals
## ------------------------------------------------------------------------------------
locals {

  # Housekeeping
  # ---------------------------------------------------------------------------------------
  global_prefix = var.flag_use_custom_resource_naming_prefix == true ? var.custom_resource_naming_prefix : "tf-${var.app_name}-${random_pet.stackname.id}"


  # Networking
  # ---------------------------------------------------------------------------------------
  vpc_id                      = var.flag_create_new_vpc == true ? module.vpc[0].vpc_id : var.vpc_existing_id
  vpc_private_route_table_ids = var.flag_create_new_vpc == true ? module.vpc[0].private_route_table_ids : data.aws_route_tables.preexisting[0].ids
  # Required for sg_from_nlb_ssh in 002_security_groups.tf.
  # NLB health checks originate from NLB nodes within the VPC — not from external IPs in sg_ingress_cidrs.
  # Without the VPC CIDR in the EC2 security group, health checks are blocked, the target shows unhealthy,
  # and the NLB stops forwarding real SSH traffic even though connect-proxy is running correctly.
  vpc_cidr_block = var.flag_create_new_vpc == true ? var.vpc_new_cidr_range : data.aws_vpc.preexisting[0].cidr_block

  flag_map_public_ip_on_launch = var.flag_map_public_ip_on_launch == true || var.flag_make_instance_public == true ? true : false

  # SSM
  # ---------------------------------------------------------------------------------------
  # Load bootstrapped secrets and define target for TF-generated SSM values. Magical - don't know why it works but it does.
  ssm_root = "/config/${var.app_name}"

  tower_secrets     = jsondecode(data.aws_ssm_parameter.tower_secrets.value)
  tower_secret_keys = nonsensitive(toset([for k, v in local.tower_secrets : k]))

  seqerakit_secrets     = jsondecode(data.aws_ssm_parameter.seqerakit_secrets.value)
  seqerakit_secret_keys = nonsensitive(toset([for k, v in local.seqerakit_secrets : k]))

  groundswell_secrets     = jsondecode(data.aws_ssm_parameter.groundswell_secrets.value)
  groundswell_secret_keys = nonsensitive(toset([for k, v in local.groundswell_secrets : k]))

  wave_lite_secrets     = jsondecode(data.aws_ssm_parameter.wave_lite_secrets.value)
  wave_lite_secret_keys = nonsensitive(toset([for k, v in local.wave_lite_secrets : k]))


  # SSH
  # ---------------------------------------------------------------------------------------
  ssh_key_name = "ssh_key_for_${local.global_prefix}.pem"


  # DNS
  # ---------------------------------------------------------------------------------------
  # All values here refer to Route53 in same AWS account as Tower instance.
  # If R53 record not generated, will create entry in EC2 hosts file.
  dns_create_alb_record = var.flag_create_load_balancer == true && var.flag_create_hosts_file_entry == false ? true : false
  dns_create_ec2_record = var.flag_create_load_balancer == false && var.flag_create_hosts_file_entry == false ? true : false

  dns_zone_id = (
    var.flag_create_route53_private_zone == true ? aws_route53_zone.private[0].id :
    var.flag_use_existing_route53_public_zone == true ? data.aws_route53_zone.public[0].id :
    var.flag_use_existing_route53_private_zone == true ? data.aws_route53_zone.private[0].id :
    "No_Match_Found"
  )

  dns_instance_ip = (
    var.flag_make_instance_private == true ? aws_instance.ec2.private_ip :
    var.flag_make_instance_private_behind_public_alb == true ? aws_instance.ec2.private_ip :
    var.flag_private_tower_without_eice == true ? aws_instance.ec2.private_ip :
    var.flag_make_instance_public == true ? aws_eip.towerhost[0].public_ip :
    "No_Match_Found"
  )


  # Security Groups
  # ---------------------------------------------------------------------------------------
  # All module values wrapped in [] to make concat work.
  # NOTE: If you add a new entry, dont forget to add it to the concat block too!
  sg_ec2_core                           = [module.sg_ec2_core.security_group_id]
  sg_ec2_noalb_with_private_certificate = try([module.sg_ec2_noalb_with_private_certificate[0].security_group_id], [])
  sg_ec2_noalb_no_https                 = try([module.sg_ec2_noalb_no_https[0].security_group_id], [])
  sg_ec2_noalb_connect                  = try([module.sg_ec2_noalb_connect[0].security_group_id], [])
  sg_from_alb_core                      = try([module.sg_from_alb_core[0].security_group_id], [])
  sg_from_alb_connect                   = try([module.sg_from_alb_connect[0].security_group_id], [])
  sg_from_alb_wave                      = try([module.sg_from_alb_wave[0].security_group_id], [])
  # Studios SSH — see 002_security_groups.tf for why two separate rules are needed
  # (one for direct EC2 access, one for NLB path; NLBs don't have security groups
  # so both use CIDR-based rules rather than source_security_group_id)
  sg_ec2_noalb_ssh = try([module.sg_ec2_noalb_ssh[0].security_group_id], [])
  sg_from_nlb_ssh  = try([module.sg_from_nlb_ssh[0].security_group_id], [])

  sg_ec2_final = concat(
    local.sg_ec2_core,
    local.sg_ec2_noalb_with_private_certificate,
    local.sg_ec2_noalb_no_https,
    local.sg_ec2_noalb_connect,
    local.sg_from_alb_core,
    local.sg_from_alb_connect,
    local.sg_from_alb_wave,
    local.sg_ec2_noalb_ssh,
    local.sg_from_nlb_ssh,

  )
  ec2_sg_final_raw = join(",", [for sg in local.sg_ec2_final : jsonencode(sg)]) # Needed?


  # ALB - Determine which CIDR Blocks to attach to allowed ports
  # `var.sg_ingress_cidrs` is added to `alb_ingress_cidrs` no matter what because it's possible other IP ranges need to have access to the network.
  alb_public_access    = var.flag_make_instance_public == true || var.flag_make_instance_private_behind_public_alb == true ? var.sg_ingress_cidrs : []
  alb_private_new      = var.flag_make_instance_private == true && var.flag_create_new_vpc == true ? [var.vpc_new_cidr_range] : []
  alb_private_existing = var.flag_make_instance_private == true && var.flag_use_existing_vpc == true ? [data.aws_vpc.preexisting[0].cidr_block] : []
  alb_private_no_eice  = var.flag_private_tower_without_eice == true && var.flag_use_existing_vpc == true ? [data.aws_vpc.preexisting[0].cidr_block] : []

  alb_ingress_cidrs = distinct(concat(
    var.sg_ingress_cidrs,
    local.alb_public_access,
    local.alb_private_new,
    local.alb_private_existing,
    local.alb_private_no_eice
  ))

  # MAY 16/2025 -- KEEP THIS UNTIL REWRITTEN LOGIC IS CONFIRMED
  # alb_ingress_cidrs = (
  #   var.flag_make_instance_public == true || var.flag_make_instance_private_behind_public_alb == true ? var.sg_ingress_cidrs :
  #   var.flag_make_instance_private == true && var.flag_create_new_vpc == true ? distinct(concat([var.vpc_new_cidr_range], var.sg_ingress_cidrs)):
  #   var.flag_make_instance_private == true && var.flag_use_existing_vpc == true ? distinct(concat([data.aws_vpc.preexisting.cidr_block], var.sg_ingress_cidrs)) :
  #   var.flag_private_tower_without_eice == true && var.flag_use_existing_vpc == true ? distinct(concat([data.aws_vpc.preexisting.cidr_block], var.sg_ingress_cidrs)) :
  #   ["No CIDR block found"]
  # )


  # Database
  # ---------------------------------------------------------------------------------------
  # If creating new RDS, get address from TF. IF using existing RDS, get address from user.
  populate_external_db = var.flag_create_external_db == true || var.flag_use_existing_external_db == true ? "true" : "false"

  # Active DB engine version: container engine if container DB in use, else RDS engine.
  # Fed into the connection_strings module to select the correct JDBC suffix.
  db_engine = var.flag_use_container_db ? var.db_container_engine_version : var.db_engine_version


  # OIDC
  # ---------------------------------------------------------------------------------------
  # If flags are set, populate local with keyword for MICRONAUT_ENVIRONMENTS inclusion. If not, blank string.
  oidc_auth         = var.flag_oidc_use_generic == true ? "auth-oidc" : ""
  oidc_google       = var.flag_oidc_use_google == true ? "auth-google" : ""
  oidc_github       = var.flag_oidc_use_github == true ? "auth-github" : ""
  oidc_consolidated = "${local.oidc_auth},${local.oidc_google},${local.oidc_github}"


  # Wave
  # ---------------------------------------------------------------------------------------
  wave_enabled              = var.flag_use_wave == true || var.flag_use_wave_lite == true ? true : false
  wave_lite_redis_container = var.flag_use_wave_lite == true && var.flag_create_external_redis == true ? false : true
  wave_lite_db_container    = var.flag_use_wave_lite == true && var.flag_create_external_db == true ? false : true


  # Private CA Files
  # ---------------------------------------------------------------------------------------
  private_ca_cert = "${module.connection_strings.tower_base_url}.crt"
  private_ca_key  = "${module.connection_strings.tower_base_url}.key"


  # Miscellaneous
  # ---------------------------------------------------------------------------------------
  # These are needed to handle templatefile rendering to Bash echoing to file craziness.
  dollar      = "$"
  singlequote = "'"


  # Ansible
  # ---------------------------------------------------------------------------------------
  playbook_dir = "/home/ec2-user/target/ansible"


  # connection_strings (cs_*)
  # ---------------------------------------------------------------------------------------
  cs_platform_security_mode = (
    var.flag_do_not_use_https ? "insecure" :
    "secure"
  )

  # Deployment intent (use_mocks is orthogonal — handled inside module via var.use_mocks).
  cs_platform_db_deployment = (
    var.flag_use_container_db ? "container" :
    var.flag_create_external_db ? "new" :
    var.flag_use_existing_external_db ? "existing" :
    "unknown"
  )

  cs_platform_redis_deployment = (
    var.flag_use_container_redis ? "container" :
    var.flag_create_external_redis ? "new" :
    "unknown"
  )

  # Studios requires HTTPS — flag_do_not_use_https blocks studios entirely.
  cs_studio_mode = (
    !var.flag_enable_data_studio || var.flag_do_not_use_https ? "disabled" :
    var.flag_studio_enable_path_routing ? "path" :
    "subdomain"
  )

  # Wave-Lite requires HTTPS; Wave (Seqera-hosted) does not.
  cs_wave_mode = (
    var.flag_use_wave_lite && !var.flag_do_not_use_https ? "wave-lite" :
    var.flag_use_wave ? "wave" :
    "disabled"
  )

  cs_studio_ssh_mode  = var.flag_enable_data_studio_ssh ? "enabled" : "disabled"
  cs_groundswell_mode = var.flag_enable_groundswell ? "enabled" : "disabled"

  platform_existing_db_url = var.flag_use_existing_external_db ? var.tower_db_url : "N/A"

}


# Add connection_strings module.
#
# Two-layer defense on resource-attribute inputs (see #353 addendum)
# -----------------------------------------------------------------------------
# Every input below that references a resource or downstream module is wrapped in:
#
#     <input> = var.use_mocks ? null : try(<resource_or_module_ref>, null)
#
# This pattern is load-bearing for the test framework's "console-without-plan"
# fast path. Specifically:
#
#   1. `var.use_mocks = true` is set by `tests/datafiles/generate_core_data.sh`
#      for every test run. The ternary's selected branch becomes the literal
#      `null` — fully resolvable under `terraform console` with no resources
#      in state.
#   2. HCL evaluates BOTH ternary branches eagerly. So the unselected branch
#      (`try(<ref>, null)`) is also evaluated. The `try()` wrapper catches the
#      evaluation error that occurs when the referenced module/resource has
#      not been applied (and therefore doesn't exist in state) and substitutes
#      `null`. Without `try()`, console would fail outright; without
#      `var.use_mocks`, the unknown-resource value would propagate into the
#      module and poison its outputs to "(known after apply)".
#
# The end result: `terraform console` can evaluate `module.connection_strings`
# in test contexts without ever needing `terraform plan` — which is what makes
# the ~30s-per-cold-cache speedup in the templatefile test path possible.
#
# MAINTENANCE RULE: any newly added resource-attribute input to this module
# (or any module the test framework expects to evaluate via console) MUST follow
# the same `var.use_mocks ? null : try(<ref>, null)` shape. Skipping either the
# `use_mocks` gate or the `try()` wrapper reintroduces a "(known after apply)"
# value into the module's input, which propagates to its outputs, which collapses
# the console fast path for any consumer that touches the unguarded input. The
# regression linter in tests/unit/framework/ catches this at PR time, but the
# convention is what prevents the failure in the first place.
#
# See also: documentation/design_decisions.md (decision #18 in the addendum
# under "console-based templatefile evaluation") and proj:testing_strategy.md
# for the broader rationale and contributor guidance.
module "connection_strings" {
  source = "./modules/connection_strings/v2.0.0"

  # Mode strings (caller resolves user-facing flags into modes)
  platform_security_mode    = local.cs_platform_security_mode
  platform_db_deployment    = local.cs_platform_db_deployment
  platform_redis_deployment = local.cs_platform_redis_deployment
  studio_mode               = local.cs_studio_mode
  wave_mode                 = local.cs_wave_mode
  studio_ssh_mode           = local.cs_studio_ssh_mode
  groundswell_mode          = local.cs_groundswell_mode

  # Tower core
  tower_server_url         = var.tower_server_url
  platform_existing_db_url = local.platform_existing_db_url
  platform_db_schema_name  = var.db_database_name
  platform_db_engine       = local.db_engine

  # Per-component values
  data_studio_path_routing_url = var.data_studio_path_routing_url
  swell_database_name          = var.swell_database_name
  wave_server_url              = var.wave_server_url

  # External resource references — two-layer defense (see header comment above).
  rds_tower             = var.use_mocks ? null : try(module.rds[0], null)
  rds_wave_lite         = var.use_mocks ? null : try(module.rds-wave-lite[0], null)
  elasticache_tower     = var.use_mocks ? null : try(aws_elasticache_cluster.redis[0], null)
  elasticache_wave_lite = var.use_mocks ? null : try(module.elasticache_wave_lite[0], null)

  # Orthogonal mock toggle: swaps "new" deployment hosts to mock strings without changing intent.
  use_mocks = var.use_mocks
}

# Add subnet_collector module.
# Testing Note: For quick config testins, use existing VPC to bypass VPC asset generation.
module "subnet_collector" {
  source = "./modules/subnet_collector/v1.0.0"

  create_new_vpc = var.flag_create_new_vpc
  vpc_id         = local.vpc_id
  vpc_module     = var.flag_create_new_vpc ? module.vpc[0] : null

  # Define subnet lists based on VPC creation mode
  subnets_ec2   = var.flag_create_new_vpc ? var.vpc_new_ec2_subnets : var.vpc_existing_ec2_subnets
  subnets_batch = var.flag_create_new_vpc ? var.vpc_new_batch_subnets : var.vpc_existing_batch_subnets
  subnets_db    = var.flag_create_new_vpc ? var.vpc_new_db_subnets : var.vpc_existing_db_subnets
  subnets_redis = var.flag_create_new_vpc ? var.vpc_new_redis_subnets : var.vpc_existing_redis_subnets
  subnets_alb   = var.flag_create_new_vpc ? var.vpc_new_alb_subnets : var.vpc_existing_alb_subnets

  # Testing flag
  use_mocks = var.use_mocks
}
