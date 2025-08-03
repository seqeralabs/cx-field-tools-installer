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
def test_002_update_file_configurations_all_present(backup_tfvars, config_ansible_02_should_be_present):  # teardown_tf_state_all):
    """
    Test 
    """

    # Given
    print("Testing Ansible 02_update_file_configurations.yml.tpl.")

    # When
    outputs = config_ansible_02_should_be_present["planned_values"]["outputs"]
    variables = config_ansible_02_should_be_present["variables"]

    ansible_file_02 = read_file(f"{root}/assets/target/ansible/02_update_file_configurations.yml")

    """
    WARNING!!!!!!
      - Plan keys are in Python dictionary form, so JSON "true" becomes True.
            AFFECTS: `outputs` and `variables`
      - tower_env_file values are directly cracked from HCL so they are "true".
    """

    # ------------------------------------------------------------------------------------
    # Test tower.env - assert all core keys exist
    # ------------------------------------------------------------------------------------
    assert "Populating external Platform DB." in ansible_file_02                     # Tower DB
    assert "Populating Wave Lite Postgres." in ansible_file_02                       # Wabe-Lite DB
    assert "Populating external DB with Groundswell." in ansible_file_02             # Groundswell DB
    assert "Configuring private certificates." in ansible_file_02                    # Private CA cert
    assert "Creating data directory on host for Studios." in ansible_file_02         # Studios datadir 0.8.2


@pytest.mark.local
@pytest.mark.ansible
@pytest.mark.vpc_existing
@pytest.mark.long
def test_002_update_file_configurations_none_present(backup_tfvars, config_ansible_02_should_not_be_present):  # teardown_tf_state_all):
    """
    Test 
    """

    # Given
    print("Testing Ansible 02_update_file_configurations.yml.tpl.")

    # When
    outputs = config_ansible_02_should_not_be_present["planned_values"]["outputs"]
    variables = config_ansible_02_should_not_be_present["variables"]

    ansible_file_02 = read_file(f"{root}/assets/target/ansible/02_update_file_configurations.yml")

    """
    WARNING!!!!!!
      - Plan keys are in Python dictionary form, so JSON "true" becomes True.
            AFFECTS: `outputs` and `variables`
      - tower_env_file values are directly cracked from HCL so they are "true".
    """

    # ------------------------------------------------------------------------------------
    # Test tower.env - assert all core keys exist
    # ------------------------------------------------------------------------------------
    assert "Populating external Platform DB." not in ansible_file_02               # Tower DB
    assert "Populating Wave Lite Postgres." not in ansible_file_02                 # Wabe-Lite DB
    assert "Populating external DB with Groundswell." not in ansible_file_02       # Groundswell DB
    assert "Configuring private certificates." not in ansible_file_02              # Private CA cert
    assert "Creating data directory on host for Studios." not in ansible_file_02   # Studios datadir 0.8.2


@pytest.mark.local
@pytest.mark.ansible
@pytest.mark.vpc_existing
@pytest.mark.long
def test_005_should_be_present(backup_tfvars, config_ansible_05_should_be_present):  # teardown_tf_state_all):
    """
    Test 
    """

    # Given
    print("Testing Ansible 02_update_file_configurations.yml.tpl.")

    # When
    outputs = config_ansible_05_should_be_present["planned_values"]["outputs"]
    variables = config_ansible_05_should_be_present["variables"]

    ansible_file_05 = read_file(f"{root}/assets/target/ansible/05_patch_groundswell.yml")

    """
    WARNING!!!!!!
      - Plan keys are in Python dictionary form, so JSON "true" becomes True.
            AFFECTS: `outputs` and `variables`
      - tower_env_file values are directly cracked from HCL so they are "true".
    """

    # ------------------------------------------------------------------------------------
    # Test tower.env - assert all core keys exist
    # ------------------------------------------------------------------------------------
    assert "Patching container db with groundswell init script." in ansible_file_05  # Groundswell


@pytest.mark.local
@pytest.mark.ansible
@pytest.mark.vpc_existing
@pytest.mark.long
def test_005_should_not_be_present(backup_tfvars, config_ansible_05_should_not_be_present):  # teardown_tf_state_all):
    """
    Test 
    """

    # Given
    print("Testing Ansible 02_update_file_configurations.yml.tpl.")

    # When
    outputs = config_ansible_05_should_not_be_present["planned_values"]["outputs"]
    variables = config_ansible_05_should_not_be_present["variables"]

    ansible_file_05 = read_file(f"{root}/assets/target/ansible/05_patch_groundswell.yml")

    """
    WARNING!!!!!!
      - Plan keys are in Python dictionary form, so JSON "true" becomes True.
            AFFECTS: `outputs` and `variables`
      - tower_env_file values are directly cracked from HCL so they are "true".
    """

    # ------------------------------------------------------------------------------------
    # Test tower.env - assert all core keys exist
    # ------------------------------------------------------------------------------------
    assert "Patching container db with groundswell init script." not in ansible_file_05  # Groundswell


@pytest.mark.local
@pytest.mark.ansible
@pytest.mark.vpc_existing
@pytest.mark.long
def test_006_should_be_present(backup_tfvars, config_ansible_06_should_be_present):  # teardown_tf_state_all):
    """
    Test 
    """

    # Given
    print("Testing Ansible 02_update_file_configurations.yml.tpl.")

    # When
    outputs = config_ansible_06_should_be_present["planned_values"]["outputs"]
    variables = config_ansible_06_should_be_present["variables"]

    ansible_file_06 = read_file(f"{root}/assets/target/ansible/06_run_seqerakit.yml")

    """
    WARNING!!!!!!
      - Plan keys are in Python dictionary form, so JSON "true" becomes True.
            AFFECTS: `outputs` and `variables`
      - tower_env_file values are directly cracked from HCL so they are "true".
    """

    # ------------------------------------------------------------------------------------
    # Test tower.env - assert all core keys exist
    # ------------------------------------------------------------------------------------
    assert "Seqerakit - Using hosts file." in ansible_file_06
    assert "Seqerakit - Using insecure."   in ansible_file_06
    assert "Seqerakit - Using truststore." not in ansible_file_06


@pytest.mark.local
@pytest.mark.ansible
@pytest.mark.vpc_existing
@pytest.mark.long
def test_006_should_not_be_present(backup_tfvars, config_ansible_06_should_not_be_present):  # teardown_tf_state_all):
    """
    Test 
    """

    # Given
    print("Testing Ansible 02_update_file_configurations.yml.tpl.")

    # When
    outputs = config_ansible_06_should_not_be_present["planned_values"]["outputs"]
    variables = config_ansible_06_should_not_be_present["variables"]

    ansible_file_06 = read_file(f"{root}/assets/target/ansible/06_run_seqerakit.yml")

    """
    WARNING!!!!!!
      - Plan keys are in Python dictionary form, so JSON "true" becomes True.
            AFFECTS: `outputs` and `variables`
      - tower_env_file values are directly cracked from HCL so they are "true".
    """

    # ------------------------------------------------------------------------------------
    # Test tower.env - assert all core keys exist
    # ------------------------------------------------------------------------------------
    assert "Seqerakit - Using hosts file." not in ansible_file_06
    assert "Seqerakit - Using insecure."   not in ansible_file_06
    assert "Seqerakit - Using truststore." in ansible_file_06
