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

BLANK_CONNSTRING = ""
MYSQL8_CONNSTRING = "allowPublicKeyRetrieval=true&useSSL=false"
V24PLUS_CONNSTRING = "permitMysqlScheme=true"


def return_tf_payload(status: str, value: str):
    payload = {"status": status, "value": value}
    print(json.dumps(payload))


# def generate_connection_string(mysql8: str, v24plus: str):
def generate_connection_string(data: SimpleNamespace):

    if data.flag_use_container_db:
        db_engine = data.db_container_engine_version
    else:
        db_engine = data.db_engine_version

    if db_engine.startswith("8."):
        add_mysql8 = True
    else:
        add_mysql8 = False

    if data.tower_container_version >= "v24":
        add_v24plus = True
    else:
        add_v24plus = False

    if add_mysql8 and add_v24plus:
        connection_string = f"?{MYSQL8_CONNSTRING}&{V24PLUS_CONNSTRING}"
    elif add_mysql8 and not add_v24plus:
        connection_string = f"?{MYSQL8_CONNSTRING}"
    elif not add_mysql8 and add_v24plus:
        connection_string = f"?{V24PLUS_CONNSTRING}"
    else:
        connection_string = BLANK_CONNSTRING

    return connection_string


if __name__ == "__main__":

    # Extract tfvars just like we do with the Python validation script
    data_dictionary = tf_vars_json_payload
    data = SimpleNamespace(**data_dictionary)

    return_tf_payload("0", generate_connection_string(data))
    exit(0)
