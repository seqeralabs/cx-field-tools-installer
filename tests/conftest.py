import subprocess
from pathlib import Path

import pytest

# Single-sourced in top-level conftest.py.
# base_import_dir = Path(__file__).resolve().parents[3]
# print(f"{base_import_dir=}")
# if base_import_dir not in sys.path:
#     sys.path.append(str(base_import_dir))

from scripts.installer.utils.purge_folders import delete_pycache_folders

from tests.utils.local import root, tfvars_path, tfvars_backup_path
from tests.utils.local import test_tfvars_source, test_tfvars_target
from tests.utils.local import test_tfvars_override_source, test_tfvars_override_target
from tests.utils.local import test_case_override_target

from tests.utils.local import copy_file, move_file
from tests.utils.local import prepare_plan
from tests.utils.local import run_terraform_apply, run_terraform_destroy
from tests.utils.local import execute_subprocess


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
## Helper Fixtures
## ------------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def backup_tfvars():
    # Create a fresh copy of the base testing terraform.tfvars file.
    subprocess.run("make generate_test_data", shell=True, check=True)

    print(f"\nBacking up {tfvars_path} to {tfvars_backup_path}.")
    move_file(tfvars_path, tfvars_backup_path)

    print(f"\nLoading test tfvars (base) artefacts.")
    copy_file(test_tfvars_source, test_tfvars_target)
    copy_file(test_tfvars_override_source, test_tfvars_override_target)

    yield

    print("\nRestoring original environment.")

    # Remove testing files, delete __pycache__ folders, restore origin tfvars.
    for file in [
        test_case_override_target,
        test_tfvars_target,
        test_tfvars_override_target,
    ]:
        Path(file).unlink(missing_ok=True)

    delete_pycache_folders(root)
    move_file(tfvars_backup_path, tfvars_path)


# TODO: Make sure module is for the file calling it, NOT where this fixture lives.
@pytest.fixture(scope="module")
def config_baseline_settings_default():
    """
    Terraform plan and apply the default test terraform.tfvars and base-override.auto.tfvars.

    This test is slower than test_module_connections_strings since we need to plan every time and apply.
    However, it generates almost every configuration (Tower / Wave Lite / Ansible / etc) so it's worth the time to check.
    I use an existing VPC in the account the AWS provider is configured to use to speed things up, but it's not perfect.
    TODO: Figure out if there's some way to speed up the plan (i.e. split out `data` resource calls? As of July 9/25, resources created:
      - data.aws_ssm_parameter.groundswell_secrets
      - data.aws_ssm_parameter.tower_secrets
      - data.aws_ssm_parameter.wave_lite_secrets
      - null_resource.generate_independent_config_files
      - random_pet.stackname
      - tls_private_key.connect_pem
      - tls_private_key.ec2_ssh_key
      - module.connection_strings.data.external.generate_db_connection_string
      - module.subnet_collector.data.aws_subnet.sp_subnets["subnet-00fad764627895f33"]
      - module.subnet_collector.data.aws_subnet.sp_subnets["subnet-0d0e8ba3b03b97a65"]
      - module.subnet_collector.data.aws_subnet.sp_subnets["subnet-0e07c9b2edbd84ea4"]
      - module.subnet_collector.data.aws_subnet.sp_subnets["subnet-0f18039d5ffcf6cd3"]
      - module.subnet_collector.data.aws_subnets.all[0]
      - module.subnet_collector.data.aws_vpc.sp_vpc)
    """

    override_data = """
        # No override values needed. Testing baseline only.
    """
    # Plan with ALL resources rather than targeted, to get all outputs in plan document.
    qualifier = "-target=null_resource.generate_independent_config_files"
    # plan = prepare_plan(override_data, qualifier)
    plan = prepare_plan(override_data)
    run_terraform_apply(qualifier)
    execute_subprocess(f"terraform state list > terraform_state_list.txt")

    # Apply will generate actual assets we can interrogate in project or via remote calls.
    # Return plan only
    yield plan

    run_terraform_destroy()


@pytest.fixture(scope="function")
def teardown_tf_state_all():
    print("This testcase will have all tf state destroyed.")

    yield

    run_terraform_destroy()
