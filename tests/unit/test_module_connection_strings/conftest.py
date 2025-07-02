import pytest
import tftest

import os
from pathlib import Path
import shutil
import warnings
import sys

import subprocess
import json

# base_import_dir = Path(__file__).resolve().parents[3]
# print(f"{base_import_dir=}")
# if base_import_dir not in sys.path:
#     sys.path.append(str(base_import_dir))

from scripts.installer.utils.purge_folders import delete_pycache_folders

# TODO: June 21/2025 -- This is a hack to get the test to run.
root = "/home/deeplearning/cx-field-tools-installer"
tfvars_path = f"{root}/terraform.tfvars"
tfvars_backup_path = f"{root}/terraform.tfvars.backup"
test_tfvars_path = f"{root}/tests/datafiles/terraform.tfvars"

"""
EXPLANATION
=======================================
I don't want tests happening in the source project. But `tftest` needs to be able to find the source code.
So, we copy the source code to a temporary directory and then run the tests from there.
This feels like a hack but I haven't seen better guidance anywhere.
`.terraform` folder is 400+MB. I can cache plugins but not the modules (downloaded each time). So these are symlinked in to save
time and bandwidth.

`try/except` wraps the tf.plan beause I wanted to use pytest-xdist to parallelize. Multiprocessing massively slows down small volumes 
(see: https://github.com/pytest-dev/pytest-xdist/issues/346 and https://stackoverflow.com/questions/42288175/why-does-pytest-xdist-make-my-tests-run-slower-not-faster)
Keeping the hooks in for now but DONT use them until there is more critical mass.

Rewritten the call to the python function to use path.module, so the fixtures below can specifically target that connection_strings module alone versus whole project.
Saves about 20 seconds per testing cycle and pattern is scaleable in situations where full project plannning is required.

NOTE: 
1) DONT cleanup on exist or you'll crush the symlinked .terraform folder and have to reinstall in actual project.
2) Targeting module only seems to produce no output. Stick with full plan.
  e.g `return tf.plan(output=True, targets=["module.connection_strings"])` vs `return tf.plan(output=True, targets=["aws_instance.ec2"])`
"""


## ------------------------------------------------------------------------------------
## Helper Fixtures
## ------------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def backup_tfvars():
    try:
        print(f"\nBacking up tfvars from {tfvars_path} to {tfvars_backup_path}")
        shutil.move(tfvars_path, tfvars_backup_path)

        print(f"\nLoading testing tfvars {tfvars_path} to {tfvars_backup_path}")
        shutil.copy2(test_tfvars_path, tfvars_path)

    except FileNotFoundError:
        print("Source file not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

    yield

    print("\nRestoring tfvars")
    shutil.move(tfvars_backup_path, tfvars_path)

    # Removing override file (once to not have conflict)
    os.remove(f"{root}/override.auto.tfvars")

    # Purging __pycache__ folder
    delete_pycache_folders(root)


def prepare_plan(override_data):
    """Generate override.auto.tfvars and then run `terrform plan` to produce useable JSON."""

    with open(f"{root}/override.auto.tfvars", "w") as f:
        f.write(override_data)
    subprocess.run(["make", "generate_json_plan"])
    with open(f"{root}/tfplan.json", "r") as f:
        plan = json.load(f)
    return plan


## ------------------------------------------------------------------------------------
## Terraform Plan Fixtures
## ------------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def plan_new_db(backup_tfvars):
    new_db_override_data = """
        flag_create_external_db = true
        flag_use_existing_external_db = false
        flag_use_container_db =  false
    """
    plan = prepare_plan(new_db_override_data)
    yield plan


@pytest.fixture(scope="session")
def plan_existing_db(backup_tfvars):
    existing_db_override_data = """
        flag_create_external_db         = false
        flag_use_existing_external_db   = true
        flag_use_container_db           = false

        tower_db_url                    = "mock-existing-tower-db.example.com"
    """
    plan = prepare_plan(existing_db_override_data)
    yield plan


@pytest.fixture(scope="session")
def plan_new_redis(backup_tfvars):
    new_redis_override_data = """
        flag_create_external_redis                      = true
        flag_use_container_redis                        = false
    """
    plan = prepare_plan(new_redis_override_data)
    yield plan


@pytest.fixture(scope="session")
def plan_urls_static(backup_tfvars):
    urls_static_override_data = """
        tower_server_url                                = "mock-tower-base-static.example.com"
        flag_use_container_redis                        = false
    """
    plan = prepare_plan(urls_static_override_data)
    yield plan


@pytest.fixture(scope="session")
def plan_urls_insecure(backup_tfvars):
    urls_insecure_override_data = """
        tower_server_url                                = "mock-tower-base-insecure.example.com"
        flag_create_load_balancer                       = false
        flag_do_not_use_https				= true
    """
    plan = prepare_plan(urls_insecure_override_data)
    yield plan
