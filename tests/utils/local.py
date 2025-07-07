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

from scripts.installer.utils.purge_folders import delete_pycache_folders

# TODO: June 21/2025 -- This is a hack to get the test to run.
root = "/home/deeplearning/cx-field-tools-installer"
tfvars_path = f"{root}/terraform.tfvars"
tfvars_backup_path = f"{root}/terraform.tfvars.backup"
test_tfvars_path = f"{root}/tests/datafiles/terraform.tfvars"

# Cache infrastructure for `terraform plan` results.
_plan_cache: Dict[str, Any] = {}
_cache_dir = f"{root}/tests/.plan_cache"

"""
EXPLANATION
=======================================
Originally tried using [tftest](https://pypi.org/project/tftest/) package to test but this became complicated and unwieldy. Instead, simplified
testing loop to:

1. Test in the project directory.
2. Take a backup of the existing `terraform.tfvars` file.
3. Create a new `terraform.tfvars` file for testing purposes (_sourced from `tests/datafiles/generate_core_data.sh`).
4. Provide override values to test fixtures (which will generate a new `override.auto.tfvars` file in the project root).
    This file supercedes the same keys defined in the `terraform.tfvars` file.
5. Run the tests:
    1. For each fixture, run `terraform plan` based on the test tvars and override file. Results as cached to speed up n+1 test runs.
    2. Execute tests tied to that fixture.
    3. Repeat.
6. Purge the test tfvars and override file.
7.Restore the original `terraform.tfvars` file when testing is complete.
"""


## ------------------------------------------------------------------------------------
## Cache Utility Functions
## ------------------------------------------------------------------------------------
def get_cache_key(override_data: str) -> str:
    """Generate SHA-256 hash of override data and tfvars content for cache key."""
    normalized = override_data.strip()

    # Read tfvars file content and include in cache key
    try:
        with open(tfvars_path, "r") as f:
            tfvars_content = f.read().strip()
    except FileNotFoundError as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

    # Combine override data and tfvars content for cache key
    combined_content = f"{normalized}\n---TFVARS---\n{tfvars_content}"
    return hashlib.sha256(combined_content.encode("utf-8")).hexdigest()[:16]


def ensure_cache_dir():
    """Ensure cache directory exists."""
    os.makedirs(_cache_dir, exist_ok=True)


def clear_plan_cache():
    """Clear both in-memory and disk cache."""
    global _plan_cache
    _plan_cache.clear()

    if os.path.exists(_cache_dir):
        shutil.rmtree(_cache_dir)
    print("Plan cache cleared")


## ------------------------------------------------------------------------------------
## Helpers
## ------------------------------------------------------------------------------------
def prepare_plan(override_data: str, use_cache: bool = True) -> dict:
    """Generate override.auto.tfvars and run terraform plan with caching.

    Args:
        override_data: Terraform variable overrides
        use_cache: Whether to use cached results (default: True)

    Returns:
        Terraform plan JSON data
    """
    # Remove intermediate whitespace (extra space makes same keys hash to different values).
    # Convert multiple sapces to single space (ASSUMPTION: Python tabs insert spaces!)
    # NOTE: Need to keep `\n` to not break HCL formatting expectations.
    override_data = "\n".join(
        re.sub(r"\s+", " ", line) for line in override_data.splitlines()
    )
    # print(f"{override_data=}")
    cache_key = get_cache_key(override_data)

    # Check in-memory cache first
    if use_cache and cache_key in _plan_cache:
        print(f"Using cached plan for key: {cache_key}")
        return _plan_cache[cache_key]

    # Check disk cache
    cache_file = f"{_cache_dir}/plan_{cache_key}.json"
    if use_cache and os.path.exists(cache_file):
        try:
            print(f"Loading cached plan from disk: {cache_key}")
            with open(cache_file, "r") as f:
                plan = json.load(f)
            _plan_cache[cache_key] = plan
            return plan
        except (json.JSONDecodeError, IOError) as e:
            print(f"Cache file corrupted, regenerating: {e}")

    # Generate new plan
    print(f"Generating new plan for key: {cache_key}")
    ensure_cache_dir()

    with open(f"{root}/override.auto.tfvars", "w") as f:
        f.write(override_data)

    subprocess.run(["make", "generate_json_plan"], check=True)

    with open(f"{root}/tfplan.json", "r") as f:
        plan = json.load(f)

    # Cache the result
    _plan_cache[cache_key] = plan
    with open(cache_file, "w") as f:
        json.dump(plan, f, indent=2)

    return plan
