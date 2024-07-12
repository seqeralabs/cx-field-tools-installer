#!/usr/bin/env python3
import os
import json
import sys
from types import SimpleNamespace

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
from utils.common_data_external_functions import getDVal, return_tf_payload

os.chdir(project_root)
data_dictionary = get_tfvars_as_json()
data = SimpleNamespace(**data_dictionary)

# Much simpler way to get variable passed in (via Terraform sending to stdin)
query = json.load(sys.stdin)
# query = SimpleNamespace(**query)
## ------------------------------------------------------------------------------------


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
        "dns_zone_id": dns_zone_id,
        "dns_instance_ip": dns_instance_ip
    }

    return values


if __name__ == '__main__':
    values = populate_values(query)
    return_tf_payload("0", values)