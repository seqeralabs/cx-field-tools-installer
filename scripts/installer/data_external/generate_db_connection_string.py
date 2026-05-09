#!/usr/bin/env python3

import json
from pathlib import Path
import sys
from types import SimpleNamespace


# https://stackoverflow.com/questions/27844088/python-get-directory-two-levels-up
# Assumes following path: .. > installer > validation > check_configuration.py
grandparent_dir = Path(__file__).resolve().parents[2]
sys.path.append(str(grandparent_dir))

from installer.utils.extractors import get_tfvars_as_json  # noqa: E402  (sys.path manipulation above)

## ------------------------------------------------------------------------------------
## WARNING / REMINDER: DONT ADD ANY stdout emissions (beyond a single print of the payload we are returning)
# in this logic or you'll break the TF `external` mechanism!!
## ------------------------------------------------------------------------------------

PLATFORM_CONNSTRING = "?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true"


def return_tf_payload(status: str, value: str):
    """Emit a Terraform `external` data-source JSON payload to stdout."""
    payload = {"status": status, "value": value}
    print(json.dumps(payload))


def generate_connection_string(data: SimpleNamespace):
    """Build the Tower DB connection-string suffix from the tfvars-derived data."""
    # TODO: Remove once terraform variable validation in place.
    if data.flag_use_container_db:
        db_engine = data.db_container_engine_version
    else:
        db_engine = data.db_engine_version

    if not db_engine.startswith("8."):
        # Check should not occur here. Better to do a Terraform variables validation.
        # TODO: Remove once terraform variable validation in place.
        pass

    return PLATFORM_CONNSTRING


if __name__ == "__main__":
    # Extract tfvars just like we do with the Python validation script
    data_dictionary = get_tfvars_as_json()
    data = SimpleNamespace(**data_dictionary)

    return_tf_payload("0", generate_connection_string(data))
    sys.exit(0)
