#!/usr/bin/env python3
import os
import json
import sys
from types import SimpleNamespace
from typing import List

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

# Extract tfvars just like we do with the Python validation script
os.chdir(project_root)
data_dictionary = get_tfvars_as_json()
data = SimpleNamespace(**data_dictionary)

# Much simpler way to get variable passed in (via Terraform sending to stdin)
query = json.load(sys.stdin)
# query = SimpleNamespace(**query)
## ------------------------------------------------------------------------------------


with open("query.json", "w") as file:
    file.write(str(query))

# Determine kinda of DNS record to create
dns_create_alb_record = True if (data.flag_create_load_balancer and not data.flag_create_hosts_file_entry) else False
dns_create_ec2_record = True if (not data.flag_create_load_balancer and not data.flag_create_hosts_file_entry) else False

if data.flag_create_route53_private_zone == True:
    dns_zone_id = query.aws_route53_zone


def return_tf_payload(status: str, value: str):
    payload = {'status': status, 'value': value}
    print(json.dumps(payload))


if __name__ == '__main__':
    return_tf_payload("0", "abc")
    
    exit(0)