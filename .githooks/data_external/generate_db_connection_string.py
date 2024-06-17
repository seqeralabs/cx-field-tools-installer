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
from utils.extractors import get_tfvars_as_json
#from utils.logger import logger
from utils.logger import external_logger #as logger

# Extract tfvars just like we do with the Python validation script
os.chdir(project_root)
data_dictionary = get_tfvars_as_json()
data = SimpleNamespace(**data_dictionary)

# Much simpler way to get variable passed in (via Terraform sending to stdin)
query = json.load(sys.stdin)
query = SimpleNamespace(**query)
## ------------------------------------------------------------------------------------


# Get engine_version depending on whether container DB or RDS instance is in play
engine_version = data.db_container_engine_version if data.flag_use_container_db else data.db_engine_version

# Connection string modifiers
mysql8_connstring = "allowPublicKeyRetrieval=true&useSSL=false"
v24plus_connstring = "permitMysqlScheme=true"


def return_tf_payload(status: str, value: str):
    external_logger.debug(f"Value is: {value}")
    payload = {'status': status, 'value': value}
    external_logger.debug(f"Payload is: {payload}")

    print(json.dumps(payload))
    # MemoryHandler configured to flush on `logger.error`. Flush once after TF gets its payload (above).
    external_logger.error("Flushing.")     #external_logger.flush()
    exit(0)


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


if __name__ == '__main__':
    connection_string = generate_connection_string(engine_version, data.tower_container_version)
    return_tf_payload("0", connection_string)