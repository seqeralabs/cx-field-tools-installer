## ------------------------------------------------------------------------------------
## NOTE!
## ------------------------------------------------------------------------------------
/* 1. Modules rewritten May 15/2025 (combined ingress & egress).

   2. Config entries like `ingress_with_cidr_blocks` require comma-delimited string, 
      whereas other config entries like `egress_rules` expect a list.

      To be reverse-compatible with existing installations, I've left tfvars keys as lists
      and process as required within each module call.

      For good config examples, see: https://github.com/terraform-aws-modules/terraform-aws-security-group/blob/master/examples/complete/main.tf

   3. Nuanced distinction between `sg_ec2_core` vs `sg_ec2_noalb` vs `sg_from_alb_`:
        - sg_ec2_core     :  Rules that need to be present regardless of how traffic gets to it (inbound SSH & egress)
        - sg_ec2_noalb_*  :  Rules that allow inbound traffic directly to the EC2 instance when an ALB has not been deployed.
        - sg_from_alb_*   :  Rules that allow inbound traffic from the ALB when the ALB is deployed.
*/


## ------------------------------------------------------------------------------------
## Instance Connect Endpoint Controls
## ------------------------------------------------------------------------------------
module "sg_eice" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  name        = "${local.global_prefix}_eice_sg"
  description = "EICE traffic."

  vpc_id = local.vpc_id
  ingress_with_cidr_blocks = [
    {
      rule        = "ssh-tcp"
      cidr_blocks = join(",", var.sg_ssh_cidrs)
    }
  ]
  egress_rules = var.sg_egress_eice
}


## ------------------------------------------------------------------------------------
## EC2 Controls
## ------------------------------------------------------------------------------------
module "sg_ec2_core" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  name        = "${local.global_prefix}_ec2_core"
  description = "Core EC2 traffic (SSH & Egress)."

  vpc_id = local.vpc_id
  ingress_with_cidr_blocks = [
    {
      rule        = "ssh-tcp"
      cidr_blocks = join(",", var.sg_ssh_cidrs)
    }
  ]
  egress_rules = var.sg_egress_tower_ec2

}


# May 15/2025
# Keeping these three rules separate so that we dont unnecessarily open Ports if they aren't needed.
# This means the code is a bit more complicated than I would like, but seems worth it for security.
module "sg_ec2_noalb" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  count = var.flag_create_load_balancer ? 1 : 0

  name        = "${local.global_prefix}_ec2_direct"
  description = "Direct HTTP (80, 443, and 8000) traffic to EC2."

  vpc_id              = local.vpc_id
  ingress_cidr_blocks = var.sg_ingress_cidrs
  ingress_rules       = ["https-443-tcp", "http-80-tcp", "splunk-web-tcp"]
}


module "sg_ec2_noalb_connect" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  count = !var.flag_create_load_balancer && var.flag_enable_data_studio ? 1 : 0

  name        = "${local.global_prefix}_ec2_direct_connect"
  description = "Direct HTTP (9090) traffic to EC2."

  vpc_id = local.vpc_id
  computed_ingress_with_cidr_blocks = [
    {
      from_port   = 9090
      to_port     = 9090
      protocol    = "tcp"
      description = "Connect-Proxy"
      cidr_blocks = join(",", var.sg_ingress_cidrs)
    }
  ]
  number_of_computed_ingress_with_source_security_group_id = 1
}


module "sg_from_alb_core" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  count = var.flag_create_load_balancer ? 1 : 0

  name        = "${local.global_prefix}_from_alb_core"
  description = "Allow HTTP (8000) traffic via ALB."

  vpc_id = local.vpc_id
  computed_ingress_with_source_security_group_id = [
    {
      rule                     = "splunk-web-tcp"
      source_security_group_id = module.sg_alb_core[0].security_group_id
    }
  ]
  number_of_computed_ingress_with_source_security_group_id = 1
}



module "sg_from_alb_connect" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  count = var.flag_create_load_balancer && var.flag_enable_data_studio ? 1 : 0

  name        = "${local.global_prefix}_from_alb_connect"
  description = "Allow Studio traffic via ALB."

  vpc_id = local.vpc_id
  computed_ingress_with_source_security_group_id = [
    {
      from_port                = 9090
      to_port                  = 9090
      protocol                 = "tcp"
      description              = "Studio"
      source_security_group_id = module.sg_alb_core[0].security_group_id
    }
  ]
  number_of_computed_ingress_with_source_security_group_id = 1
}


# Wave Lite only currently supported via ALB
module "sg_from_alb_wave" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  count = var.flag_create_load_balancer && var.flag_use_wave_lite ? 1 : 0

  name        = "${local.global_prefix}_from_alb_wave"
  description = "Allow Wave Lite traffic via ALB."

  vpc_id = local.vpc_id
  computed_ingress_with_source_security_group_id = [
    {
      from_port                = 9099
      to_port                  = 9099
      protocol                 = "tcp"
      description              = "Wave_Lite"
      source_security_group_id = module.sg_alb_core[0].security_group_id
    }
  ]
  number_of_computed_ingress_with_source_security_group_id = 1
}


## ------------------------------------------------------------------------------------
## ALB Controls
## ------------------------------------------------------------------------------------
module "sg_alb_core" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  count = var.flag_create_load_balancer ? 1 : 0

  name        = "${local.global_prefix}_alb_core"
  description = "Allow HTTP (80, 443) to ALB."

  vpc_id              = local.vpc_id
  ingress_cidr_blocks = local.alb_ingress_cidrs
  ingress_rules       = ["https-443-tcp", "http-80-tcp"]
  egress_rules        = var.sg_egress_tower_alb
}


## ------------------------------------------------------------------------------------
## DB Controls
## ------------------------------------------------------------------------------------
module "sg_db" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  count = var.flag_create_external_db ? 1 : 0

  name        = "${local.global_prefix}_rds"
  description = "Seqera Platform RDS traffic."

  vpc_id = local.vpc_id
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
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  name        = "${local.global_prefix}_batch"
  description = "Security group for Tower Batch instance."

  vpc_id = local.vpc_id
  computed_ingress_with_source_security_group_id = [
    {
      rule                     = "ssh-tcp"
      source_security_group_id = module.sg_ec2_core.security_group_id
    }
  ]
  number_of_computed_ingress_with_source_security_group_id = 1
  egress_rules                                             = var.sg_egress_batch_ec2
}


## ------------------------------------------------------------------------------------
## Elasticache (Redis) Controls
## ------------------------------------------------------------------------------------
module "sg_redis" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  count = var.flag_create_external_redis ? 1 : 0

  name        = "${local.global_prefix}_redis"
  description = "Seqera Platform Redis traffic."

  vpc_id = local.vpc_id
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
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  name        = "${local.global_prefix}_vpc_interface"
  description = "Seqera Platform VPC Endpoint traffic."

  vpc_id              = local.vpc_id
  ingress_cidr_blocks = [var.vpc_new_cidr_range]
  ingress_rules       = ["all-all"]
  egress_rules        = var.sg_egress_interface_endpoint
}
