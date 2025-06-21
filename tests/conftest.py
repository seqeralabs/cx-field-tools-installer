import pytest
import tftest
import shutil

import json
from pathlib import Path


# @pytest.fixture
# def scratch(tmpdir):
#     print(f"{str(tmpdir)=}")
#     root = '/home/deeplearning/cx-field-tools-installer'
#     target = f"{str(tmpdir)}/cx-field-tools-installer"
#     shutil.copytree(root, target)
#     yield target


@pytest.fixture(scope="session")
def datafiles_folder():
    parent_path = Path(__file__).parent.absolute()
    return parent_path / "datafiles"

# CORE -- I've moved these two the target directory for better localization
# @pytest.fixture
# def terraform_test(fixtures_dir): 
#     # Initialize test with fixtures
#     tf = tftest.TerraformTest(fixtures_dir)
    
#     # Copy test configurations to fixtures directory
#     tf.setup(
#         extra_files=[
#             'test.tfvars',
#             'mock_provider.tf'
#         ]
#     )
#     return tf


# TODO Add logger for agentic access

@pytest.fixture(scope="session", autouse=True)
def tfplan_json():
    with open("tfplan.json", "r") as f:
        yield json.load(f)
        print("Done")

        
        