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

    # Deployment machines are a mix of Intel and Mac. Dynamically assess chip architecture to pass correct container architecture qualifier.
    # For Mac Silicon, if no ARM image, without `--paltform``, Docker will pull the amd image and run automatically.
    # To make logic simpler, we set `--platform` manually to amd if machine architecture is arm64
    arch = platform.machine().lower()
    if arch in ["x86_64", "amd64"]:
        arch = "linux/amd64"
    elif arch == "arm64":
        arch = "linux/amd64" 
    else:
        raise Exception("Chip-type is not x86_64, AMD64, or arm64.")

    # Because this is a 3rd party container, we are locking down as much as possible for security reasons:
    # Single local file mounted as read-only, non-root user, disabled network capabilities, and
    # use of immutable container hash fingerprint over mutable tag.
    timestamp = datetime.now().strftime("%Y_%b%d_%I-%M%p")
    cmd = [
            "docker", "run",
            "--platform", arch,
            "-i", "--rm",
            "-v", f"{os.getcwd()}/terraform.tfvars:/tmp/terraform.tfvars:ro",
            "--user", "1000:1000",
            "--network", "none",
            "tmccombs/hcl2json@sha256:312ac54d3418b87b2ad64f82027483cb8b7750db6458b7b9ebe42ec278696e96",
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
        with tempfile.NamedTemporaryFile(delete=False, prefix=f"terraform_tfvars_{timestamp}_", suffix=".json", mode='w+', dir="/tmp") as temp_output:
            temp_output.write(payload)
    
    # Capture invalid json errors
    try:
        logger.info(payload)
        return json.loads(payload)
    except json.JSONDecodeError as e:
        raise RuntimeError("Failed to decode Docker output as JSON.") from e

tf_vars_json_payload = get_tfvars_as_json()
