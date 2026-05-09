from types import SimpleNamespace

import boto3
from installer.utils.extractors import get_tfvars_as_json
from installer.utils.logger import logger


def _get_data():
    """Lazily fetch tfvars-as-namespace. Avoids module-level Docker invocation at import time."""
    return SimpleNamespace(**get_tfvars_as_json())


def generate_aws_session(data=None):
    """Build a boto3 EC2 client using credentials from tfvars."""
    if data is None:
        data = _get_data()
    session = boto3.Session(profile_name=data.aws_profile)
    return session.client("ec2", region_name=data.aws_region)


def get_all_subnets(cloud_provider="aws"):
    """Return public/private subnet CIDRs for the configured VPC."""
    if cloud_provider.lower() == "aws":
        return get_all_aws_subnets()
    if cloud_provider.lower() in ("azure", "gcp"):
        return None  # Azure/GCP support not yet implemented.
    raise AssertionError("[ERROR]: Unsupported Cloud Provider specified.")


def get_all_aws_subnets():
    """Query AWS for the configured VPC's public/private subnet CIDRs."""
    data = _get_data()

    ec2_client = generate_aws_session(data)
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_subnets.html#
    all_subnets = ec2_client.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [data.vpc_existing_id]}])
    if data.flag_create_new_vpc:
        public_subnet_cidrs = data.vpc_new_public_subnets
        private_subnet_cidrs = data.vpc_new_private_subnets
    else:
        public_subnet_cidrs = [
            subnet["CidrBlock"] for subnet in all_subnets["Subnets"] if subnet["MapPublicIpOnLaunch"]
        ]
        private_subnet_cidrs = [
            subnet["CidrBlock"] for subnet in all_subnets["Subnets"] if not subnet["MapPublicIpOnLaunch"]
        ]

    logger.debug(public_subnet_cidrs)
    logger.debug(private_subnet_cidrs)

    return public_subnet_cidrs, private_subnet_cidrs
