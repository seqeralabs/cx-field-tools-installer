import os
import shutil
import subprocess
from pathlib import Path

from tests.utils.cache.cache import hash_cache_key, normalize_whitespace
from tests.utils.config import FP
from tests.utils.filehandling import FileHelper


## ------------------------------------------------------------------------------------
## Subprocess Utility Functions
## ------------------------------------------------------------------------------------
# NOTE: PIPE needed to capture plan output (for apply), but causes noisy console.
#       Replaced with shell-type subprocess.run commands Bash redirect output to files.
def execute_subprocess(command: str) -> bytes:
    """
    Execute a subprocess command.
    """
    result = subprocess.run(
        command,
        check=True,
        # stdout=subprocess.PIPE,
        stdout=subprocess.DEVNULL,  # > /dev/null
        stderr=subprocess.STDOUT,  # 2>&1
        shell=True,
    ).stdout

    return result


## ------------------------------------------------------------------------------------
## Utility Class
## ------------------------------------------------------------------------------------
# Keep all file method helpers in a single class to simplify imports.
class TF:
    """
    Terraform command execution helpers.
      - Plan based on core tfvars, core override, and testcase override.
      - Targeted apply/destroy available if necessary. eg.
        - `terraform apply   --auto-approve tfpan`
        - `terraform apply   --auto-approve -target=null_resource.my_resource`
        - `terraform destroy --auto-approve`
        - `terraform destroy --auto-approve -target=null_resource.my_resource`
    """

    @staticmethod
    def plan(qualifier: str = "") -> None:
        """Run terraform plan with caching support."""
        files_to_purge = [FP.TFPLAN_FILE_LOCATION, FP.TFPLAN_JSON_LOCATION]

        for file in files_to_purge:
            Path(file).unlink(missing_ok=True)

        command = f"terraform plan {qualifier} -out=tfplan -refresh=false && terraform show -json tfplan > tfplan.json"
        execute_subprocess(command)

    @staticmethod
    def apply(qualifier: str = "") -> None:
        """Run terraform apply (defaults to using tfplan)."""
        qualifier = qualifier if len(qualifier) > 0 else "tfplan"
        command = f"terraform apply --auto-approve {qualifier}"
        execute_subprocess(command)

    @staticmethod
    def destroy(qualifier: str = "") -> None:
        """Run terraform destroy."""
        qualifier = qualifier if len(qualifier) > 0 else ""
        command = f"terraform destroy --auto-approve {qualifier}"
        execute_subprocess(command)


## ------------------------------------------------------------------------------------
## Plan Generation
## ------------------------------------------------------------------------------------
# Find a cached Terraform plan, or generate new one with fresh set of tfvars files.
def prepare_plan(tf_modifiers: str, qualifier: str = "") -> dict:
    """Generate override.auto.tfvars and run terraform plan with caching.

    Args:
        tf_modifiers: Terraform variable overrides
        qualifier: Additional modifier to add to cache key (e.g '-target=null_resource.my_resource')

    Returns:
        Terraform plan JSON data
    """

    # Cache key affected by whitespace. Standardize before hashing.
    tf_modifiers = normalize_whitespace(tf_modifiers)
    cache_key = hash_cache_key(tf_modifiers, qualifier)

    # Always try to use cached results (for speed and performance)
    cached_plan = f"{FP.CACHE_PLAN_DIR}/plan_{cache_key}"
    cached_json = f"{FP.CACHE_PLAN_DIR}/plan_{cache_key}.json"

    # Write normalized tf_modifiers to the 'override.auto.tfvars' file.
    FileHelper.write_file(FP.TFVARS_AUTO_OVERRIDE_DST, tf_modifiers)

    if os.path.exists(cached_json):
        print(f"Cache hit! {cache_key}")
        shutil.copy(cached_plan, FP.TFPLAN_FILE_LOCATION)
        shutil.copy(cached_json, FP.TFPLAN_JSON_LOCATION)
        return FileHelper.read_json(FP.TFPLAN_JSON_LOCATION)

    # Cache miss. Create plan files and cache for future use.
    print(f"Cache miss. {cache_key}")
    TF.plan(qualifier)

    shutil.copy(FP.TFPLAN_FILE_LOCATION, cached_plan)
    shutil.copy(FP.TFPLAN_JSON_LOCATION, cached_json)

    return FileHelper.read_json(FP.TFPLAN_JSON_LOCATION)
