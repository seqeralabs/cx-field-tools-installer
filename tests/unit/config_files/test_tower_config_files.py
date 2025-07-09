import pytest
import subprocess

from tests.utils.local import root
from tests.utils.local import prepare_plan, run_terraform_apply, execute_subprocess
from tests.utils.local import parse_key_value_file


## ------------------------------------------------------------------------------------
## Tower Config Files
## ------------------------------------------------------------------------------------
# NOTE: To avoid creating VPC assets, use an existing VPC in the account the AWS provider is configured to use.


@pytest.mark.local
@pytest.mark.config_files
def test_config_tower_env(backup_tfvars, teardown_tf_state_all):
    """
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
    execute_subprocess(f"terraform state list > terraform_state_list.txt")

    # Crack actual created file
    file = parse_key_value_file(f"{root}/assets/target/tower/config/tower_env")

    print(f"{file=}")

    # TODO: Get assets/target/tower/config/tower_env.sh and check for expected values.
