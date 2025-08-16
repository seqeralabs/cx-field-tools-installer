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
module "sg_ec2_noalb_with_private_certificate" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  count = var.flag_create_load_balancer == false && var.flag_use_private_cacert ? 1 : 0

  name        = "${local.global_prefix}_ec2_direct_with_private_certificate"
  description = "Direct HTTP (80 & 443) traffic to EC2."

  vpc_id              = local.vpc_id
  ingress_cidr_blocks = var.sg_ingress_cidrs
  ingress_rules       = ["https-443-tcp", "http-80-tcp"]
}

module "sg_ec2_noalb_no_https" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  count = var.flag_create_load_balancer == false && var.flag_do_not_use_https ? 1 : 0

  name        = "${local.global_prefix}_ec2_direct_no_https"
  description = "Direct HTTP (8000) traffic to EC2."

  vpc_id              = local.vpc_id
  ingress_cidr_blocks = var.sg_ingress_cidrs
  ingress_rules       = ["splunk-web-tcp"]
}


module "sg_ec2_noalb_connect" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  count = var.flag_create_load_balancer == false && var.flag_enable_data_studio == true ? 1 : 0

  name        = "${local.global_prefix}_ec2_direct_connect"
  description = "Direct HTTP (9090) traffic to EC2."

  vpc_id = local.vpc_id
  computed_ingress_with_cidr_blocks = [
    {
      from_port   = 9090
      to_port     = 9090
      protocol    = "tcp"
      description = "Connect-Proxy"
      cidr_blocks = "${join(",", var.sg_ingress_cidrs)}"
    }
  ]
  # number_of_computed_ingress_with_source_security_group_id = 1
  number_of_computed_ingress_with_source_security_group_id = 0
}


module "sg_from_alb_core" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  count = var.flag_create_load_balancer == true ? 1 : 0

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

  count = var.flag_create_load_balancer == true && var.flag_enable_data_studio == true ? 1 : 0

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

  count = var.flag_create_load_balancer == true && var.flag_use_wave_lite == true ? 1 : 0

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

  count = var.flag_create_load_balancer == true ? 1 : 0

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

  count = var.flag_create_external_db == true ? 1 : 0

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

  count = var.flag_create_external_redis == true ? 1 : 0

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


/*
## ------------------------------------------------------------------------------------
## AUGUST 15, 2025 - THIS SECTION DEPRECATED BUT NEEDS TO EXIST FOR REASONS
## ------------------------------------------------------------------------------------
@gwright99 did something stupid between Release 1.5.0 and 1.6.0:
- [1.5.0](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.5.0/002_security_groups.tf)
- [1.6.0](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.6.0/002_security_groups.tf)

I renamed and consolidated many of the Security Groups for easier management and cleaner naming, but didn't consider
what the impact would be on sites that:

1) Reused these assets in other parts of the AWS Account not tied to the installer.
2) Had an instance running on a VM with an old AMI, which would cause TF to instantiate a new VM and SGs alongside the old one.

In order to support an orderly transition, I am reintroducing ALL the old 1.5.0 SGs. The reintroduction will ensure that any of the
existing deloyments still find the assets they need prior to upgrade and then be able to transition to the new SG model introduced in 1.6.0.

In a subsequent release, the resources below will be removed and documentation will clearly reflect that < 1.6.1 needs to upgrade to 1.6.1 
prior to upgrading to any future release > 1.6.1

*/

## ------------------------------------------------------------------------------------
## Instance Connect Endpoint Controls
## ------------------------------------------------------------------------------------
module "tower_eice_ingress_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  name        = "${local.global_prefix}_eice_sg"
  description = "Allowed ingress CIDRS EC2 Instance Connect endpoint."

  vpc_id              = local.vpc_id
  ingress_cidr_blocks = var.sg_ssh_cidrs
  ingress_rules       = ["ssh-tcp"]
}


module "tower_eice_egress_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  name        = "${local.global_prefix}_ec2_egress_sg"
  description = "Allowed egress CIDRS EC2 Instance Connect endpoint."

  vpc_id       = local.vpc_id
  egress_rules = var.sg_egress_eice
}


## ------------------------------------------------------------------------------------
## EC2 Controls
## ------------------------------------------------------------------------------------
module "tower_ec2_ssh_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  name        = "${local.global_prefix}_ec2_ssh_sg"
  description = "Allowed SSH ingress to EC2 instance (EICE only)."

  vpc_id              = local.vpc_id
  ingress_cidr_blocks = var.sg_ssh_cidrs
  ingress_rules       = ["ssh-tcp"]
}


module "tower_ec2_egress_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  name        = "${local.global_prefix}_ec2_egress_sg"
  description = "Tower EC2 host egress."

  vpc_id              = local.vpc_id
  ingress_cidr_blocks = var.sg_ingress_cidrs
  egress_rules        = var.sg_egress_tower_ec2
}


module "tower_ec2_direct_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  name        = "${local.global_prefix}_ec2_direct_sg"
  description = "Direct HTTP to Tower EC2 host."

  vpc_id              = local.vpc_id
  ingress_cidr_blocks = var.sg_ingress_cidrs
  ingress_rules       = ["https-443-tcp", "http-80-tcp", "splunk-web-tcp"]
}

module "tower_ec2_direct_connect_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  count = var.flag_enable_data_studio == true ? 1 : 0

  name        = "${local.global_prefix}_ec2_direct_connect_sg"
  description = "Direct HTTP to Tower EC2 host when Connect active."

  vpc_id = local.vpc_id
  # ingress_with_cidr_blocks = ["local.tower_ec2_direct_connect_sg_final"]
}


module "tower_ec2_alb_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  name        = "${local.global_prefix}_ec2_alb_sg"
  description = "ALB HTTP to Tower EC2 host."

  vpc_id = local.vpc_id
  computed_ingress_with_source_security_group_id = [
    {
      rule                     = "splunk-web-tcp"
      source_security_group_id = module.tower_alb_sg.security_group_id
    }
  ]
  number_of_computed_ingress_with_source_security_group_id = 1
}


## ------------------------------------------------------------------------------------
## ALB Controls
## ------------------------------------------------------------------------------------
module "tower_alb_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  name        = "${local.global_prefix}_alb_sg"
  description = "HTTP to Tower ALB instance."

  vpc_id              = local.vpc_id
  ingress_cidr_blocks = local.alb_ingress_cidrs #var.sg_ingress_cidrs
  ingress_rules       = ["https-443-tcp", "http-80-tcp"]
  egress_rules        = var.sg_egress_tower_alb
}


module "tower_ec2_alb_connect_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  count = var.flag_enable_data_studio == true ? 1 : 0

  name        = "${local.global_prefix}_ec2_alb_connect_sg"
  description = "Direct HTTP to Tower EC2 host when Connect active."

  vpc_id = local.vpc_id
  # computed_ingress_with_cidr_blocks = local.tower_ec2_alb_connect_sg_final
  # computed_ingress_with_cidr_blocks = local.tower_ec2_alb_connect_sg_final
  #computed_ingress_with_source_security_group_id= local.tower_ec2_alb_connect_sg_final
  # number_of_computed_ingress_with_source_security_group_id = 1
}

## ------------------------------------------------------------------------------------
## DB Controls
## ------------------------------------------------------------------------------------
module "tower_db_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  name        = "${local.global_prefix}_rds_sg"
  description = "Security group for Tower RDS instance."

  vpc_id = local.vpc_id
  computed_ingress_with_source_security_group_id = [
    {
      rule                     = "mysql-tcp"
      source_security_group_id = module.tower_ec2_egress_sg.security_group_id
    }
  ]
  number_of_computed_ingress_with_source_security_group_id = 1
}


## ------------------------------------------------------------------------------------
## AWS Batch Security Groups
## ------------------------------------------------------------------------------------
module "tower_batch_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  name        = "${local.global_prefix}_batch_sg"
  description = "Security group for Tower Batch instance."

  vpc_id       = local.vpc_id
  egress_rules = var.sg_egress_batch_ec2

  computed_ingress_with_source_security_group_id = [
    {
      rule                     = "ssh-tcp"
      source_security_group_id = module.tower_ec2_egress_sg.security_group_id
    }
  ]
  number_of_computed_ingress_with_source_security_group_id = 1
}


## ------------------------------------------------------------------------------------
## Elasticache (Redis) Controls
## ------------------------------------------------------------------------------------
module "tower_redis_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  name        = "${local.global_prefix}_redis_sg"
  description = "Security group for Tower Elasticache instance."

  vpc_id = local.vpc_id
  computed_ingress_with_source_security_group_id = [
    {
      rule                     = "redis-tcp"
      source_security_group_id = module.tower_ec2_egress_sg.security_group_id
    }
  ]
  number_of_computed_ingress_with_source_security_group_id = 1
}


## ------------------------------------------------------------------------------------
## Gateway & Interface Endpoint Controls
## ------------------------------------------------------------------------------------
module "tower_interface_endpoint_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  name        = "${local.global_prefix}_interface_sg"
  description = "Allowed ingress on VPC endpoints in Tower Subnet."

  vpc_id              = local.vpc_id
  ingress_cidr_blocks = [var.vpc_new_cidr_range]
  ingress_rules       = ["all-all"]
  egress_rules        = var.sg_egress_interface_endpoint
}
