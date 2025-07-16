from pickle import FALSE
from numpy.core.fromnumeric import nonzero
import pytest

import os
from pathlib import Path
import shutil
import sys
import hashlib
from typing import Dict, Any
import re

import subprocess
import json


import yaml

from scripts.installer.utils.purge_folders import delete_pycache_folders


"""
EXPLANATION
=======================================
Originally tried using [tftest](https://pypi.org/project/tftest/). Too complicated and abstract IMO. Now using simpler methodology:

1. Test in the project directory.
2. Take a backup of the existing `terraform.tfvars` file.
3. Create a new testing artifacts:
    - Core (via `tests/datafiles/generate_core_data.sh`):
        - `terraform.tfvars` generate from `templates/TEMPLATE_terraform.tfvars.
        - `base-overrides.auto.tfvars` to generate REPLACE_ME substitutions and set some values for faster baseline testing.
    - Testcase:
        - Generate a new `override.auto.tfvars` file in the project root based on necessary overrides for each test.
        - Terraform lexical hierarchy means this file trumps same settings in core files.
4. Run tests:
    1. For each test case, run `terraform plan` using test tfvars and override files. 
    2. Run assertions.
    NOTE: Results cached when possible (i.e. local) to speed up n+1 test runs. Not always feasible with apply-type tests.

5. When tests are complete:
    - Purge tfvars and override files.
    - Restore the original `terraform.tfvars` to project root.
"""


## ------------------------------------------------------------------------------------
## Universal Configuration
## ------------------------------------------------------------------------------------
# Assumes this file lives at 3rd layer of project (i.e. PROJECT_ROOT/tests/utils/local.py)
root = str(Path(__file__).parent.parent.parent.resolve())

# Tfvars and override files filepaths
tfvars_path = f"{root}/terraform.tfvars"
tfvars_backup_path = f"{root}/terraform.tfvars.backup"

test_tfvars_source = f"{root}/tests/datafiles/terraform.tfvars"
test_tfvars_target = f"{root}/terraform.tfvars"
test_tfvars_override_source = f"{root}/tests/datafiles/base-overrides.auto.tfvars"
test_tfvars_override_target = f"{root}/base-overrides.auto.tfvars"

test_case_override_target = f"{root}/override.auto.tfvars"

# SSM (testing) secrets
ssm_tower = f"{root}/tests/datafiles/ssm_sensitive_values_tower_testing.json"
ssm_groundswell = f"{root}/tests/datafiles/ssm_sensitive_values_groundswell_testing.json"
ssm_seqerakit = f"{root}/tests/datafiles/ssm_sensitive_values_seqerakit_testing.json"
ssm_wave_lite = f"{root}/tests/datafiles/ssm_sensitive_values_wave_lite_testing.json"

# Tfplan files and caching folder
plan_cache_dir = f"{root}/tests/.plan_cache"

test_case_tfplan_file = f"{root}/tfplan"
test_case_tfplan_json_file = f"{root}/tfplan.json"


## ------------------------------------------------------------------------------------
## File Utility Functions
## ------------------------------------------------------------------------------------
def read_json(file_path: str) -> dict:
    """Read a JSON plan file."""
    with open(file_path, "r") as f:
        return json.load(f)


def read_yaml(file_path: str) -> Any:
    """Read a JSON plan file."""
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def read_file(file_path: str) -> str:
    """Read a file."""
    with open(file_path, "r") as f:
        return f.read()


def write_file(file_path: str, content: str | bytes) -> None:
    """Write content to a file."""
    if isinstance(content, bytes):
        content = content.decode("utf-8")
    with open(file_path, "w") as f:
        f.write(content)


def move_file(source: str, target: str) -> None:
    """Move a file."""
    try:
        shutil.move(source, target)
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        sys.exit(1)


def copy_file(source: str, target: str) -> None:
    """Move a file."""
    try:
        shutil.copy2(source, target)
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        sys.exit(1)


## ------------------------------------------------------------------------------------
## Cache Utility Functions
## ------------------------------------------------------------------------------------
def get_cache_key(override_data: str, qualifier: str = "") -> str:
    """Generate SHA-256 hash of override data and tfvars content for cache key."""
    override_data = override_data.strip()
    qualifier = qualifier.strip()

    tfvars_content = read_file(tfvars_path).strip()

    # Create combined cache key
    combined_content = f"{override_data}\n---TFVARS---\n{qualifier}\n---QUALIFIER---\n{tfvars_content}"
    return hashlib.sha256(combined_content.encode("utf-8")).hexdigest()[:16]


def strip_overide_whitespace(override_data: str) -> str:
    """
    Purges intermediate whitespace (extra space makes same keys hash to different values).
    Convert multiple spaces to single space (ASSUMPTION: Python tabs insert spaces!)
    NOTE: Need to keep `\n` to not break HCL formatting expectations.
    """
    return "\n".join(re.sub(r"\s+", " ", line) for line in override_data.splitlines())


## ------------------------------------------------------------------------------------
## Subprocess Utility Functions
## ------------------------------------------------------------------------------------
# NOTE: I need the PIPE to capture output for the plan to apply, but it's noisy in the console.
# Ended up using shell-type subprocess.run commands so I can use native Bash to dump output to files.
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
## Terrafrom Comamnd Execution Helpers
## ------------------------------------------------------------------------------------
def run_terraform_plan(qualifier: str = "") -> None:
    """
    Plan based on core tfvars, core override, and testcase override.
    Uses shell-type Bash commands to simplify code.
    """
    for file in [test_case_tfplan_file, test_case_tfplan_json_file]:
        Path(file).unlink(missing_ok=True)

    command = f"terraform plan {qualifier} -out=tfplan && terraform show -json tfplan > tfplan.json"
    execute_subprocess(command)


def run_terraform_apply(qualifier: str = "", auto_approve: bool = True) -> None:
    """
    Normally should use tfplan from `run_terraform_plan`.
    Command override available for targeted apply just in case (will need to plan again).
    Uses shell-type Bash commands to simplify code.
    Results will generally be:
        - `terraform apply --auto-approve tfpan`
        - `terraform apply --auto-approve -target=null_resource.my_resource`
    """
    base_command = f"terraform apply {'--auto-approve' if auto_approve else ''}"
    command = f"{base_command} {qualifier if len(qualifier) > 0 else 'tfplan'}"
    execute_subprocess(command)


def run_terraform_destroy(qualifier: str = "", auto_approve: bool = True) -> None:
    """
    Override file generated by prepare_plan; core tfvars file generated by fixture.
    Results will generally be:
        - `terraform destroy --auto-approve`
        - `terraform destroy --auto-approve -target=null_resource.my_resource`
    """
    base_command = f"terraform destroy {'--auto-approve' if auto_approve else ''}"
    command = f"{base_command} {qualifier if len(qualifier) > 0 else ''}"
    execute_subprocess(command)


## ------------------------------------------------------------------------------------
## Helpers
## ------------------------------------------------------------------------------------
def prepare_plan(
    override_data: str,
    qualifier: str = "",
    use_cache: bool = True,
) -> dict:
    """Generate override.auto.tfvars and run terraform plan with caching.

    Args:
        override_data: Terraform variable overrides
        qualifier: Additional modifier to add to cache key (e.g '-target=null_resource.my_resource')
        use_cache: Whether to use cached results (default: True)

    Returns:
        Terraform plan JSON data
    """

    override_data = strip_overide_whitespace(override_data)

    cache_key = get_cache_key(override_data, qualifier)
    cached_plan_file = f"{plan_cache_dir}/plan_{cache_key}"
    cached_plan_json_file = f"{plan_cache_dir}/plan_{cache_key}.json"

    os.makedirs(plan_cache_dir, exist_ok=True)

    if use_cache and os.path.exists(cached_plan_json_file):
        print(f"Reusing cached plans for: {cache_key}")

        execute_subprocess(f"cp {cached_plan_file} {test_case_tfplan_file}")
        execute_subprocess(f"cp {cached_plan_json_file} {test_case_tfplan_json_file}")
        write_file(test_case_override_target, override_data)
    else:
        # Write override file in root and create plan files.
        print(f"Cache miss. Generating new plan for: {cache_key}")
        write_file(test_case_override_target, override_data)
        run_terraform_plan(qualifier)

        # Stash generated plan files in cachedir for future use.
        execute_subprocess(f"cp {test_case_tfplan_file} {cached_plan_file}")
        execute_subprocess(f"cp {test_case_tfplan_json_file} {cached_plan_json_file}")

    return read_json(test_case_tfplan_json_file)


def parse_key_value_file(file_path: str) -> Dict[str, Any]:
    """Parse a file containing KEY=VALUE pairs.

    Args:
        file_path: Path to the file to parse

    Returns:
        Dictionary containing key-value pairs
    """
    result = {}
    raw = read_file(file_path)

    for line in raw.splitlines():
        line = line.strip()
        if line and "=" in line:
            key, value = line.split("=", 1)
            # Edgecase: Config files have empty string represented by "" or ''
            #  but python thinks the string is literally x2 doublequotes or single quotes.
            if (value == '""') or (value == "''"):
                value = ""
            result[key.strip()] = value.strip()

    return result
