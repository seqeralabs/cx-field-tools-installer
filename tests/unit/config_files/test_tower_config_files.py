import pytest

from conftest import prepare_plan


## ------------------------------------------------------------------------------------
## Tower Config Files
## ------------------------------------------------------------------------------------
# NOTE: To avoid creating VPC assets, use an existing VPC in the account the AWS provider is configured to use.


@pytest.mark.local
@pytest.mark.config_files
def test_config_tower_env(backup_tfvars):
    # Given
    override_data = """
        flag_create_new_vpc   = false
        flag_use_existing_vpc = true

        vpc_existing_id            = "vpc-0fd280748c05b375b"
        vpc_existing_ec2_subnets   = ["10.0.3.0/24"]
        vpc_existing_batch_subnets = ["10.0.3.0/24"]
        vpc_existing_db_subnets    = ["10.0.3.0/24"]
        vpc_existing_redis_subnets = ["10.0.3.0/24"]
        vpc_existing_alb_subnets   = ["10.0.1.0/24", "10.0.2.0/24"]
    """

    # When
    plan = prepare_plan(override_data)
    outputs = plan["planned_values"]["outputs"]

    # TODO: Get assets/target/tower/config/tower_env.sh and check for expected values.
