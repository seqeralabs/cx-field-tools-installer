import pytest
import tftest


@pytest.fixture
def tf_test_new_db(fixtures_dir, datafiles_folder):
    # Initialize test with fixtures
    tf = tftest.TerraformTest(fixtures_dir)
    
    # Copy test configurations to fixtures directory
    tf.setup(
        extra_files=[
            f"{datafiles_folder}/terraform.tfvars",
            f"{datafiles_folder}/external_db_new.auto.tfvars",
        ]
    )
    return tf


def test_resource_creation(terraform_test):
    # Run plan and verify outputs
    plan = terraform_test.plan(output=True)
    assert plan.outputs['database_endpoint'] == 'mock-db.example.com'