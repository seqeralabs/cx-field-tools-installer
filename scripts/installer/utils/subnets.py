from types import SimpleNamespace

import boto3
from installer.utils.extractors import tf_vars_json_payload
from installer.utils.logger import logger

data = tf_vars_json_payload
data = SimpleNamespace(**data)  # Can access items via dot-notation for cleaner code.


def generate_aws_session(data=data):
    session = boto3.Session(profile_name=data.aws_profile)
    ec2_client = session.client("ec2", region_name=data.aws_region)
    return ec2_client


def get_all_subnets(cloud_provider="aws"):
    if cloud_provider.lower() == "aws":
        return get_all_aws_subnets()
    elif cloud_provider.lower() == "azure":
        pass
    elif cloud_provider.lower() == "gcp":
        pass
    else:
        raise AssertionError("[ERROR]: Unsupported Cloud Provider specified.")


def get_all_aws_subnets():

    ec2_client = generate_aws_session(data)
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_subnets.html#
    all_subnets = ec2_client.describe_subnets(
        Filters=[{"Name": "vpc-id", "Values": [data.vpc_existing_id]}]
    )
    if data.flag_create_new_vpc:
        public_subnet_cidrs = data.vpc_new_public_subnets
        private_subnet_cidrs = data.vpc_new_private_subnets
    else:
        public_subnet_cidrs = [
            subnet["CidrBlock"]
            for subnet in all_subnets["Subnets"]
            if subnet["MapPublicIpOnLaunch"]
        ]
        private_subnet_cidrs = [
            subnet["CidrBlock"]
            for subnet in all_subnets["Subnets"]
            if subnet["MapPublicIpOnLaunch"] == False
        ]

    logger.debug(public_subnet_cidrs)
    logger.debug(private_subnet_cidrs)

    return public_subnet_cidrs, private_subnet_cidrs
