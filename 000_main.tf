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

  sg_ec2_final = concat(
    local.sg_ec2_core,
    local.sg_ec2_noalb_with_private_certificate,
    local.sg_ec2_noalb_no_https,
    local.sg_ec2_noalb_connect,
    local.sg_from_alb_core,
    local.sg_from_alb_connect,
    local.sg_from_alb_wave,

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


  # OIDC
  # ---------------------------------------------------------------------------------------
  # If flags are set, populate local with keyword for MICRONAUT_ENVIRONMENTS inclusion. If not, blank string.
  oidc_auth         = var.flag_oidc_use_generic == true ? "auth-oidc" : ""
  oidc_google       = var.flag_oidc_use_google == true ? "auth-google" : ""
  oidc_github       = var.flag_oidc_use_github == true ? "auth-github" : ""
  oidc_consolidated = "${local.oidc_auth},${local.oidc_google},${local.oidc_github}"


  # Studios
  # ---------------------------------------------------------------------------------------
  # Note: This is an ugly way to check but aligns to how I already check for migrate_db.
  # TODO: Refactor in v2.
  studio_uses_distroless = (
    tonumber(length(regexall("^0.7.[8-9]", var.data_studio_container_version))) >= 1 ||
    tonumber(length(regexall("^0.[8-9].[0-9]", var.data_studio_container_version))) >= 1 ? true : false
  )


  # Wave
  # ---------------------------------------------------------------------------------------
  wave_enabled              = var.flag_use_wave == true || var.flag_use_wave_lite == true ? true : false
  wave_lite_redis_container = var.flag_use_wave_lite == true && var.flag_create_external_redis == true ? false : true
  wave_lite_db_container    = var.flag_use_wave_lite == true && var.flag_create_external_db == true ? false : true


  # Private CA Files
  # ---------------------------------------------------------------------------------------
  private_ca_cert       = "${module.connection_strings.tower_base_url}.crt"
  private_ca_key        = "${module.connection_strings.tower_base_url}.key


  # Private CA Files
  # ---------------------------------------------------------------------------------------
  private_ca_cert = "${module.connection_strings.tower_base_url}.crt"
  private_ca_key  = "${module.connection_strings.tower_base_url}.key"


  # Miscellaneous
  # ---------------------------------------------------------------------------------------
  # These are needed to handle templatefile rendering to Bash echoing to file craziness.
  dollar      = "$"
  singlequote = "'"

    
  # Migrate-DB Flag
  # ---------------------------------------------------------------------------------------
  # Migrate-db only available for 23.4.1+ or higher. Check to ensure we don't include for 23.3.x or below. 
  # TODO: Rationalize this to a single regex (July 26/25)
  flag_new_enough_for_migrate_db = (
    tonumber(length(regexall("^v23.4.[1-9]", var.tower_container_version))) >= 1 ||
    tonumber(length(regexall("^v2[4-9]", var.tower_container_version))) >= 1 ? true : false
  )

  # Account for changes in tower.yml due to Micronaut 4
  flag_using_micronaut_4 = (
    tonumber(length(regexall("^v24.[0-9]", var.tower_container_version))) >= 1 ||
    tonumber(length(regexall("^v2[5-9]", var.tower_container_version))) >= 1 ? true : false
  )

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
}

# Add connection_strings module
module "connection_strings" {
  source = "./modules/connection_strings/v1.0.0"

  # Feature Flags
  flag_create_load_balancer       = var.flag_create_load_balancer
  flag_do_not_use_https           = var.flag_do_not_use_https
  flag_create_external_db         = var.flag_create_external_db
  flag_use_existing_external_db   = var.flag_use_existing_external_db
  flag_create_external_redis      = var.flag_create_external_redis
  flag_use_wave                   = var.flag_use_wave
  flag_use_wave_lite              = var.flag_use_wave_lite
  flag_studio_enable_path_routing = var.flag_studio_enable_path_routing

  # Tower Configuration
  tower_server_url = var.tower_server_url
  tower_db_url     = var.flag_use_existing_external_db == true ? var.tower_db_url : ""
  db_database_name = var.db_database_name

  # Groundswell Configuration
  swell_database_name = var.swell_database_name

  # Wave Configuration
  wave_server_url              = var.flag_use_wave ? var.wave_server_url : "https://wave.seqera.io"
  wave_lite_server_url         = var.flag_use_wave_lite ? var.wave_lite_server_url : ""
  data_studio_path_routing_url = var.flag_studio_enable_path_routing ? var.data_studio_path_routing_url : ""

  # External Resource References
  rds_tower             = var.flag_create_external_db ? try(module.rds[0], null) : null
  rds_wave_lite         = var.flag_create_external_db ? try(module.rds-wave-lite[0], null) : null
  elasticache_tower     = var.flag_create_external_redis ? try(aws_elasticache_cluster.redis[0], null) : null
  elasticache_wave_lite = var.flag_create_external_redis ? try(module.elasticache_wave_lite[0], null) : null

  # Testing flag
  use_mocks = var.use_mocks

}
