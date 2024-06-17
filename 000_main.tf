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


data "aws_caller_identity" "current" {}

data "aws_vpc" "preexisting" { 
  id = local.vpc_id 
}

# https://stackoverflow.com/questions/67562197/terraform-loop-through-ids-list-and-generate-data-blocks-from-it-and-access-it
data "aws_subnet" "existing" {
  # Creates a map with the keys being the CIDRs --  e.g. `data.aws_subnet.public["10.0.0.0/20"].id
  for_each = toset(local.subnets_all)
  vpc_id     = local.vpc_id
  cidr_block = each.key
}

# https://medium.com/@leslie.alldridge/terraform-external-data-source-using-custom-python-script-with-example-cea5e618d83e
data "external" "generate_db_connection_string" {
  program = ["python3", "${path.module}/.githooks/data_external/generate_db_connection_string.py"]
  query = {}
}

data "external" "generate_flags" {
  program = ["python3", "${path.module}/.githooks/data_external/generate_flags.py"]
  query = {}
}

data "external" "generate_dns_values" {
  program = ["python3", "${path.module}/.githooks/data_external/generate_dns_values.py"]
  query = {
    # jsonencoding necessary for empty objects
    zone_private_new          = jsonencode(aws_route53_zone.private)
    zone_private_existing     = jsonencode(data.aws_route53_zone.private)
    zone_public_existing      = jsonencode(data.aws_route53_zone.public)

    tower_host_instance       = jsonencode(aws_instance.ec2)
    tower_host_eip            = jsonencode(aws_eip.towerhost)

    # subnets = data.aws_subnet.existing          # Adding in these values wont be known til created.
    # ec2 = jsonencode(aws_instance.ec2)                     # Adding in these values wont be known til created.
  }
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
  vpc_id = var.flag_create_new_vpc == true ? module.vpc[0].vpc_id : var.vpc_existing_id

  vpc_private_route_table_ids = data.aws_route_tables.preexisting.ids

  # Map CIDR blocks to subnet IDs (depending on tf resource, either/or needed). 
  # Cant delegate this to Python due to need to make multiple data calls.
  subnets_ec2   = var.flag_create_new_vpc == true ? var.vpc_new_ec2_subnets   : var.vpc_existing_ec2_subnets
  subnets_batch = var.flag_create_new_vpc == true ? var.vpc_new_batch_subnets : var.vpc_existing_batch_subnets
  subnets_db    = var.flag_create_new_vpc == true ? var.vpc_new_db_subnets    : var.vpc_existing_db_subnets
  subnets_redis = var.flag_create_new_vpc == true ? var.vpc_new_redis_subnets : var.vpc_existing_redis_subnets
  subnets_alb   = var.flag_create_new_vpc == true ? var.vpc_new_alb_subnets   : var.vpc_existing_alb_subnets
  subnets_all   = concat(local.subnets_ec2, local.subnets_batch, local.subnets_db, local.subnets_redis, local.subnets_alb)

  subnet_ids_ec2    = [for cidr in local.subnets_ec2 : data.aws_subnet.existing[cidr].id]
  subnet_ids_batch  = [for cidr in local.subnets_batch : data.aws_subnet.existing[cidr].id]
  subnet_ids_db     = [for cidr in local.subnets_db : data.aws_subnet.existing[cidr].id]
  subnet_ids_redis  = [for cidr in local.subnets_redis : data.aws_subnet.existing[cidr].id]
  subnet_ids_alb    = (var.flag_create_load_balancer == true ? 
    [for cidr in local.subnets_alb : data.aws_subnet.existing[cidr].id] : []
  )


  # SSM
  # ---------------------------------------------------------------------------------------
  # Load bootstrapped secrets and define target for TF-generated SSM values. Magical - don't know why it works but it does.
  ssm_root = "/config/{$var.app_name}"

  tower_secrets     = jsondecode(data.aws_ssm_parameter.tower_secrets.value)
  tower_secret_keys = nonsensitive(toset([for k, v in local.tower_secrets : k]))

  seqerakit_secrets     = jsondecode(data.aws_ssm_parameter.seqerakit_secrets.value)
  seqerakit_secret_keys = nonsensitive(toset([for k, v in local.seqerakit_secrets : k]))

  groundswell_secrets     = jsondecode(data.aws_ssm_parameter.groundswell_secrets.value)
  groundswell_secret_keys = nonsensitive(toset([for k, v in local.groundswell_secrets : k]))


  # SSH
  # ---------------------------------------------------------------------------------------
  ssh_key_name = "ssh_key_for_${local.global_prefix}.pem"


  # DNS
  # ---------------------------------------------------------------------------------------
  # All values here refer to Route53 in same AWS account as Tower instance.
  # If R53 record not generated, will create entry in EC2 hosts file.
  dns_create_alb_record = jsondecode(data.external.generate_flags.result.dns_create_alb_record)
  dns_create_ec2_record = jsondecode(data.external.generate_flags.result.dns_create_ec2_record)

  dns_zone_id           = data.external.generate_dns_values.result.dns_zone_id
  dns_instance_ip       = data.external.generate_dns_values.result.dns_instance_ip


  # If no HTTPS and no load-balancer, use `http` prefix and expose port in URL. Otherwise, use `https` prefix and no port.
  tower_server_url = (
    var.flag_create_load_balancer == false && var.flag_do_not_use_https == true ?
    "http://${var.tower_server_url}:${var.tower_server_port}" :
    "https://${var.tower_server_url}"
  )

  tower_base_url     = var.tower_server_url
  tower_api_endpoint = "${local.tower_server_url}/api"


  # Security Groups
  # ---------------------------------------------------------------------------------------
  # Always grant egress anywhere & SSH ingress to EC2 instance. 
  # Add additional ingress restrictions depending on whether ALB is created or not.
  ec2_sg_start = [
    module.tower_ec2_egress_sg.security_group_id,
    module.tower_ec2_ssh_sg.security_group_id
  ]

  ec2_sg_final = (
    var.flag_create_load_balancer == true ?
    concat(local.ec2_sg_start, [module.tower_ec2_alb_sg.security_group_id]) :
    concat(local.ec2_sg_start, [module.tower_ec2_direct_sg.security_group_id])
  )

  ec2_sg_final_raw = join(",", [for sg in local.ec2_sg_final : jsonencode(sg)])

  alb_ingress_cidrs = (
    var.flag_make_instance_public == true || var.flag_make_instance_private_behind_public_alb == true ? var.sg_ingress_cidrs :
    var.flag_make_instance_private == true && var.flag_create_new_vpc == true ? [var.vpc_new_cidr_range] :
    var.flag_make_instance_private == true && var.flag_use_existing_vpc == true ? [data.aws_vpc.preexisting.cidr_block] :
    var.flag_private_tower_without_eice == true && var.flag_use_existing_vpc == true ? [data.aws_vpc.preexisting.cidr_block] :
    # DELETE THIS
    var.flag_private_tower_without_eice == true && var.flag_create_new_vpc == true ? [data.aws_vpc.preexisting.cidr_block] :
    ["No CIDR block found"]
  )


  # Database
  # ---------------------------------------------------------------------------------------
  # If creating new RDS, get address from TF. IF using existing RDS, get address from user. 
  populate_external_db = var.flag_create_external_db == true || var.flag_use_existing_external_db == true ? "true" : "false"

  # tower_db_url = var.flag_create_external_db == true ? module.rds[0].db_instance_address : var.tower_db_url
  tower_db_root = ( var.flag_use_container_db == true? var.tower_db_url : module.rds[0].db_instance_address )
  tower_db_url = "${local.tower_db_root}/${var.db_database_name}${data.external.generate_db_connection_string.result.connection_string}"


  # Redis
  # ---------------------------------------------------------------------------------------
  tower_redis_url = (
    var.flag_create_external_redis == true ?
    "redis://${aws_elasticache_cluster.redis[0].cache_nodes[0].address}:${aws_elasticache_cluster.redis[0].cache_nodes[0].port}" :
    "redis://redis:6379"
  )

  # Docker-Compose
  # ---------------------------------------------------------------------------------------
  docker_compose_file = (
    var.flag_use_custom_docker_compose_file == false && var.flag_use_container_db == true ? "dc_with_db.yml" :
    var.flag_use_custom_docker_compose_file == false && var.flag_use_container_db == false ? "dc_without_db.yml" :
    var.flag_use_custom_docker_compose_file == true ? "dc_custom.yml" : "No_Match_Found"
  )


  # OIDC
  # ---------------------------------------------------------------------------------------
  # If flags are set, populate local with keyword for MICRONAUT_ENVIRONMENTS inclusion. If not, blank string.
  oidc_auth   = var.flag_oidc_use_generic == true || var.flag_oidc_use_google == true ? ",auth-oidc" : ""
  oidc_github = var.flag_oidc_use_github == true ? ",auth-github" : ""


  # Miscellaneous
  # ---------------------------------------------------------------------------------------
  # These are needed to handle templatefile rendering to Bash echoing to file craziness.
  dollar      = "$"
  singlequote = "'"

    # Migrate-DB Flag
  # ---------------------------------------------------------------------------------------
  # Migrate-db only available for 23.4.1+ or higher. Check to ensure we don't include for 23.3.x or below. 
  flag_new_enough_for_migrate_db = (
    tonumber(length(regexall("^v23.4.[1-9]", var.tower_container_version))) >= 1 || 
      tonumber(length(regexall("^v2[4-9]", var.tower_container_version))) >= 1 ? true : false
  )
}