import pytest
import subprocess
import json
import os
import tempfile

from tests.utils.local import root, test_tfvars_target, test_tfvars_override_target, test_case_override_target
from tests.utils.local import prepare_plan, run_terraform_apply, execute_subprocess
from tests.utils.local import parse_key_value_file, read_file, read_yaml, read_json
from tests.utils.local import get_reconciled_tfvars

from tests.utils.local import ssm_tower, ssm_groundswell, ssm_seqerakit, ssm_wave_lite

from testcontainers.mysql import MySqlContainer


## ------------------------------------------------------------------------------------
## Test Ansible Configuration files
## ------------------------------------------------------------------------------------
# NOTE: To avoid creating VPC assets, use an existing VPC in the account the AWS provider is configured to use.


@pytest.mark.local
@pytest.mark.ansible
@pytest.mark.vpc_existing
@pytest.mark.long
def test_002_update_file_configurations_all_present(backup_tfvars, config_ansible_02_all_flags_true):  # teardown_tf_state_all):
    """
    Test 
    """

    # Given
    print("Testing Ansible 02_update_file_configurations.yml.tpl.")

    # When
    outputs = config_ansible_02_all_flags_true["planned_values"]["outputs"]
    variables = config_ansible_02_all_flags_true["variables"]

    ansible_file = read_file(f"{root}/assets/target/ansible/02_update_file_configurations.yml")

    """
    WARNING!!!!!!
      - Plan keys are in Python dictionary form, so JSON "true" becomes True.
            AFFECTS: `outputs` and `variables`
      - tower_env_file values are directly cracked from HCL so they are "true".
    """

    # ------------------------------------------------------------------------------------
    # Test tower.env - assert all core keys exist
    # ------------------------------------------------------------------------------------
    assert "Populating external Platform DB." in ansible_file             # Tower DB
    assert "Populating Wave Lite Postgres." in ansible_file               # Wabe-Lite DB
    assert "Populating external DB with Groundswell." in ansible_file     # Groundswell DB
    assert "Configuring private certificates." in ansible_file            # Private CA cert


@pytest.mark.local
@pytest.mark.ansible
@pytest.mark.vpc_existing
@pytest.mark.long
def test_002_update_file_configurations_none_present(backup_tfvars, config_ansible_02_all_flags_false):  # teardown_tf_state_all):
    """
    Test 
    """

    # Given
    print("Testing Ansible 02_update_file_configurations.yml.tpl.")

    # When
    outputs = config_ansible_02_all_flags_false["planned_values"]["outputs"]
    variables = config_ansible_02_all_flags_false["variables"]

    ansible_file = read_file(f"{root}/assets/target/ansible/02_update_file_configurations.yml")

    """
    WARNING!!!!!!
      - Plan keys are in Python dictionary form, so JSON "true" becomes True.
            AFFECTS: `outputs` and `variables`
      - tower_env_file values are directly cracked from HCL so they are "true".
    """

    # ------------------------------------------------------------------------------------
    # Test tower.env - assert all core keys exist
    # ------------------------------------------------------------------------------------
    assert "Populating external Platform DB." not in ansible_file             # Tower DB
    assert "Populating Wave Lite Postgres." not in ansible_file               # Wabe-Lite DB
    assert "Populating external DB with Groundswell." not in ansible_file     # Groundswell DB
    assert "Configuring private certificates." not in ansible_file            # Private CA cert
