import pytest
# import tftest

# # TODO: June 21/2025 -- This is a hack to get the test to run.
# root = '/home/deeplearning/cx-field-tools-installer'


# @pytest.fixture(scope="session")
# def plan_new_db(datafiles_folder):  #def plan_new_db(scratch, datafiles_folder):

#     tf = tftest.TerraformTest(tfdir=root)
    
#     # Copy test configurations to fixtures directory
#     tf.setup(
#         extra_files=[
#             f"{datafiles_folder}/terraform.tfvars",
#             f"{datafiles_folder}/external_db_new.auto.tfvars",
#         ],
#         cleanup_on_exit=False   # Dont trash .terraform and terraform.tfstate
#     )
#     return tf.plan(output=True)


# @pytest.fixture(scope="session")
# def plan_existing_db(datafiles_folder):  #def plan_new_db(scratch, datafiles_folder):

#     tf = tftest.TerraformTest(tfdir=root)
    
#     # Copy test configurations to fixtures directory
#     tf.setup(
#         extra_files=[
#             f"{datafiles_folder}/terraform.tfvars",
#             f"{datafiles_folder}/external_db_existing.auto.tfvars",
#         ],
#         cleanup_on_exit=False   # Dont trash .terraform and terraform.tfstate
#     )
#     return tf.plan(output=True)


# @pytest.fixture(scope="session")
# def plan_new_redis(datafiles_folder):  #def plan_new_db(scratch, datafiles_folder):

#     tf = tftest.TerraformTest(tfdir=root)
    
#     # Copy test configurations to fixtures directory
#     tf.setup(
#         extra_files=[
#             f"{datafiles_folder}/terraform.tfvars",
#             f"{datafiles_folder}/external_redis_new.auto.tfvars",
#         ],
#         cleanup_on_exit=False   # Dont trash .terraform and terraform.tfstate
#     )
#     return tf.plan(output=True)


## ------------------------------------------------------------------------------------
## New RDS
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.db
def test_new_tower_db_url(plan_new_db):
    # assert plan_new_db.outputs['tower_db_url'] == 'mock-db.example.com'
    # mod = plan_new_db.modules['module.connection_strings']
    # print(mod)
    # res ['tower_db_url'] == 'mock-db.example.com'
    # print(plan_new_db.modules)
    # mod = plan_new_db.modules['module.connection_strings']
    # print(mod)
    # print(plan_new_db.outputs)
    # This value comes from mock value in module.connection_strings.main.tf

    assert "mock-new-tower-db.example.com" in plan_new_db.outputs["tower_db_url"] 


@pytest.mark.local
@pytest.mark.db
def test_new_swell_db_url(plan_new_db):
    assert "mock-new-tower-db.example.com" in plan_new_db.outputs["swell_db_url"] 


@pytest.mark.local
@pytest.mark.db
def test_new_wave_lite_db_url(plan_new_db):
    assert "mock-new-wave-lite-db.example.com" in plan_new_db.outputs["wave_lite_db_url"] 


## ------------------------------------------------------------------------------------
## Existing RDS
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.db
def test_existing_tower_db_url(plan_existing_db):
    assert "mock-existing-tower-db.example.com" in plan_existing_db.outputs["tower_db_url"] 


@pytest.mark.local
@pytest.mark.db
def test_existing_swell_db_url(plan_existing_db):
    assert "mock-existing-tower-db.example.com" in plan_existing_db.outputs["swell_db_url"] 

# GAP: Wave-Lite with pre-existing database.


## ------------------------------------------------------------------------------------
## New Redis
## NOTE: Could combine this with new DB to save testing cycles (if cant optimize)
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.redis
def test_new_tower_redis_url(plan_new_redis):
    assert "mock-new-tower-redis.example.com" in plan_new_redis.outputs["tower_redis_url"] 