## ------------------------------------------------------------------------------------
## NOTE!
## ------------------------------------------------------------------------------------
/* 1. Modules rewritten May 15/2025 (combined ingress & egress).

   2. Config entries like `ingress_with_cidr_blocks` require comma-delimited string, 
      whereas other config entries like `egress_rules` expect a list.

      To be reverse-compatible with existing installations, I've left tfvars keys as lists
      and process as required within each module call.
*/


## ------------------------------------------------------------------------------------
## Instance Connect Endpoint Controls
## ------------------------------------------------------------------------------------
module "sg_eice" {
  source            = "terraform-aws-modules/security-group/aws"
  version           = "5.1.0"

  name              = "${local.global_prefix}_eice_sg"
  description       = "EICE traffic."

  vpc_id            = local.vpc_id
  ingress_with_cidr_blocks = [
    {
      rule          = "ssh-tcp"
      cidr_blocks   = join(",", var.sg_ssh_cidrs)
    }
  ]
  egress_rules      = var.sg_egress_eice
}


## ------------------------------------------------------------------------------------
## EC2 Controls
## ------------------------------------------------------------------------------------
module "sg_ec2_core" {
  source            = "terraform-aws-modules/security-group/aws"
  version           = "5.1.0"

  name              = "${local.global_prefix}_ec2_core"
  description       = "Core EC2 traffic (SSH & Egress)."

  vpc_id            = local.vpc_id
  ingress_with_cidr_blocks = [
    {
      rule          = "ssh-tcp"
      cidr_blocks   = join(",", var.sg_ssh_cidrs)
    }
  ]
  egress_rules      = var.sg_egress_tower_ec2

}


# May 15/2025
# Keeping these three rules separate so that we dont unnecessarily open Ports if they aren't needed.
# This means the code is a bit more complicated than I would like, but seems worth it for security.
module "sg_ec2_direct" {
  source              = "terraform-aws-modules/security-group/aws"
  version             = "5.1.0"

  count               = var.flag_create_load_balancer == false ? 1 : 0

  name                = "${local.global_prefix}_ec2_direct"
  description         = "Direct HTTP traffic to EC2."

  vpc_id              = local.vpc_id
  ingress_cidr_blocks = var.sg_ingress_cidrs
  ingress_rules       = ["https-443-tcp", "http-80-tcp", "splunk-web-tcp"]
}


module "sg_ec2_direct_connect" {
  source                    = "terraform-aws-modules/security-group/aws"
  version                   = "5.1.0"

  count                     = var.flag_enable_data_studio == true ? 1 : 0

  name                      = "${local.global_prefix}_ec2_direct_connect"
  description               = "Direct HTTP to Tower EC2 host when Connect active."

  vpc_id                    = local.vpc_id
  ingress_with_cidr_blocks  = local.sg_ec2_direct_connect_final
}


module "sg_ec2_alb" {
  source                    = "terraform-aws-modules/security-group/aws"
  version                   = "5.1.0"

  count                     = var.flag_create_load_balancer == true ? 1 : 0

  name                      = "${local.global_prefix}_ec2_alb"
  description               = "ALB HTTP traffic to EC2."

  vpc_id                    = local.vpc_id
  computed_ingress_with_source_security_group_id = [
    {
      rule                     = "splunk-web-tcp"
      source_security_group_id = module.sg_alb_core[0].security_group_id
    }
  ]
  number_of_computed_ingress_with_source_security_group_id = 1
}


## ------------------------------------------------------------------------------------
## ALB Controls
## ------------------------------------------------------------------------------------
module "sg_alb_core" {
  source                    = "terraform-aws-modules/security-group/aws"
  version                   = "5.1.0"

  count                     = var.flag_create_load_balancer == true ? 1 : 0

  name                      = "${local.global_prefix}_alb"
  description               = "Allow HTTP & HTTPS to ALB."

  vpc_id                    = local.vpc_id
  ingress_cidr_blocks       = local.alb_ingress_cidrs
  ingress_rules             = ["https-443-tcp", "http-80-tcp"]
  egress_rules              = var.sg_egress_tower_alb
}


module "sg_alb_connect" {
  source                    = "terraform-aws-modules/security-group/aws"
  version                   = "5.1.0"

  count                     = var.flag_create_load_balancer == true && var.flag_enable_data_studio == true ? 1 : 0

  name                      = "${local.global_prefix}_alb_connect"
  description               = "Allow Connect Proxy traffic to ALB."

  vpc_id                    = local.vpc_id
  computed_ingress_with_source_security_group_id= local.sg_alb_connect_final
  number_of_computed_ingress_with_source_security_group_id = 1
}


# Wave Lite only currently supported via ALB
module "sg_alb_wave" {
  source                    = "terraform-aws-modules/security-group/aws"
  version                   = "5.1.0"

  count                     = var.flag_create_load_balancer == true && var.flag_use_wave_lite == true ? 1 : 0

  name                      = "${local.global_prefix}_alb_wave"
  description               = "Allow Wave Lite traffic to ALB."

  vpc_id                    = local.vpc_id
  computed_ingress_with_source_security_group_id= local.sg_alb_wave_final
  number_of_computed_ingress_with_source_security_group_id = 1
}


## ------------------------------------------------------------------------------------
## DB Controls
## ------------------------------------------------------------------------------------
module "sg_db" {
  source                    = "terraform-aws-modules/security-group/aws"
  version                   = "5.1.0"

  count                     = var.flag_create_external_db == true ? 1 : 0

  name                      = "${local.global_prefix}_rds"
  description               = "Seqera Platform RDS traffic."

  vpc_id                    = local.vpc_id
  computed_ingress_with_source_security_group_id = [
    {
      rule                     = "mysql-tcp"
      source_security_group_id = module.sg_ec2_core.security_group_id
    },
    {
      rule                     = "postgresql-tcp"
      source_security_group_id = module.sg_ec2_core.security_group_id
    }
  ]
  # TODO: Decide whether 
  number_of_computed_ingress_with_source_security_group_id = 2
}


## ------------------------------------------------------------------------------------
## AWS Batch Security Groups
## ------------------------------------------------------------------------------------
module "sg_batch" {
  source                      = "terraform-aws-modules/security-group/aws"
  version                     = "5.1.0"

  name                        = "${local.global_prefix}_batch"
  description                 = "Security group for Tower Batch instance."

  vpc_id                      = local.vpc_id
  computed_ingress_with_source_security_group_id = [
    {
      rule                     = "ssh-tcp"
      source_security_group_id = module.sg_ec2_core.security_group_id
    }
  ]
  number_of_computed_ingress_with_source_security_group_id = 1
  egress_rules                = var.sg_egress_batch_ec2
}


## ------------------------------------------------------------------------------------
## Elasticache (Redis) Controls
## ------------------------------------------------------------------------------------
module "sg_redis" {
  source                      = "terraform-aws-modules/security-group/aws"
  version                     = "5.1.0"

  count                       = var.flag_create_external_redis == true ? 1 : 0

  name                        = "${local.global_prefix}_redis"
  description                 = "Seqera Platform Redis traffic."

  vpc_id                      = local.vpc_id
  computed_ingress_with_source_security_group_id = [
    {
      rule                     = "redis-tcp"
      source_security_group_id = module.sg_ec2_core.security_group_id
    }
  ]
  number_of_computed_ingress_with_source_security_group_id = 1
}


## ------------------------------------------------------------------------------------
## Gateway & Interface Endpoint Controls
## ------------------------------------------------------------------------------------
module "sg_vpc_endpoint" {
  source                      = "terraform-aws-modules/security-group/aws"
  version                     = "5.1.0"

  name                        = "${local.global_prefix}_vpc_interface"
  description                 = "Seqera Platform VPC Endpoint traffic."

  vpc_id                      = local.vpc_id
  ingress_cidr_blocks         = [var.vpc_new_cidr_range]
  ingress_rules               = ["all-all"]
  egress_rules                = var.sg_egress_interface_endpoint
}
