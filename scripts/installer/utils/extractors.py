from datetime import datetime
import json
import os
import subprocess
import tempfile

## ------------------------------------------------------------------------------------
## Convert terraform.tfvars to JSON
## Notes:
##   1. Deprecation Notice: Starting May 16, 20205, the bespoke parser to convert terraform.tfvars into json will be replaced with a new container based solution from tmccombs/hcl2json. The home-rolled parser was originally created to avoid introducing packages from the internet. Due to more complicated parsing needs, the new parser solution has been implemented. To refer to the previous parser, please refer to previous Git histroy.
##   2. The new parser relies on the containerized solution provided here: https://github.com/tmccombs/hcl2json. Seqera will vendor their own copy of the image within Harbor.
## ------------------------------------------------------------------------------------


def get_tfvars_as_json():
    """Uses the `tmccombs/hcl2json` Docker image to convert `terraform.tfvars` into JSON format and return it as a Python dictionary."""
    
    tfvars_path = os.path.abspath("terraform.tfvars")
    timestamp = datetime.now().strftime("%Y_%b%d_%I-%M%p")
    
    if not os.path.exists(tfvars_path):
        raise FileNotFoundError("terraform.tfvars file not found in current directory.")

    try:
        # Create a temporary file for Docker output
        # delete=True would delete the tmp file as soon as the `with` block exits but we need the file further down
        with tempfile.NamedTemporaryFile(delete=False, prefix=f"terraform_tfvars_{timestamp}_", suffix=".json", dir="/tmp") as temp_output:
            output_path = temp_output.name

        cmd = [
                "docker", "run",
                "--platform", "linux/amd64",
                "-i", "--rm",
                "-v", f"{os.getcwd()}:/tmp:ro",            # read-only mount
                "--user", "1000:1000",                     # non-root user (adjust UID/GID if needed or user current user)
                "--network", "none",                       # disable network
                "tmccombs/hcl2json@sha256:312ac54d3418b87b2ad64f82027483cb8b7750db6458b7b9ebe42ec278696e96",
                "/tmp/terraform.tfvars"
            ]

        # Redirect output to temporary JSON file
        with open(output_path, "w") as outfile:
            subprocess.run(cmd, stdout=outfile, stderr=subprocess.PIPE, check=True)

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Docker command failed: {e.stderr.decode().strip()}")

    # Read and return the parsed JSON
    with open(output_path, "r") as json_file:
        return json.load(json_file)
    
    # TODO: Should script clean up after using the json
    # os.remove(output_path)