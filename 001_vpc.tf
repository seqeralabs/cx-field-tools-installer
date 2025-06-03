# Ignore: (1) Flow log enablement; (2) Ingress on all ports; (3) Ingress from public internet
#trivy:ignore:AVD-AWS-0102 trivy:ignore:AVD-AWS-0105
module "vpc" {
  # https://registry.terraform.io/modules/terraform-aws-modules/vpc/aws/latest?tab=dependencies
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.2"

  count = var.flag_create_new_vpc == true ? 1 : 0

  name = "${local.global_prefix}-vpc"
  cidr = var.vpc_new_cidr_range
  azs  = var.vpc_new_azs

  private_subnets = var.vpc_new_private_subnets
  public_subnets  = var.vpc_new_public_subnets
  # database_subnets        = var.vpc_new_db_subnets

  map_public_ip_on_launch                           = var.flag_make_instance_public == true ? true : false
  public_subnet_private_dns_hostname_type_on_launch = "ip-name"

  # Opinionated for simplicity.
  enable_nat_gateway     = var.flag_make_instance_private == true || var.flag_make_instance_private_behind_public_alb == true ? true : false
  single_nat_gateway     = var.flag_make_instance_private == true || var.flag_make_instance_private_behind_public_alb == true ? true : false
  one_nat_gateway_per_az = false

  # Flow log config
  # Config taken from here: https://github.com/terraform-aws-modules/terraform-aws-vpc/blob/master/examples/vpc-flow-logs/main.tf
  enable_flow_log = var.enable_vpc_flow_logs
  create_flow_log_cloudwatch_log_group = true
  create_flow_log_cloudwatch_iam_role  = true
  flow_log_max_aggregation_interval         = 60
  flow_log_cloudwatch_log_group_name_prefix = "/${local.global_prefix}/vpc-flow-logs/"
  flow_log_cloudwatch_log_group_name_suffix = "platform"
  # flow_log_cloudwatch_log_group_class       = "INFREQUENT_ACCESS"
}


# https://stackoverflow.com/questions/67562197/terraform-loop-through-ids-list-and-generate-data-blocks-from-it-and-access-it
data "aws_subnet" "existing" {
  # Creates a map with the keys being the CIDRs --  e.g. `data.aws_subnet.public["10.0.0.0/20"].id
  # Only make a data query if we are using an existing VPC
  for_each = var.flag_use_existing_vpc == true ? toset(local.subnets_all) : []

  vpc_id     = local.vpc_id
  cidr_block = each.key
}


# Needed to add this to get existing CIDR range to limit ALB listeners
data "aws_vpc" "preexisting" {
  id = local.vpc_id
}

# Needed to grab route tables from pre-existing VPC to create VPC endpoints.
data "aws_route_tables" "preexisting" {
  vpc_id = local.vpc_id

  filter {
    name = "tag:Name"
    values = ["*private*"]
  }
}


resource "aws_vpc_endpoint" "global_endpoints" {
  for_each = toset(var.vpc_gateway_endpoints_all)

  vpc_id            = local.vpc_id
  vpc_endpoint_type = "Gateway"
  service_name      = "com.amazonaws.${var.aws_region}.${each.key}"
  # route_table_ids   = module.vpc[0].private_route_table_ids
  route_table_ids = local.vpc_private_route_table_ids


  tags = {
    Name = "${local.global_prefix}-global-${each.key}"
  }
}


resource "aws_vpc_endpoint" "tower_endpoints" {
  for_each = toset(var.vpc_interface_endpoints_tower)

  vpc_id             = local.vpc_id
  subnet_ids         = [local.subnet_ids_ec2[0]]
  vpc_endpoint_type  = "Interface"
  service_name       = "com.amazonaws.${var.aws_region}.${each.key}"
  security_group_ids = [module.sg_vpc_endpoint.security_group_id]

  auto_accept         = true
  private_dns_enabled = true

  tags = {
    Name = "${local.global_prefix}-tower-${each.key}"
  }
}

resource "aws_vpc_endpoint" "batch_endpoints" {
  for_each = toset(var.vpc_interface_endpoints_batch)

  vpc_id             = local.vpc_id
  subnet_ids         = local.subnet_ids_batch
  vpc_endpoint_type  = "Interface"
  service_name       = "com.amazonaws.${var.aws_region}.${each.key}"
  security_group_ids = [module.sg_vpc_endpoint.security_group_id]

  auto_accept = true

  # This caused conflict with the existing endpoints created by EC2.
  # Rule: Overload EC2 with any endpoints required by Batch
  # private_dns_enabled       = true

  tags = {
    Name = "${local.global_prefix}-batch-${each.key}"
  }
}
