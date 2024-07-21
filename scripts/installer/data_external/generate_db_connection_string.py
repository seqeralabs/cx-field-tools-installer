#!/usr/bin/env python3
import json
import sys
from types import SimpleNamespace

sys.dont_write_bytecode = True


# Connection string modifiers
mysql8_connstring = "allowPublicKeyRetrieval=true&useSSL=false"
v24plus_connstring = "permitMysqlScheme=true"


def return_tf_payload(status: str, value: str):
    payload = {"status": status, "value": value}
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


if __name__ == "__main__":

    # Much simpler way to get variable passed in (via Terraform sending to stdin)
    query = json.load(sys.stdin)
    data = SimpleNamespace(**query)

    # Get engine_version depending on whether container DB or RDS instance is in play
    if data.flag_use_container_db:
        engine_version = data.db_container_engine_version
    else:
        engine_version = data.db_engine_version

    connection_string = generate_connection_string(
        engine_version, data.tower_container_version
    )
    return_tf_payload("0", connection_string)

    exit(0)
