terraform {
  required_version = ">= 1.1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.12.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
  # Use a test profile or credentials
  profile = "test"
}

# Test VPC
module "test_vpc" {
  source = "../../modules/vpc"

  name = "test-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true
}

# Test outputs for validation
output "vpc_id" {
  value = module.test_vpc.vpc_id
}

output "private_subnets" {
  value = module.test_vpc.private_subnets
}

output "public_subnets" {
  value = module.test_vpc.public_subnets
} 