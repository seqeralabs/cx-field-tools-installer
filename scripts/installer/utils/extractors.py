import os
import sys
from pathlib import Path

import hcl2

base_import_dir = Path(__file__).resolve().parents[2]
if base_import_dir not in sys.path:
    sys.path.append(str(base_import_dir))


## ------------------------------------------------------------------------------------
## Convert terraform.tfvars to a Python dict.
##
## Earlier revisions of this file shelled out to the `tmccombs/hcl2json` Docker image
## (see git history). That worked but required a Docker daemon to be running anywhere
## the installer was exercised — including CI and `terraform test` runs that touch the
## connection-strings external data source. Switching to `python-hcl2` removes the
## daemon dependency in exchange for one in-process Python library.
##
## WARNING: do not emit anything to stdout from this module — the data.external block in
## modules/connection_strings/v1.0.0/main.tf relies on a single JSON line on stdout from
## generate_db_connection_string.py, and any extra output corrupts the protocol.
## ------------------------------------------------------------------------------------


def _unwrap_hcl_strings(value):
    """python-hcl2 returns string scalars with their surrounding double quotes preserved
    (so `foo = "bar"` becomes the Python string `'"bar"'`). The downstream consumers
    expect plain Python strings. Walk the parsed structure and strip those.
    """
    if isinstance(value, str):
        if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
            return value[1:-1]
        return value
    if isinstance(value, list):
        return [_unwrap_hcl_strings(item) for item in value]
    if isinstance(value, dict):
        return {key: _unwrap_hcl_strings(val) for key, val in value.items()}
    return value


def get_tfvars_as_json():
    """Parse the project-root `terraform.tfvars` into a dict."""
    tfvars_path = os.path.abspath("terraform.tfvars")
    if not os.path.exists(tfvars_path):
        raise FileNotFoundError(
            f"terraform.tfvars file not found in path: {tfvars_path}."
        )

    with open(tfvars_path) as fp:
        parsed = hcl2.load(fp)

    return _unwrap_hcl_strings(parsed)


tf_vars_json_payload = get_tfvars_as_json()
