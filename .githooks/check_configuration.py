#!/usr/bin/env python3

import os, sys
#sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.dont_write_bytecode = True

import re
from types import SimpleNamespace
from typing import List

from utils.extractors import get_tfvars_as_json #convert_tfvars_to_dictionary
from utils.logger import logger
from utils.subnets import get_all_subnets


## ------------------------------------------------------------------------------------
## NOTE: See comments in utils/helpers.py for reasons why we created our own hacky tfvars parser.
## ------------------------------------------------------------------------------------


## ------------------------------------------------------------------------------------
## HELPER FUNCTIONS
## ------------------------------------------------------------------------------------
# def get_container_semantic_versions(data):
#     """This may not be necessary since I can do basic string comparisons. TODO: Decide if can be purged."""
#     tower_container_version = data.tower_container_version
#     tower_container_version = tower_container_version.replace("v", "")
#     major, minor, patch = tower_container_version.split(".")
#     # TO DO: Handle special BETA tags? https://shahzaibchadhar.medium.com/how-to-split-numeric-and-letters-from-a-string-in-python-3646043a73bd
#     patch = re.split('(\d+)', patch)[1]
#     return f"{major}.{minor}.{patch}"


def only_one_true_set(flags: List, qualifier: str) -> None:
    """Check flag groupings to only ensure 1 per group is set as `true`. Aggregate values of all specified values and then count."""

    values = [ flag for flag in flags ]
    if (values.count(True) != 1):
        raise AssertionError(f' {qualifier} requires one and only one True.')
    logger.debug(f"[OK]: {qualifier} flags")


def subnet_matches_privacy_type(flag: str, subnets: List, qualifier: str) -> None:
    """Check subnets configured in VPC versus those specified in tfvars for various components."""
    ec2_subnets, vpc_subnets = subnets

    if flag:
        assert set(ec2_subnets).issubset(set(vpc_subnets)), f"{qualifier} do not match. Please fix."
        logger.debug(f"[OK]: {qualifier}")
        return
    logger.debug(f"[SKIP]: {qualifier}")


def ensure_dependency_populated(flag: bool, child: str, qualifier: str) -> None:
    """If a flag is set, ensure dependent keys also set."""

    if flag:
        assert "REPLACE_ME" not in child, f"[ERROR]: {qualifier}"
        logger.debug(f"[OK]: {qualifier}")
        return
    logger.debug(f"[SKIP]: {qualifier}")


## ------------------------------------------------------------------------------------
## MAIN
## ------------------------------------------------------------------------------------
if __name__ == '__main__':

    logger.info("")
    logger.info("Beginning tfvars configuration check.")

    # Generaed dictionary from tfvars then convert to SimpleNamespace for cleaner dot-notation access.
    # Kept the two objects different for convenience when .keys() method is required.
    data_dictionary = get_tfvars_as_json()
    data = SimpleNamespace(**data_dictionary)

    # Check minimum container version
    if not ((data.tower_container_version).startswith('v')) or (data.tower_container_version < "v23.1.0"):
        raise AssertionError(" Tower version minimum is 23.1.0 (for Parameter Store integration).")


    # Check true/false blocks
    only_one_true_set([ data.flag_create_new_vpc, data.flag_use_existing_vpc ], "VPC")
    only_one_true_set([ data.flag_create_external_db, data.flag_use_existing_external_db, data.flag_use_container_db ], "DB")
    only_one_true_set([ data.flag_create_external_redis, data.flag_use_container_redis ], "REDIS" )
    only_one_true_set([ data.flag_create_load_balancer, data.flag_generate_private_cacert, data.flag_use_existing_private_cacert, data.flag_do_not_use_https ], "REDIS")
    only_one_true_set([ data.flag_create_load_balancer, data.flag_generate_private_cacert, data.flag_use_existing_private_cacert, data.flag_do_not_use_https ], "ALB")
    only_one_true_set([ data.flag_use_aws_ses_iam_integration, data.flag_use_existing_smtp ], "SMTP" )


    # Check EC2 subnet configuration
    public_subnets, private_subnets = get_all_subnets("aws")

    if data.flag_create_new_vpc:
        subnet_matches_privacy_type( data.flag_make_instance_public, [data.vpc_new_ec2_subnets, public_subnets], "VPC/EC2 public (new) subnets" )
        subnet_matches_privacy_type( data.flag_make_instance_private, [data.vpc_new_ec2_subnets, private_subnets ], "VPC/EC2 private (new) subnets" )
        subnet_matches_privacy_type( data.flag_make_instance_private_behind_public_alb, [data.vpc_new_ec2_subnets, private_subnets ], "VPC/EC2 ALB-private (new) subnets" )
        subnet_matches_privacy_type( data.flag_private_tower_without_eice, [data.vpc_new_ec2_subnets, private_subnets ], "VPC/EC2 ALB-private (new) subnets" )
    elif  data.flag_use_existing_vpc:
        subnet_matches_privacy_type( data.flag_make_instance_public, [data.vpc_existing_ec2_subnets, public_subnets], "VPC/EC2 public (existing) subnets" )
        subnet_matches_privacy_type( data.flag_make_instance_private, [data.vpc_existing_ec2_subnets, private_subnets ], "VPC/EC2 private (new) subnets" )
        subnet_matches_privacy_type( data.flag_make_instance_private_behind_public_alb, [data.vpc_existing_ec2_subnets, private_subnets ], "VPC/EC2 ALB-private (existing) subnets" )
        subnet_matches_privacy_type( data.flag_private_tower_without_eice, [data.vpc_existing_ec2_subnets, private_subnets ], "VPC/EC2 ALB-private (existing) subnets" )
    else:
        raise AssertionError("Invalid VPC options selected.")

    # Check ALB subnet configuration
    subnet_matches_privacy_type( data.flag_create_load_balancer, [data.vpc_new_alb_subnets, public_subnets], "VPC/EC2 public (new) subnets" )
    subnet_matches_privacy_type( data.flag_create_load_balancer, [data.vpc_existing_alb_subnets, public_subnets], "VPC/EC2 public (existing) subnets" )


    # Check sensitive keys
    sensitive_keys = [
        'db_root_user', 'db_root_password',
        'tower_db_user', 'tower_db_password',
        'tower_redis_password',
        'tower_jwt_secret', 'tower_crypto_secretkey', 'tower_license',
        'tower_smtp_user', 'tower_smtp_password',
        'swell_db_user', 'swell_db_password'
    ]

    data_keys = data_dictionary.keys()
    for key in sensitive_keys:
        if key in data_keys:
            raise AssertionError(f" Do not specify `{key}`. This value will be sourced from SSM.")


    ## SES IAM integration check
    if data.flag_use_aws_ses_iam_integration:

        if data.tower_container_version < "v23.2.0": 
            raise AssertionError(" SES IAM integration not available until Tower 23.2.0. Please fix.")
        
        if "amazonaws.com" not in data.tower_smtp_host: 
            raise AssertionError(" You want to SES but are not pointing to an SES endpoint. Please fix.")
        
        if data.tower_smtp_port != "587": 
            raise AssertionError(" SES integration requires port 587. Plese fix.")


    ## Tower server URL checks
    if data.flag_create_route53_private_zone:
        assert data.flag_create_route53_private_zone in data.tower_server_url, "[ERROR] `tower_server_url` does not match DNS zone."

    if data.flag_use_existing_route53_public_zone:
        assert data.existing_route53_public_zone_name in data.tower_server_url, "[ERROR] `tower_server_url` does not match DNS zone."

    if data.flag_use_existing_route53_private_zone:
        assert data.existing_route53_private_zone_name in data.tower_server_url, "[ERROR] `tower_server_url` does not match DNS zone."

    if data.tower_server_url.startswith('http'):
        raise AssertionError(" Field `tower_server_url` must not have a prefix.")

    if data.tower_server_port != "8000":
        logger.warning("[REMINDER]: Your Tower instance is using a non-default port (8000). Ensure your Docker-Compose file is updated accordingly.")


    ## Database checks
    if ( data.db_engine == "mysql" ) and ( '8' in data.db_engine_version):
        logger.warning("MySQL 8 may need TOWER_DB_URL connection string modifiers.")

    if ( data.tower_db_url.startswith('jdbc:') ) or ( data.tower_db_url.startswith('mysql:') ):
        raise AssertionError(" Do not include protocol in `tower_db_url`. Start with hostname.")

    if ( data.tower_db_driver != "org.mariadb.jdbc.Driver" ):
        raise AssertionError(" Field `tower_db_driver` must be `org.mariadb.jdbc.Driver`.")

    if ( data.tower_db_dialect != "io.seqera.util.MySQL55DialectCollateBin" ):
        raise AssertionError(" Field `tower_db_dialect` must be `org.mariadb.jdbc.Driver`.")

    if data.flag_use_container_db:
        
        if data.tower_db_url != "db:3306":
            logger.warning("[REMINDER] You are using a non-standard db container name or port. Ensure Docker-Compose config is updated accordingly.")

    if ( data.flag_use_existing_external_db ):
        logger.warning("[REMINDER] You are using a pre-existing external database. Please ensure you create the database, user, and append the database name to `tower_db_url`.")


    # Tower root users check
    if data.tower_root_users in [ "REPLACE_ME", "" ]:
        raise AssertionError(" Please populate `tower_root_user` with at least one email address.")


    # Private CA checks
    if data.flag_generate_private_cacert:
        if not data.bucket_prefix_for_new_private_ca_cert.startswith('s3://'):
            raise AssertionError(' Field `bucket_prefix_for_new_private_ca_cert` must start with `s3://`')

    if data.flag_use_existing_private_cacert:
        logger.warning("\t[REMINDER]: Ensure you have added your private .crt and .key files to `assets/customcerts`.")
        logger.warning('\t[REMINDER]: Ensure you have updated tfvars `existing_ca_cert_file` and `existing_ca_key_file`.')


    ## Security Group reminders
    if data.sg_ingress_cidrs == "0.0.0.0/0":
        logger.warning('[REMINDER]: Security group rule for HTTP(s) ingress is loose by default. Please consider tightening.')

    if data.sg_ssh_cidrs == "0.0.0.0/0":
        logger.warning('[REMINDER]: Security group rule for SSH ingress is loose by default. Please consider tightening.')


    # VPC Dependency checks
    ensure_dependency_populated(data.flag_use_existing_vpc, data.vpc_existing_id, 'Specify a `vpc_existing_id` value.')
    ensure_dependency_populated(data.flag_create_load_balancer, data.alb_certificate_arn, 'Specify an `alb_certificate_arn` value.')


    # DNS dependency checks
    ensure_dependency_populated(data.flag_create_route53_private_zone, data.new_route53_private_zone_name, 'Specify an `new_route53_private_zone_name` value.')
    ensure_dependency_populated(data.flag_use_existing_route53_public_zone, data.existing_route53_public_zone_name, 'Specify an `existing_route53_public_zone_name` value.')
    ensure_dependency_populated(data.flag_use_existing_route53_private_zone, data.existing_route53_private_zone_name, 'Specify an `existing_route53_private_zone_name` value.')


    logger.info("Finished tfvars configuration check.")
    logger.info("")

    exit()

# 23.4.3
# TO DO
#  - migrate-db
#  - Mandatory bootstrap values
#  - Improve logic for value cleansing for these checks.
#  - `tower_enable_platforms`
#  - Check `tower_db_min_pool_size`, `tower_db_max_pool_size`, `tower_db_max_lifetime`, `flyway_locations`
#  - Check ALB cert for legit ARN syntax.
#  - `tower_root_user` values are valid email format and comma-delimited.
#  - Custom OIDC
#  - SEQERAKIT
#  - Custom docker-compose file `flag_use_custom_docker_compose_file``
#  - DNS Reminder `flag_create_route53_record`
#  - Add proper email string check
# - Non-EC2 Subnets in VPC CIDR
# - AZs and Region
# - Pre-existing IAM role
# - EBS encryption key
# - DNS hosted zones
#    - Check existing public / private hosted zones exist if specified in tfvars.

# Don't have access to existing public / private subnets as of yet. Maybe need to add boto3 to get?
# TO DO: 
#   1. Improve detection of public vs private subnets via route table access to an internet gateway and/or tagging.
#      For Seqera testing purposes, auto-assignment of IP on launch is good enough - comes back in subnet payload and our test
#      VPC is configured to auto-assign.
#   2. Add RDS subnet check
#   3. Add Redis subent check