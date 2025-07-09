import pytest
import subprocess

from tests.utils.local import root
from tests.utils.local import prepare_plan, run_terraform_apply
from tests.utils.local import parse_key_value_file


## ------------------------------------------------------------------------------------
## Tower Config Files
## ------------------------------------------------------------------------------------
# NOTE: To avoid creating VPC assets, use an existing VPC in the account the AWS provider is configured to use.


@pytest.mark.local
@pytest.mark.config_files
def test_config_tower_env(backup_tfvars, teardown_tf_state_all):
    # Given
    override_data = """
        flag_create_new_vpc   = false
        flag_use_existing_vpc = true

        flag_create_external_db         = false
        flag_use_existing_external_db   = false
        flag_use_container_db           = true
        flag_use_wave_lite              = false

        vpc_existing_id            = "vpc-0fd280748c05b375b"
        vpc_existing_ec2_subnets   = ["10.0.3.0/24"]
        vpc_existing_batch_subnets = ["10.0.3.0/24"]
        vpc_existing_db_subnets    = ["10.0.3.0/24"]
        vpc_existing_redis_subnets = ["10.0.3.0/24"]
        vpc_existing_alb_subnets   = ["10.0.1.0/24", "10.0.2.0/24"]
    """

    # When
    # plan = prepare_plan(override_data)
    # outputs = plan["planned_values"]["outputs"]

    qualifier = "-target=null_resource.generate_independent_config_files"
    plan = prepare_plan(override_data, qualifier, will_apply=True)
    run_terraform_apply(qualifier)

    # Crack actual created file
    file = parse_key_value_file(f"{root}/assets/target/tower/config/tower_env")

    print(f"{file=}")

    # TODO: Get assets/target/tower/config/tower_env.sh and check for expected values.
