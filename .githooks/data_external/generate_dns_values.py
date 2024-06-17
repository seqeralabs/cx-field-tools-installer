#!/usr/bin/env python3
import os
import json
import sys
from types import SimpleNamespace
from typing import Any, List

sys.dont_write_bytecode = True


## ------------------------------------------------------------------------------------
## Extract TFvars and get query values
## ------------------------------------------------------------------------------------
# NOTE! This part is a bit convoluted but there's a method to the madness:
#   - Script executes from `~/cx-field-tools-installer`. 
#   - Change into .githooks (to avoid the `.` import problem), import, return to project root to extract tfvars.
#   - Error thrown without workaround: `ImportError: attempted relative import with no known parent package`
#   - Query object to receive objects via TF data call (i.e. resources)
project_root = os.getcwd()
os.chdir(f"{project_root}/.githooks")
sys.path.append(".")
from utils.extractors import get_tfvars_as_json #convert_tfvars_to_dictionary
from utils.logger import external_logger

# Extract tfvars just like we do with the Python validation script
os.chdir(project_root)
data_dictionary = get_tfvars_as_json()
data = SimpleNamespace(**data_dictionary)

# Much simpler way to get variable passed in (via Terraform sending to stdin)
query = json.load(sys.stdin)
# query = SimpleNamespace(**query)
## ------------------------------------------------------------------------------------


# https://www.reddit.com/r/learnpython/comments/y02net/is_there_a_better_way_to_store_full_dictionary/
def getDVal(d : dict, listPath : list) -> Any:
    '''Recursively loop through a dictionary object to get to the target nested key.'''
    for key in listPath:
        d = d[key]
    return d

# Vars
dns_zone_mappings = {
    "flag_create_route53_private_zone":             ("zone_private_new",        [0, 'id']),
    "flag_use_existing_route53_private_zone":       ("zone_private_existing",   [0, 'id']),
    "flag_use_existing_route53_public_zone":        ("zone_public_existing",    [0, 'id']),
}

# Transformed dictionary nested into flat dicionary so value can be passed around.
# I don't love this approach but can't find a cleaner/simpler way right now.
dns_instance_ip_mappings = {
    "flag_make_instance_private":                   ("tower_host_instance", ['private_ip']),
    "flag_make_instance_private_behind_public_alb": ("tower_host_instance", ['private_ip']),
    "flag_private_tower_without_eice":              ("tower_host_instance", ['private_ip']),
    "flag_make_instance_public":                    ("tower_host_eip",      [0, 'public_ip'])
}


def populate_values(query):

    external_logger.debug(f"Query is: {query}")

    # Baseline variables
    dns_zone_id = ""
    dns_instance_ip = ""

    # Determine kinda of DNS record to create
    # dns_create_alb_record = True if (data.flag_create_load_balancer and not data.flag_create_hosts_file_entry) else False
    # dns_create_ec2_record = True if (not data.flag_create_load_balancer and not data.flag_create_hosts_file_entry) else False

    for k,v in dns_zone_mappings.items():
        external_logger.debug(f"k is : {k}; and v is: {v}")
        tf_obj, dpath = v
        tf_obj_json = json.loads(query[tf_obj])
        dns_zone_id = getDVal(tf_obj_json, dpath) if data_dictionary[k] else dns_instance_ip


    for k,v in dns_instance_ip_mappings.items():
        '''`aws_instance.ec2.private_ip` vs `aws_eip.towerhost[0].public_ip`'''
        tf_obj, dpath = v
        tf_obj_json = json.loads(query[tf_obj])
        dns_instance_ip = getDVal(tf_obj_json, dpath) if data_dictionary[k] else dns_instance_ip

    values = {
        # "dns_create_alb_record": dns_create_alb_record,
        # "dns_create_ec2_record": dns_create_ec2_record,

        "dns_zone_id": dns_zone_id,
        "dns_instance_ip": dns_instance_ip
    }

    return values


def convert_booleans_to_strings(payload: dict) -> dict: 
    for k,v in payload.items():
        external_logger.debug(f"k is {k} and v is {v}.")
        if isinstance(v, bool):
            payload[k] = "true" if v == True else "false"
    return payload
        

def return_tf_payload(status: str, values: dict):
    external_logger.debug(f"Payload is: {values}")

    payload = {'status': status, **values}
    payload = convert_booleans_to_strings(payload)
    print(json.dumps(payload))

    external_logger.error("Flushing.")
    exit(0)


if __name__ == '__main__':
    values = populate_values(query)
    return_tf_payload("0", values)