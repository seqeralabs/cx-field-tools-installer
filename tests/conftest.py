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
from tests.utils.local import run_terraform_destroy


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


@pytest.fixture(scope="function")
def teardown_tf_state_all():
    print("This testcase will have all tf state destroyed.")

    yield

    run_terraform_destroy()
