from datetime import datetime
import json
import logging
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

base_import_dir = Path(__file__).resolve().parents[2]
if base_import_dir not in sys.path:
    sys.path.append(str(base_import_dir))

from installer.utils.logger import logger

## ------------------------------------------------------------------------------------
## Convert terraform.tfvars to JSON
## Notes:
##   1. As of May 16, 2025, the bespoke parser to convert terraform.tfvars into json is replaced with a new container-based
##      solution from tmccombs/hcl2json. The home-rolled parser was originally created to avoid introducing packages from 
##      the internet. Due to more complicated parsing needs, the new parser solution has been implemented. 
##      To refer to the previous parser, please refer to previous Git histroy.
##
##   2. The new parser relies on the containerized solution provided here: https://github.com/tmccombs/hcl2json. 
##      Seqera will vendor their own copy of the image within Harbor.
##
## WARNING / REMINDER: DONT ADD ANY stdout emissions in this logic or you'll break the TF `external` mechanism!!
## ------------------------------------------------------------------------------------


def get_tfvars_as_json():
    """
    Uses the `tmccombs/hcl2json` Docker image to convert `terraform.tfvars` into JSON format and return it as 
    a Python dictionary.
    """
    
    # Check for tfvars
    tfvars_path = os.path.abspath("terraform.tfvars")
    if not os.path.exists(tfvars_path):
        raise FileNotFoundError("terraform.tfvars file not found in current directory.")

    # Because this is a 3rd party container, we are locking down as much as possible for security reasons:
    # Single local file mounted as read-only, non-root user, disabled network capabilities, and
    # use of immutable container hash fingerprint over mutable tag.
    cmd = [
            "docker", "run",
            "--platform", "linux/amd64",
            "-i", "--rm",
            "-v", f"{os.getcwd()}/terraform.tfvars:/tmp/terraform.tfvars:ro",
            "--user", "1000:1000",
            "--network", "none",
            #"tmccombs/hcl2json@sha256:312ac54d3418b87b2ad64f82027483cb8b7750db6458b7b9ebe42ec278696e96",
            "ghcr.io/seqeralabs/cx-field-tools-installer/hcl2json@sha256:48af2029d19d824ba1bd1662c008e691c04d5adcb055464e07b2dc04980dcbf5",
            "/tmp/terraform.tfvars"
        ]
    
    # Assign result to variable (to then be returned directly or written to file for debugging)
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Capture Docker runtime failures
    if result.returncode != 0:
        raise RuntimeError(f"Docker command failed:\nSTDERR: {result.stderr.strip()}")

    # Capture Docker stdout
    payload = result.stdout.strip()

    # Redirect output to temporary JSON file (debugging only)
    if logging.getLevelName(logger.getEffectiveLevel()) == "DEBUG":
        timestamp = datetime.now().strftime("%Y_%b%d_%I-%M%p")
        with tempfile.NamedTemporaryFile(delete=False, prefix=f"terraform_tfvars_{timestamp}_", suffix=".json", mode='w+', dir="/tmp") as temp_output:
            temp_output.write(payload)
    
    # Capture invalid json errors
    try:
        # logger.info(payload)
        return json.loads(payload)  # json.loads converts json string to python object.
    except json.JSONDecodeError as e:
        raise RuntimeError("Failed to decode Docker output as JSON.") from e

tf_vars_json_payload = get_tfvars_as_json()
