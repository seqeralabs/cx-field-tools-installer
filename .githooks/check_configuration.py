#!/usr/bin/env python3

# Preliminary tooling to programmtically check related `terraform.tfvars` settings prior to `terraform apply`.
# Not yet fully complete (current as of Jan 29/24).

from typing import List


tfvars = {}
# Rules:
#   1. Skip any line that is blank.
#   2. Skip any line starting with a `#``
#   3. Skip any line starting with `/*` or `*/`
#   4. Skip any line found between finding `/*` and finding `*/` 

# Assumptions:
#   1. Inline comments will only use 1 `#`
#   2. All discrete keys start on Column 1 of a line.
#   3. Any blank lines between entries will be via carriage return (not spacebar)

# Edgecase:
#   1. `default_tags` has closing brace without leading space.

# Notes:
#   1. I know it's dumb to home-roll your own parser, but I don't want to introduce extra random
#      packages from the internet. This is fine for our purposes.





# lines_without_bulk_comments = []
# lines_without_inline_comments = []
# lines_without_inline_whitespace = []

# lines_without_compound_entries = []

# with open('terraform.tfvars', 'r') as f:
#     raw_lines = f.readlines()

# # print(raw_lines)

# # Rip out all blank lines, single- and block-comment lines.
# flag_skip_block_comment = False
# for line in raw_lines:
#     if (line.strip() == "") or (line.startswith('#')):
#         pass
#     elif line.startswith("/*"):
#         flag_skip_block_comment = True
#         pass
#     elif line.startswith("*/"):
#         flag_skip_block_comment = False
#         pass
#     # Must be here so we can deactivate the block comment if encountered
#     elif flag_skip_block_comment == True:
#         pass
#     else:
#         lines_without_bulk_comments.append(line)

# # Strip out inline comments
# for line in lines_without_bulk_comments:
#     line = line.split('#')[0]
#     lines_without_inline_comments.append(line)
#     print(f"line: {line}")

# # Strip out inline bulk whitespace
# for line in lines_without_inline_comments:
#     while '  ' in line:
#         line = line.replace('  ', ' ')
#     lines_without_inline_whitespace.append(line)
#     print(f"line: {line}")

# # Grab multi-line entries and smash them together.
# consolidated = False
# while consolidated == False:

#     flag_loop_again = False
#     for i, line in enumerate(lines_without_inline_whitespace):
#         # if line[0] in [ ' ', '{', '}' ]:
#         if line[0] in [ '{', '}' ]:
#             # Convert to dict
#         if line[0] == ' ':
#             # Smash list together
#             print(f"[HIT!]: {line}")
#             lines_without_inline_whitespace[i-1] = lines_without_inline_whitespace[i-1].rstrip() + line.strip()
#             print(f"Updated: {lines_without_inline_whitespace[i-1]}")
#             lines_without_inline_whitespace.pop(i)
#             flag_loop_again = True
#             break

#     if flag_loop_again == True:
#         pass
#     else:
#         consolidated = True

# for line in lines_without_inline_whitespace:
#     print(line.strip())




# sed '/^\s*\/\*/,/^\s*\*\//d;/^\s*#/d' terraform.tfvars > terraform_no_comments.tfvars
import json

data = {}
default_tags = {}

with open('terraform_no_comments.tfvars', 'r') as file:
    lines = file.readlines()
    lines_array = [line.strip() for line in lines]

    # Handle `default tags` edge case: extract this value specifically into a dict and pop lines.
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

    # Pop offending values from right side of array to ensure indices don't shift.
    for i in reversed(indices_to_pop):
        lines_array.pop(i)


print(default_tags)
exit()
        


    

#     for line in file:
#         if "=" in line:
#             key, value = [x.strip() for x in line.split('=', 1)]
#             if value.startswith('"') and value.endswith('"'):
#                 data[key] = value.strip('"')
#             elif value.lower() == 'true':
#                 data[key] = True
#             elif value.lower() == 'false':
#                 data[key] = False
#             else:
#                 data[key] = value
# with open('output.json', 'w') as file:
#     json.dump(data, file, indent=4)






# print("lines_without_bulk_comments is: ", lines_without_bulk_comments)


# for line in lines_without_bulk_comments:
#     if line[0] in [ ' ', '{', '}' ]:
#         pass
#     else:
#         print(f"line is: {line}")
#         k,v = line.split('=', maxsplit=1)
#         print(f"k is: {k}")
#         k = k.strip()
#         v = v.strip()
#         line = f"{k} = {v}"
#         lines_without_compound_entries.append(line)

# print("lines_without_compound_entries is: ", lines_without_compound_entries)

exit()





flag_skip_block_comment = False
with open('terraform.tfvars', 'r') as file:
    lines = file.readlines()
    for line in lines:
        if line.strip() == "":
            pass
        elif line.startswith('#'):
            pass
        elif line.startswith("/*"):
            flag_skip_block_comment = True
            pass
        elif line.startswith("*/"):
            flag_skip_block_comment = False
            pass
        elif flag_skip_block_comment == True:
            pass
        else:
            print(line)
            # Purge inline comments
            line = line.split('#')[0]
            line = line.strip()

            # 
            kv = line.split('=')
            key = kv[0].strip()
            value = kv[1].strip()   # Necessary to remove whitespace to right of '='

            # Cleanse values of after-the-value comments/whitespace. ALL values starts a strings since I've read from a file and split line.
            # Conventional value starting and ending with a double-quote. Extract value between doublequotes and process no further.
            # Number, array, doublequoted string with space/hash after.
            if value.startswith('"'):
                value = value.split('"')[1]
            else:
                value = value.strip()
            tfvars[key] = value

print("------------------------------")


def only_one_true_set(values: List, qualifier: str) -> None:
    count = values.count('true')
    if count > 1:
        raise AssertionError(f'[ERROR]: {qualifier} flags must have only one true.')
    elif count < 1:
        raise AssertionError(f'[ERROR]: {qualifier} flags must have one true.')
    else: 
        print(f"[OK]: {qualifier} flags.")

## ----- Check Starting Flags
# Check VPC
flags = ["flag_create_new_vpc", "flag_use_existing_vpc"]
values = [ tfvars[flag] for flag in flags]
only_one_true_set(values, "VPC")


# Check DB
flags = ["flag_create_external_db", "flag_use_existing_external_db", "flag_use_container_db" ]
values = [ tfvars[flag] for flag in flags]
only_one_true_set(values, "DB")


# Check Redis
flags = ["flag_create_external_redis", "flag_use_existing_external_redis", "flag_use_container_redis" ]
values = [ tfvars[flag] for flag in flags]
only_one_true_set(values, "REDIS")


# Check Load Balancer
flags = ["flag_create_load_balancer", "flag_generate_private_cacert", "flag_use_existing_private_cacert", "flag_do_not_use_https" ]
values = [ tfvars[flag] for flag in flags]
only_one_true_set(values, "LOAD_BALANCER")


# Check SMTP
flags = ["flag_use_aws_ses_iam_integration", "flag_use_existing_smtp" ]
values = [ tfvars[flag] for flag in flags]
only_one_true_set(values, "SMTP")


## ----- Private CA Checks (if applicable)
if tfvars["flag_generate_private_cacert"] == "true":

    if not tfvars["bucket_prefix_for_new_private_ca_cert"].startswith('s3://'):
        raise AssertionError('[ERROR]: Field `bucket_prefix_for_new_private_ca_cert` must start with `s3://`')
    

if tfvars["flag_use_existing_private_cacert"] == "true":
    
    print("\t[REMINDER]: Ensure you have added your private .crt and .key files to `assets/customcerts`.")
    print('\t[REMINDER]: Ensure you have updated tfvars `existing_ca_cert_file` and `existing_ca_key_file`.')


## ----- VPC Settings Check
if tfvars["flag_use_existing_vpc"] == 'true':
    if tfvars["vpc_existing_id"] == "REPLACE_ME":
        raise AssertionError('[ERROR]: Please specify pre-existing VPC to use.')
    
if tfvars["flag_create_new_vpc"] == 'true':
    pass


## ----- Security Group Reminders
if ( tfvars["sg_ingress_cidrs"] == "0.0.0.0/0"):
    print('[REMINDER]: Security group rule for HTTP(s) ingress is loose by default. Please consider tightening.')

if ( tfvars["sg_ssh_cidrs"] == "0.0.0.0/0" ):
    print('[REMINDER]: Security group rule for SSH ingress is loose by default. Please consider tightening.')


## ----- Database Checks (External)
if ( tfvars["db_engine"] == "mysql" ) and ( '8' in tfvars["db_engine_version"]):
    print("[WARNING]: You appear to be using MySQL 8. Please note that additional TOWER_DB_URL configuration may be required.")


## ----- ALB Cert
if ( tfvars["flag_create_load_balancer"] == "true"):
    if tfvars["alb_certificate_arn"] == "REPLACE_ME":
        raise AssertionError("Please provide an ARN for the `alb_certificate_arn` field.")


## ----- TOWER GOTCHAS
# Ensure secrets not present
if ( 'tower_jwt_secret' in tfvars ):
    raise AssertionError("[ERROR]: Do not specify `tower_jwt_secret`. This value will be sourced from SSM.")

if ( 'tower_crypto_secretkey' in tfvars ):
    raise AssertionError("[ERROR]: Do not specify `tower_crypto_secretkey`. This value will be sourced from SSM.")

if ( 'tower_license' in tfvars ):
    raise AssertionError("[ERROR]: Do not specify `tower_license`. This value will be sourced from SSM.")

if ( 'tower_db_user' in tfvars ):
    raise AssertionError("[ERROR]: Do not specify `tower_db_user`. This value will be sourced from SSM.")

if ( 'tower_db_password' in tfvars ):
    raise AssertionError("[ERROR]: Do not specify `tower_db_password`. This value will be sourced from SSM.")

if ( 'tower_smtp_user' in tfvars ):
    raise AssertionError("[ERROR]: Do not specify `tower_smtp_user`. This value will be sourced from SSM.")

if ( 'tower_smtp_password' in tfvars ):
    raise AssertionError("[ERROR]: Do not specify `tower_smtp_password`. This value will be sourced from SSM.")


# URL
if ( tfvars["tower_server_url"].startswith('http') ):
    raise AssertionError("[ERROR]: Field `tower_server_url` must not have a prefix.")

if ( tfvars["tower_server_port"] != "8000" ):
    print("[REMINDER]: Your Tower instance appears to be using a non-default port (8000). Please ensure your Docker-Compose file is updated accordingly.")


# Database
if ( tfvars["tower_db_url"].startswith('jdbc:') ) or ( tfvars["tower_db_url"].startswith('mysql:') ):
    raise AssertionError("[ERROR] Do not include protocol in `tower_db_url`. Start with hostname.")

if ( tfvars["tower_db_driver"] != "org.mariadb.jdbc.Driver" ):
    print(tfvars["tower_db_driver"])
    raise AssertionError("[ERROR] Field `tower_db_driver` must be `org.mariadb.jdbc.Driver`.")

if ( tfvars["tower_db_dialect"] != "io.seqera.util.MySQL55DialectCollateBin" ):
    raise AssertionError("[ERROR] Field `tower_db_dialect` must be `org.mariadb.jdbc.Driver`.")

if ( tfvars["flag_use_container_db"] == "true" ):
    
    if ( tfvars["tower_db_url"] != "db:3306" ):
        print("[REMINDER] You appear to be using a non-standard db container name or port. Please verify Docker-Compose config is updated accordingly.")

if ( tfvars["flag_use_existing_external_db"] == "true" ):
    print("[REMINDER] You are using a pre-existing external database. Please ensure you create the database, user, and append the database name to `tower_db_url`.")


# Redis
if ( tfvars["tower_redis_url"] != "redis://redis:6379" ):
    raise AssertionError("[REMINDER] You appear to be using a non-standard redis container setting. Please verify Docker-Compose config is updated accordingly.")


# Email
if ( tfvars['flag_use_aws_ses_iam_integration'] == "true" ):

    if ( "amazonaws.com" not in tfvars["tower_smtp_host"] ):
        raise AssertionError("[ERROR]: You want to SES but are not pointing to an SES endpoint. Please fix.")
    
    if ( tfvars["tower_smtp_port"] != "587" ):
        raise AssertionError("[ERROR]: SES integration requires port 587. Plese fix.")


# Tower root user
if ( tfvars["tower_root_user"] in ["REPLACE_ME", ""] ):
    raise AssertionError("[ERROR]: Please populate `tower_root_user` with an email address.")

if ( ',' in tfvars["tower_root_user"] ):
    raise AssertionError("[ERROR]: Please populate `tower_root_user` with only a single email address.")


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
# TO DO: Modify tower_root_user check once comma-delimited string can be populated in yaml.