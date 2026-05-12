## DATA
## ===============================================================================
/*
If using a pre-existing VPC, we can immediately find all subnet details via data.aws_subnets.
If creating a new VPC, we need to pull this information from the VPC module output.
*/
data "aws_vpc" "sp_vpc" {
  count = var.use_mocks ? 0 : 1
  id    = var.vpc_id
}

data "aws_subnets" "all" {
  count = var.create_new_vpc || var.use_mocks ? 0 : 1
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.sp_vpc[0].id]
  }
}

data "aws_subnet" "sp_subnets" {
  for_each = var.create_new_vpc || var.use_mocks ? toset([]) : toset(data.aws_subnets.all[0].ids)
  id       = each.value
}


locals {

  # Combine real and testing flows
  mock_sp_vpc          = "vpc-0fd280748c05b375b"
  mock_aws_subnets_all = ["subnet-00fad764627895f33", "subnet-0d0e8ba3b03b97a65", "subnet-0e07c9b2edbd84ea4", "subnet-0f18039d5ffcf6cd3"]

  # For new VPC: Get subnet details from the VPC module
  real_new_vpc_subnets = var.create_new_vpc ? {
    public = {
      cidr_blocks = var.vpc_module.public_subnets_cidr_blocks
      subnet_ids  = var.vpc_module.public_subnets
    }
    private = {
      cidr_blocks = var.vpc_module.private_subnets_cidr_blocks
      subnet_ids  = var.vpc_module.private_subnets
    }
  } : {}

  # For existing VPC: Get subnet details from data sources when doing a real deployment.
  real_existing_vpc_subnets = var.create_new_vpc || var.use_mocks ? {} : {
    public = {
      cidr_blocks = [for subnet in data.aws_subnet.sp_subnets : subnet.cidr_block if subnet.map_public_ip_on_launch]
      subnet_ids  = [for subnet in data.aws_subnet.sp_subnets : subnet.id if subnet.map_public_ip_on_launch]
    }
    private = {
      cidr_blocks = [for subnet in data.aws_subnet.sp_subnets : subnet.cidr_block if !subnet.map_public_ip_on_launch]
      subnet_ids  = [for subnet in data.aws_subnet.sp_subnets : subnet.id if !subnet.map_public_ip_on_launch]
    }
  }

  # NOTE: These values need to map to CIDRs set in testing data.
  mock_existing_vpc_subnets = var.use_mocks ? {
    public = {
      cidr_blocks = ["10.0.1.0/24", "10.0.2.0/24"]
      subnet_ids  = ["subnet-00fad764627895f33", "subnet-0d0e8ba3b03b97a65"]
    }
    private = {
      cidr_blocks = ["10.0.3.0/24", "10.0.4.0/24"]
      subnet_ids  = ["subnet-0e07c9b2edbd84ea4", "subnet-0f18039d5ffcf6cd3"]
    }
  } : {}

  # Combine the mappings based on VPC creation mode. Then decide whether to use real or mock based on testing flag.
  real_subnet_details = var.create_new_vpc ? local.real_new_vpc_subnets : local.real_existing_vpc_subnets
  subnet_details      = var.use_mocks ? local.mock_existing_vpc_subnets : local.real_subnet_details

  # Create the final CIDR to ID maps
  public_cidr_to_id_map = {
    for idx, cidr in local.subnet_details.public.cidr_blocks : cidr => local.subnet_details.public.subnet_ids[idx]
  }

  private_cidr_to_id_map = {
    for idx, cidr in local.subnet_details.private.cidr_blocks : cidr => local.subnet_details.private.subnet_ids[idx]
  }

  # Combined map of all subnets
  # Should create an output like `{ "10.0.1.0/24": "subnet-01234567890abcdef", "10.0.2.0/24": "subnet-01234567890abcdef" }`
  cidr_to_id_map = merge(local.public_cidr_to_id_map, local.private_cidr_to_id_map)

  subnet_ids_ec2   = [for cidr in var.subnets_ec2 : local.cidr_to_id_map[cidr]]
  subnet_ids_batch = [for cidr in var.subnets_batch : local.cidr_to_id_map[cidr]]
  subnet_ids_db    = [for cidr in var.subnets_db : local.cidr_to_id_map[cidr]]
  subnet_ids_redis = [for cidr in var.subnets_redis : local.cidr_to_id_map[cidr]]
  subnet_ids_alb   = try([for cidr in var.subnets_alb : local.cidr_to_id_map[cidr]], [])
}
