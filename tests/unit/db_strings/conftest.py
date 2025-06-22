import pytest
import tftest

# TODO: June 21/2025 -- This is a hack to get the test to run.
root = '/home/deeplearning/cx-field-tools-installer'


@pytest.fixture(scope="session")
def plan_new_db(datafiles_folder):  #def plan_new_db(scratch, datafiles_folder):

    tf = tftest.TerraformTest(tfdir=root)
    
    # Copy test configurations to fixtures directory
    tf.setup(
        extra_files=[
            f"{datafiles_folder}/terraform.tfvars",
            f"{datafiles_folder}/external_db_new.auto.tfvars",
        ],
        cleanup_on_exit=False   # Dont trash .terraform and terraform.tfstate
    )
    return tf.plan(output=True)


@pytest.fixture(scope="session")
def plan_existing_db(datafiles_folder):  #def plan_new_db(scratch, datafiles_folder):

    tf = tftest.TerraformTest(tfdir=root)
    
    # Copy test configurations to fixtures directory
    tf.setup(
        extra_files=[
            f"{datafiles_folder}/terraform.tfvars",
            f"{datafiles_folder}/external_db_existing.auto.tfvars",
        ],
        cleanup_on_exit=False   # Dont trash .terraform and terraform.tfstate
    )
    return tf.plan(output=True)


@pytest.fixture(scope="session")
def plan_new_redis(datafiles_folder):  #def plan_new_db(scratch, datafiles_folder):

    tf = tftest.TerraformTest(tfdir=root)
    
    # Copy test configurations to fixtures directory
    tf.setup(
        extra_files=[
            f"{datafiles_folder}/terraform.tfvars",
            f"{datafiles_folder}/external_redis_new.auto.tfvars",
        ],
        cleanup_on_exit=False   # Dont trash .terraform and terraform.tfstate
    )
    return tf.plan(output=True)