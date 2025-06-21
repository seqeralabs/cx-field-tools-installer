import pytest
import tftest

import json
from pathlib import Path


@pytest.fixture
def fixtures_dir(tmpdir):
    # Create a temporary test directory
    return tmpdir.mkdir("fixtures")


@pytest.fixture(scope="session", autouse=True)
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

@pytest.fixture
def terraform_test(fixtures_dir): 
    # Initialize test with fixtures
    tf = tftest.TerraformTest(fixtures_dir)
    
    # Copy test configurations to fixtures directory
    tf.setup(
        extra_files=[
            'test.tfvars',
            'mock_provider.tf'
        ]
    )
    return tf

# def test_resource_creation(terraform_test):
#     # Run plan and verify outputs
#     plan = terraform_test.plan(output=True)
#     assert plan.outputs['database_endpoint'] == 'mock-db.example.com'



# TODO Add logger for agentic access

@pytest.fixture(scope="session", autouse=True)
def tfplan_json():
    with open("tfplan.json", "r") as f:
        yield json.load(f)
        print("Done")

        
        