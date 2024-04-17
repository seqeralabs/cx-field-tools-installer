import boto3

from types import SimpleNamespace

from utils.extractors import get_tfvars_as_json
from utils.logger import logger

data = get_tfvars_as_json()
data = SimpleNamespace(**data)          # Can access items via dot-notation for cleaner code.

session = boto3.Session(profile_name=data.aws_profile)
ec2_client = session.client('ec2', region_name=data.aws_region)


def get_all_subnets(cloud_provider="aws"):
    if cloud_provider.lower() == 'aws':
        return get_all_aws_subnets()
    elif cloud_provider.lower() == 'azure':
        pass
    elif cloud_provider.lower() == 'gcp':
        pass
    else:
        raise AssertionError("[ERROR]: Unsupported Cloud Provider specified.")


def get_all_aws_subnets():
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_subnets.html#
    all_subnets = ec2_client.describe_subnets( 
        Filters=[ { 'Name': 'vpc-id', 'Values': [ data.vpc_existing_id ] } ]
    )
    if data.flag_create_new_vpc:
        public_subnet_cidrs = data.vpc_new_public_subnets
        private_subnet_cidrs = data.vpc_new_private_subnets
    else:
        public_subnet_cidrs = [ subnet['CidrBlock'] for subnet in all_subnets['Subnets'] if subnet['MapPublicIpOnLaunch'] ]
        private_subnet_cidrs = [ subnet['CidrBlock'] for subnet in all_subnets['Subnets'] if subnet['MapPublicIpOnLaunch'] == False ]

    logger.debug(public_subnet_cidrs)
    logger.debug(private_subnet_cidrs)

    return public_subnet_cidrs, private_subnet_cidrs