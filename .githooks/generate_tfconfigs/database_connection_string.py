#!/usr/bin/env python3
import os
import json
import sys
from types import SimpleNamespace
from typing import List

sys.dont_write_bytecode = True

# NOTE! This part is a bit convoluted but there's a method to the madness:
# - Script executes from `/~/cx-field-tools-installer`. 
# - Need to change dir into .githooks (to avoid the `.` import problem), import, then return to project root so the extractor can find tfvars.
# - Error this is solving: `ImportError: attempted relative import with no known parent package``
project_root = os.getcwd()
os.chdir(f"{project_root}/.githooks")
sys.path.append(".")
from utils.extractors import get_tfvars_as_json #convert_tfvars_to_dictionary

# Extract tfvars just like we do with the Python validation script
os.chdir(project_root)
data_dictionary = get_tfvars_as_json()
data = SimpleNamespace(**data_dictionary)

# Connection string modifiers
mysql8_connstring = "allowPublicKeyRetrieval=true&useSSL=false"
v24plus_connstring = "permitMysqlScheme=true"


def return_tf_payload(status: str, value: str):
    payload = {'status': status, 'value': value}
    print(json.dumps(payload))


def generate_connection_string(mysql8: str, v24plus: str):
    connection_string = ""
    add_mysql8 = False
    add_v24plus = False

    if mysql8.startswith("8."): 
        add_mysql8 = True

    if v24plus >= "v24":
        add_v24plus = True

    if add_mysql8 and add_v24plus:
        connection_string = f"?{mysql8_connstring}&{v24plus_connstring}"
    elif add_mysql8 and not add_v24plus:
        connection_string = f"?{mysql8_connstring}"
    elif not add_mysql8 and add_v24plus:
        connection_string = f"?{v24plus_connstring}"

    return connection_string


if data.flag_use_container_db:
    connection_string = generate_connection_string(data.db_container_engine_version, data.tower_container_version)
else:
    connection_string = generate_connection_string(data.db_engine_version, data.tower_container_version)

return_tf_payload("0", connection_string)
exit(0)