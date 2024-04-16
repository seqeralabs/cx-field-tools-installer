#!/usr/bin/env python3
from typing import List
import ast
import json
import boto3
import re



## ------------------------------------------------------------------------------------
## Convert terraform.tfvars to JSON
## Notes:
##   1. I know it's dumb to home-roll your own parser, but I don't want to introduce extra random
##      packages from the internet. This is fine for our purposes.
##   2. Clean command: `sed '/^\s*\/\*/,/^\s*\*\//d;/^\s*#/d' terraform.tfvars > terraform_no_comments.tfvars`
##      However, `sed` has problem on MacOS, so sticking with (uglier) native Python.
## ------------------------------------------------------------------------------------

# Rules:
#   1. Purge any blank line.
#   2. Purge any line starting with a `#``
#   3. Purge any line starting with `/*`, `*/`, or in between them.
#   4. Purge via tracking indices; purge from right-to-left to avoid index shifting.

# Assumptions:
#   1. Inline comments will only use 1 `#`
#   2. All discrete keys start on Column 1 of a line.

# Edgecase:
#   1. `default_tags` has closing brace without leading space.

data = {}
default_tags = {}


def purge_indices_in_reverse(indices_to_pop):
    for i in reversed(indices_to_pop):
        lines_array.pop(i)


with open('terraform.tfvars', 'r') as file:
    lines = file.readlines()
    lines_array = [line.strip() for line in lines]


    # 1) Remove any blank link in file
    flag_skip_block_comment = False
    indices_to_pop = []

    for i, line in enumerate(lines_array):
        if (line.strip() == "") or (line.startswith('#')):
            indices_to_pop.append(i)

        # Once '/*' detected, flag every line for deletion until '*/' encountered.
        if line.startswith("/*"):
            flag_skip_block_comment = True
            indices_to_pop.append(i)
            continue
        elif line.startswith("*/"):
            flag_skip_block_comment = False
            indices_to_pop.append(i)
        elif flag_skip_block_comment:
            indices_to_pop.append(i)

    purge_indices_in_reverse(indices_to_pop)


    # 2) Purge inline comments from rationalized kv pairs
    for i, line in enumerate(lines_array):
        line = line.rsplit('#')[0]
        lines_array[i] = line


    # 3) Handle `default tags` edge case: extract this value specifically into a dict and pop lines.
    start_handling_tags = False
    indices_to_pop = []

    for i, line in enumerate(lines_array):
        if "default_tags" in line:
            start_handling_tags = True
            indices_to_pop.append(i)
        elif (start_handling_tags) and ("=" in line):
            key, value = [x.strip() for x in line.split('=', 1)]
            default_tags[key] = value.strip('"')
            indices_to_pop.append(i)
        elif (start_handling_tags) and (line == "}"):
            indices_to_pop.append(i)
            break

    purge_indices_in_reverse(indices_to_pop)
    data['default_tags'] = default_tags


    # 4) Handle multiline arrays. Find opening line with '=' and ending in '['
    target_index = None
    indices_to_pop = []
    for i, line in enumerate(lines_array):
        if ("=" in line) and (line.strip()[-1] == "["):
            target_index = i
            continue

        if (target_index is not None):
            lines_array[target_index] += line.strip()
            indices_to_pop.append(i)

        if (line.strip()[-1] == "]"):
            target_index = None

    purge_indices_in_reverse(indices_to_pop)


    # 5) Convert items to proper python types.
    for line in lines_array:
        if "=" in line:
            key, value = [x.strip() for x in line.split('=', 1)]
            if value.lower() == 'true':
                data[key] = True
            elif value.lower() == 'false':
                data[key] = False
            else:
                data[key] = ast.literal_eval(value)

# with open('output.json', 'w') as file:
#     json.dump(data, file, indent=4)

# exit()


def get_container_semantic_versions(data):
    tower_container_version = data["tower_container_version"]
    tower_container_version = tower_container_version.replace("v", "")
    major, minor, patch = tower_container_version.split(".")
    # TO DO: Handle special BETA tags? https://shahzaibchadhar.medium.com/how-to-split-numeric-and-letters-from-a-string-in-python-3646043a73bd
    patch = re.split('(\d+)', patch)[1]

    return f"{major}.{minor}.{patch}"



## ------------------------------------------------------------------------------------
## Check flag groupings to only ensure 1 per group is set as `true`.
## ------------------------------------------------------------------------------------
def only_one_true_set(flags: List, qualifier: str) -> None:
    """Aggregate values of all specified values and then count."""

    values = [ data[flag] for flag in flags ]
    count = values.count(True)

    if (count != 1):
        raise AssertionError(f'[ERROR]: {qualifier} requires one and only one True.')
    else: 
        print(f"[OK]: {qualifier} flags")


def subnet_matches_privacy_type(keys: tuple, qualifier: str) -> None:
    """Ensure EC2 lives in public subnet if fully public; or private if not"""
    flag, ec2_subnets, vpc_subnets = keys
    flag = data[flag]
    ec2_subnets = data[ec2_subnets]
    # Different source of data if creating new vs using existing
    try:
        vpc_subnets = data[vpc_subnets]
    except TypeError:
        pass

    if flag:
        assert set(ec2_subnets).issubset(set(vpc_subnets)), f"{qualifier} do not match. Please fix."
        print(f"[OK]: {qualifier}")
    else:
        print(f"[SKIP]: {qualifier}")


flag_checks = [
    ( [ "flag_create_new_vpc", "flag_use_existing_vpc" ], "VPC" ),
    ( [ "flag_create_external_db", "flag_use_existing_external_db", "flag_use_container_db" ], "DB" ),
    ( [ "flag_create_external_redis", "flag_use_container_redis" ], "REDIS"),
    ( [ "flag_create_load_balancer", "flag_generate_private_cacert", "flag_use_existing_private_cacert", "flag_do_not_use_https" ], "ALB"),
    ( [ "flag_use_aws_ses_iam_integration", "flag_use_existing_smtp" ], "SMTP" )
]


## ------------------------------------------------------------------------------------
## Check subnet assignments based on VPC
## ------------------------------------------------------------------------------------
# Don't have access to existing public / private subnets as of yet. Maybe need to add boto3 to get?
# TO DO: 
#   1. Improve detection of public vs private subnets via route table access to an internet gateway and/or tagging.
#      For Seqera testing purposes, auto-assignment of IP on launch is good enough - comes back in subnet payload and our test
#      VPC is configured to auto-assign.
#   2. Add RDS subnet check
#   3. Add Redis subent check
import boto3
session = boto3.Session(profile_name=data["aws_profile"])
ec2_client = session.client('ec2', region_name=data["aws_region"])

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_subnets.html#
sn_full = ec2_client.describe_subnets(
    Filters=[
        # { 'Name': 'map-public-ip-on-launch', 'Values': [ 'false' ] },
        { 'Name': 'vpc-id', 'Values': [ data["vpc_existing_id"] ] }
    ]
)
sn_public_cidrs = [ subnet['CidrBlock'] for subnet in sn_full['Subnets'] if subnet['MapPublicIpOnLaunch'] ]
sn_private_cidrs = [ subnet['CidrBlock'] for subnet in sn_full['Subnets'] if subnet['MapPublicIpOnLaunch'] == False ]
print(sn_public_cidrs)
print(sn_private_cidrs)

ec2_subnet_privacy = [
    # Check EC2 Assignments
    ( [ "flag_make_instance_public", "vpc_new_ec2_subnets", "vpc_new_public_subnets"], "VPC/EC2 public (new) subnets" ),
    ( [ "flag_make_instance_public", "vpc_existing_ec2_subnets", sn_public_cidrs], "VPC/EC2 public (existing) subnets" ),
    ( [ "flag_make_instance_private", "vpc_new_ec2_subnets", "vpc_new_public_subnets"], "VPC/EC2 private (new) subnets" ),
    ( [ "flag_make_instance_private", "vpc_existing_ec2_subnets", sn_private_cidrs], "VPC/EC2 private (existing) subnets" ),
    ( [ "flag_make_instance_private_behind_public_alb", "vpc_new_ec2_subnets", "vpc_new_public_subnets"], "VPC/EC2 ALB-private (new) subnets" ),
    ( [ "flag_make_instance_private_behind_public_alb", "vpc_existing_ec2_subnets", sn_private_cidrs], "VPC/EC2 ALB-private (existing) subnets" ),
    ( [ "flag_private_tower_without_eice", "vpc_new_ec2_subnets", "vpc_new_public_subnets"], "VPC/EC2 private-noEICE (new) subnets" ),
    ( [ "flag_private_tower_without_eice", "vpc_existing_ec2_subnets", sn_private_cidrs], "VPC/EC2 private-noEICE (existing) subnets" ),
]

if data["flag_create_new_vpc"]:
    alb_subnet_privacy = [
        ( [ "flag_create_load_balancer", "vpc_new_alb_subnets", sn_public_cidrs], "VPC/ALB public (new) subnets"),
    ]
else:
    alb_subnet_privacy = [
        ( [ "flag_create_load_balancer", "vpc_existing_alb_subnets", sn_public_cidrs], "VPC/ALB public (existing) subnets"),
    ]

for check in flag_checks:
    only_one_true_set(*check) 

for check in ec2_subnet_privacy:
    subnet_matches_privacy_type(*check)

for check in alb_subnet_privacy:
    subnet_matches_privacy_type(*check)


## ------------------------------------------------------------------------------------
## Check that passwords not specified in tfvars
## ------------------------------------------------------------------------------------
# Passwords and sensitive values must be stored in SSM

sensitive_keys = [
    'db_root_user', 'db_root_password',
    'tower_db_user', 'tower_db_password',
    'tower_redis_password',
    'tower_jwt_secret', 'tower_crypto_secretkey', 'tower_license',
    'tower_smtp_user', 'tower_smtp_password',
    'swell_db_user', 'swell_db_password'
]

data_keys = data.keys()
for key in sensitive_keys:
    if key in data_keys:
        raise AssertionError(f"[ERROR]: Do not specify `{key}`. This value will be sourced from SSM.")
    else:
        print(f"[OK]: {key}")


## ------------------------------------------------------------------------------------
## Check for dependency keys which were not populated
## ------------------------------------------------------------------------------------
def ensure_dependency_populated(keys: tuple, qualifier: str) -> None:
    """If a flag is set, ensure dependent keys also set."""
    parent, child = keys
    parent = data[parent]
    child = data[child]

    if parent:
        assert "REPLACE_ME" not in child, f"[ERROR]: {qualifier}"
        print(f"[OK]: {qualifier}")
    else: 
        print(f"[SKIP]: {qualifier}")


correlated_keys = [
    # VPC Stuff
    [ ("flag_use_existing_vpc", "vpc_existing_id"), 'Please specify a `vpc_existing_id` value.'],
    [ ("flag_create_load_balancer", "alb_certificate_arn"), 'Please specify an `alb_certificate_arn` value.'],
    # DNS Stuff
    [ ("flag_create_route53_private_zone", "new_route53_private_zone_name"), 'Please specify an `new_route53_private_zone_name` value.'],
    [ ("flag_use_existing_route53_public_zone", "existing_route53_public_zone_name"), 'Please specify an `existing_route53_public_zone_name` value.'],
    [ ("flag_use_existing_route53_private_zone", "existing_route53_private_zone_name"), 'Please specify an `existing_route53_private_zone_name` value.'],
]

for check in correlated_keys:
    ensure_dependency_populated(*check)


## ------------------------------------------------------------------------------------
## Bespoke checks
## ------------------------------------------------------------------------------------

## ----- Tower Server URL
tower_server_url = data["tower_server_url"]

if data["flag_create_route53_private_zone"]:
    assert data["flag_create_route53_private_zone"] in tower_server_url, "[ERROR] `tower_server_url` does not match DNS zone."

if data["flag_use_existing_route53_public_zone"]:
    assert data["existing_route53_public_zone_name"] in tower_server_url, "[ERROR] `tower_server_url` does not match DNS zone."

if data["flag_use_existing_route53_private_zone"]:
    assert data["existing_route53_private_zone_name"] in tower_server_url, "[ERROR] `tower_server_url` does not match DNS zone."

if ( data["tower_server_url"].startswith('http') ):
    raise AssertionError("[ERROR]: Field `tower_server_url` must not have a prefix.")

if ( data["tower_server_port"] != "8000" ):
    print("[REMINDER]: Your Tower instance appears to be using a non-default port (8000). Please ensure your Docker-Compose file is updated accordingly.")


## ----- Tower Root User
if ( data["tower_root_users"] in ["REPLACE_ME", ""] ):
    raise AssertionError("[ERROR]: Please populate `tower_root_user` with an email address.")


## ----- Private CA Checks (if applicable)
if data["flag_generate_private_cacert"]:

    if not data["bucket_prefix_for_new_private_ca_cert"].startswith('s3://'):
        raise AssertionError('[ERROR]: Field `bucket_prefix_for_new_private_ca_cert` must start with `s3://`')

if data["flag_use_existing_private_cacert"]:
    
    print("\t[REMINDER]: Ensure you have added your private .crt and .key files to `assets/customcerts`.")
    print('\t[REMINDER]: Ensure you have updated tfvars `existing_ca_cert_file` and `existing_ca_key_file`.')


## ----- Security Group Reminders
if ( data["sg_ingress_cidrs"] == "0.0.0.0/0"):
    print('[REMINDER]: Security group rule for HTTP(s) ingress is loose by default. Please consider tightening.')

if ( data["sg_ssh_cidrs"] == "0.0.0.0/0" ):
    print('[REMINDER]: Security group rule for SSH ingress is loose by default. Please consider tightening.')


## ----- Database Checks
if ( data["db_engine"] == "mysql" ) and ( '8' in data["db_engine_version"]):
    print("[WARNING]: You appear to be using MySQL 8. Please note that additional TOWER_DB_URL configuration may be required.")

if ( data["tower_db_url"].startswith('jdbc:') ) or ( data["tower_db_url"].startswith('mysql:') ):
    raise AssertionError("[ERROR] Do not include protocol in `tower_db_url`. Start with hostname.")

if ( data["tower_db_driver"] != "org.mariadb.jdbc.Driver" ):
    raise AssertionError("[ERROR] Field `tower_db_driver` must be `org.mariadb.jdbc.Driver`.")

if ( data["tower_db_dialect"] != "io.seqera.util.MySQL55DialectCollateBin" ):
    raise AssertionError("[ERROR] Field `tower_db_dialect` must be `org.mariadb.jdbc.Driver`.")

if ( data["flag_use_container_db"] ):
    
    if ( data["tower_db_url"] != "db:3306" ):
        print("[REMINDER] You appear to be using a non-standard db container name or port. Please verify Docker-Compose config is updated accordingly.")

if ( data["flag_use_existing_external_db"] ):
    print("[REMINDER] You are using a pre-existing external database. Please ensure you create the database, user, and append the database name to `tower_db_url`.")


## ----- Email
if ( data['flag_use_aws_ses_iam_integration'] ):

    container_version = get_container_semantic_versions(data)
    if (container_version) < "23.2.0":
        raise AssertionError("[ERROR]: SES IAM integration not available until Tower 23.2.0. Please fix.")

    if ( "amazonaws.com" not in data["tower_smtp_host"] ):
        raise AssertionError("[ERROR]: You want to SES but are not pointing to an SES endpoint. Please fix.")
    
    if ( data["tower_smtp_port"] != "587" ):
        raise AssertionError("[ERROR]: SES integration requires port 587. Plese fix.")


## ----- Parameter Store
container_version = get_container_semantic_versions(data)
if (container_version) < "23.1.0":
    raise AssertionError("[ERROR]: Parameter Store integration not available until Tower 23.1.0. This is a mandatory integration for the installer.")

exit()



# 23.4.3
#  - migrate-db
# TO DO: Mandatory bootstrap values
# TO DO: Improve logic for value cleansing for these checks.
# TO DO: `tower_enable_platforms`
# TO DO: Check `tower_db_min_pool_size`, `tower_db_max_pool_size`, `tower_db_max_lifetime`, `flyway_locations`
# TO DO: Add new VPC checks
# TO DO: Check ALB cert for legit ARN syntax.
# TO DO: `tower_root_user` values are valid email format and comma-delimited.
# TO DO: Custom OIDC
# TO DO: SEQERAKIT
# TO DO: Custom docker-compose file `flag_use_custom_docker_compose_file``
# TO DO: DNS Reminder `flag_create_route53_record`
# TO DO: Add proper email string check
# - Non-EC2 Subnets in VPC CIDR
# - New subnet CIDRs fit into new VPC CIDR
# - SES IAM
# - DNS checks (Hosted Zones)
# - DNS checks (Tower server URL vs zone name)
# - AZs and Region
# - Pre-existing IAM role
# - EBS encryption key
# Handle RC text on newer container versions

