## ------------------------------------------------------------------------------------
## NOTE!
## ------------------------------------------------------------------------------------
# This is less elegant than using a for-each construct but I think it's easier to maintain.
# YMMV - A rewrite could make things cleaner.


## ------------------------------------------------------------------------------------
## Instance Connect Endpoint Controls
## ------------------------------------------------------------------------------------
module "tower_eice_ingress_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  name        = "${local.global_prefix}_eice_sg"
  description = "Allowed ingress CIDRS EC2 Instance Connect endpoint."

  vpc_id              = local.vpc_id
  ingress_cidr_blocks = var.sg_ingress_cidrs
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
  ingress_cidr_blocks = var.sg_ingress_cidrs
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

  vpc_id              = local.vpc_id
  ingress_with_cidr_blocks = local.tower_ec2_direct_connect_sg_final
#   ingress_with_cidr_blocks = [ for cidr_block in var.sg_ingress_cidrs :
#       { 
#         from_port   = 7070
#         to_port     = 7070
#         protocol    = "tcp"
#         description = "Connect-Server"
#         cidr_blocks = cidr_block
#       },
#       { 
#         from_port   = 9090
#         to_port     = 9090
#         protocol    = "tcp"
#         description = "Connect-Proxy"
#         cidr_blocks = cidr_block
#       }
#     ]
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

  name        = "${local.global_prefix}_ec2_direct_connect_sg"
  description = "Direct HTTP to Tower EC2 host when Connect active."

  vpc_id              = local.vpc_id
  computed_ingress_with_cidr_blocks = local.tower_ec2_alb_connect_sg_final
  # ingress_with_cidr_blocks = [
  #   [ for cidr_block in var.sg_ingress_cidrs :
  #     { 
  #       from_port   = 7070
  #       to_port     = 7070
  #       protocol    = "tcp"
  #       description = "Connect-Server"
  #       source_security_group_id = module.tower_alb_sg.security_group_id
  #     }
  #   ],
  #   [ for cidr_block in var.sg_ingress_cidrs : 
  #     { 
  #       from_port   = 9090
  #       to_port     = 9090
  #       protocol    = "tcp"
  #       description = "Connect-Proxy"
  #       source_security_group_id = module.tower_alb_sg.security_group_id
  #     }
  #   ]
  # ]
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