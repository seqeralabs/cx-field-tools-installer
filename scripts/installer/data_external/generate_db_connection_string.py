#!/usr/bin/env python3

import sys
from pathlib import Path

import json
from types import SimpleNamespace

# https://stackoverflow.com/questions/27844088/python-get-directory-two-levels-up
# Assumes following path: .. > installer > validation > check_configuration.py
grandparent_dir = Path(__file__).resolve().parents[2]
sys.path.append(str(grandparent_dir))

from installer.utils.extractors import tf_vars_json_payload

## ------------------------------------------------------------------------------------
## WARNING / REMINDER: DONT ADD ANY stdout emissions (beyond a single print of the payload we are returning)
# in this logic or you'll break the TF `external` mechanism!!
## ------------------------------------------------------------------------------------

BLANK_CONNSTRING = ""
MYSQL8_CONNSTRING = "allowPublicKeyRetrieval=true&useSSL=false"
PLATFORM_CONNSTRING = "permitMysqlScheme=true"


def return_tf_payload(status: str, value: str):
    payload = {"status": status, "value": value}
    print(json.dumps(payload))


def generate_connection_string(data: SimpleNamespace):
    # master supports only Platform v26.1.x, which always wants `permitMysqlScheme=true`.
    # MySQL 8.x adds the public-key-retrieval flag on top.
    if data.flag_use_container_db:
        db_engine = data.db_container_engine_version
    else:
        db_engine = data.db_engine_version

    if db_engine.startswith("8."):
        return f"?{MYSQL8_CONNSTRING}&{PLATFORM_CONNSTRING}"

    return f"?{PLATFORM_CONNSTRING}"


if __name__ == "__main__":

    # Extract tfvars just like we do with the Python validation script
    data_dictionary = tf_vars_json_payload
    data = SimpleNamespace(**data_dictionary)

    return_tf_payload("0", generate_connection_string(data))
    exit(0)
