import pytest
import subprocess
import json
import os
import tempfile
import sys

from tests.utils.config import root, test_tfvars_target, test_tfvars_override_target, test_case_override_target
from tests.utils.config import ssm_tower, ssm_groundswell, ssm_seqerakit, ssm_wave_lite

from tests.utils.local import prepare_plan, run_terraform_apply, execute_subprocess
from tests.utils.local import get_reconciled_tfvars


from testcontainers.mysql import MySqlContainer



from tests.utils.config import ansible_file_list, all_ansible_files
from tests.utils.filehandling import read_json, read_yaml, read_file
from tests.utils.local import generate_tc_files, verify_all_assertions

from tests.datafiles.expected_results.expected_results import generate_assertions_all_active, generate_assertions_all_disabled


## ------------------------------------------------------------------------------------
## Test Ansible Configuration files
## ------------------------------------------------------------------------------------
# NOTE: To avoid creating VPC assets, use an existing VPC in the account the AWS provider is configured to use.


def assertion_modifiers_template():
    """
    Generate a blank dict for each testcase file to attach test-specific assertion modifiers to.
    These are then reconciled with the core set of assertions in `expected_results.py` (via `generate_assertions_xxx`).
    """
    return {k: {} for k in ansible_file_list}


@pytest.mark.local
@pytest.mark.ansible
def test_002_all_present(session_setup):  # teardown_tf_state_all):
    """
    Confirm that all conditional blocks are present.
    """

    # Given
    tf_modifiers        = """
        flag_create_external_db       = true
        flag_use_container_db         = false

        flag_create_external_redis    = true
        flag_use_container_redis      = false

        flag_create_load_balancer     = false
        flag_use_private_cacert       = true

        flag_enable_data_studio       = true
        flag_enable_groundswell       = true
        flag_use_wave_lite            = true
    """
    plan                           = prepare_plan(tf_modifiers)

    desired_files                       = ["ansible_02_update_file_configurations"]
    assertion_modifiers = assertion_modifiers_template()

    tc_files            = generate_tc_files(plan, desired_files, sys._getframe().f_code.co_name)
    # tc_assertions       = generate_assertions_all_active(tc_files, assertion_modifiers)

    ansible_file_02 = read_file(f"{tc_files['ansible_02_update_file_configurations']['filepath']}")

    assert "Populating external Platform DB." in ansible_file_02
    assert "Populating Wave Lite Postgres." in ansible_file_02
    assert "Populating external DB with Groundswell." in ansible_file_02
    assert "Configuring private certificates." in ansible_file_02
    assert "Creating data directory on host for Studios." in ansible_file_02


@pytest.mark.local
@pytest.mark.ansible
@pytest.mark.vpc_existing
@pytest.mark.long
def test_002_update_file_configurations_none_present(session_setup, config_ansible_02_should_not_be_present):  # teardown_tf_state_all):
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
def test_005_should_be_present(session_setup, config_ansible_05_should_be_present):  # teardown_tf_state_all):
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
def test_005_should_not_be_present(session_setup, config_ansible_05_should_not_be_present):  # teardown_tf_state_all):
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
def test_006_should_be_present(session_setup, config_ansible_06_should_be_present):  # teardown_tf_state_all):
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
def test_006_should_not_be_present(session_setup, config_ansible_06_should_not_be_present):  # teardown_tf_state_all):
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
