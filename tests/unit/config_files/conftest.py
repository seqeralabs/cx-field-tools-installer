# import pytest

# import os
# from pathlib import Path
# import shutil
# import sys
# import hashlib
# from typing import Dict, Any
# import re

# import subprocess
# import json

# # Single-sourced in top-level conftest.py.
# # base_import_dir = Path(__file__).resolve().parents[3]
# # print(f"{base_import_dir=}")
# # if base_import_dir not in sys.path:
# #     sys.path.append(str(base_import_dir))

# from scripts.installer.utils.purge_folders import delete_pycache_folders

# from tests.utils.local import prepare_plan
# from tests.utils.local import get_cache_key, ensure_cache_dir, clear_plan_cache
# from tests.utils.local import root, tfvars_path, tfvars_backup_path, test_tfvars_path
# from tests.utils.local import _plan_cache, _cache_dir


# """
# EXPLANATION
# =======================================
# Originally tried using [tftest](https://pypi.org/project/tftest/) package to test but this became complicated and unwieldy. Instead, simplified
# testing loop to:

# 1. Test in the project directory.
# 2. Take a backup of the existing `terraform.tfvars` file.
# 3. Create a new `terraform.tfvars` file for testing purposes (_sourced from `tests/datafiles/generate_core_data.sh`).
# 4. Provide override values to test fixtures (which will generate a new `override.auto.tfvars` file in the project root).
#     This file supercedes the same keys defined in the `terraform.tfvars` file.
# 5. Run the tests:
#     1. For each fixture, run `terraform plan` based on the test tvars and override file. Results as cached to speed up n+1 test runs.
#     2. Execute tests tied to that fixture.
#     3. Repeat.
# 6. Purge the test tfvars and override file.
# 7.Restore the original `terraform.tfvars` file when testing is complete.
# """


# ## ------------------------------------------------------------------------------------
# ## Helper Fixtures
# ## ------------------------------------------------------------------------------------
# @pytest.fixture(scope="session")
# def backup_tfvars():
#     # Create a fresh copy of the base testing terraform.tfvars file.
#     subprocess.run(["make", "generate_test_data"], check=True)

#     try:
#         print(f"\nBacking up tfvars from {tfvars_path} to {tfvars_backup_path}")
#         shutil.move(tfvars_path, tfvars_backup_path)

#         print(f"\nLoading testing tfvars {tfvars_path} to {tfvars_backup_path}")
#         shutil.copy2(test_tfvars_path, tfvars_path)

#     except FileNotFoundError as e:
#         print(f"Source file not found: {e}")
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         sys.exit(1)

#     yield

#     print("\nRestoring original environment.")
#     try:
#         shutil.move(tfvars_backup_path, tfvars_path)
#     except FileNotFoundError as e:
#         print(f"Source file not found: {e}")

#     # Remove testing files
#     for file in [f"{root}/override.auto.tfvars", test_tfvars_path]:
#         try:
#             os.remove(file)
#         except FileNotFoundError as e:
#             # Commented out to avoid noise in test output.
#             # print(f"Source file not found: {e}")
#             pass

#     # July 4/2025 -- Removed cache auto-cleanup since it want these to persist between runs so n+1 goes much faster.
#     # clear_plan_cache()

#     delete_pycache_folders(root)
