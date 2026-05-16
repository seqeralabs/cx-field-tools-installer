import sys

import pytest
from tests.utils.filehandling import FileHelper
from tests.utils.terraform.executor import stage_tfvars
from tests.utils.terraform.template_generator import generate_tc_files


## ------------------------------------------------------------------------------------
## MARK: File 002
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.ansible
def test_002_all_present(session_setup):
    """Confirm that all conditional blocks are present."""
    tf_modifiers = """
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
    stage_tfvars(tf_modifiers)

    desired_files = ["ansible_02_update_file_configurations"]
    # Kept for consistency with config-file tests; ansible tests use inline string assertions.
    # assertion_modifiers = assertion_modifiers_template()

    tc_files = generate_tc_files(None, desired_files, sys._getframe().f_code.co_name)
    # tc_assertions = generate_assertions_all_active(tc_files, assertion_modifiers)

    ansible_file_02 = FileHelper.read_file(f"{tc_files['ansible_02_update_file_configurations']['filepath']}")
    assert "Populating external Platform DB." in ansible_file_02
    assert "Populating Wave Lite Postgres." in ansible_file_02
    assert "Populating external DB with Groundswell." in ansible_file_02
    assert "Configuring private certificates." in ansible_file_02
    assert "Creating data directory on host for Studios." in ansible_file_02


@pytest.mark.local
@pytest.mark.ansible
def test_002_none_present(session_setup):
    """Confirm that no conditional blocks are present."""
    # Given
    tf_modifiers = """
        flag_create_external_db       = false
        flag_use_container_db         = true

        flag_create_external_redis    = false
        flag_use_container_redis      = true

        flag_create_load_balancer     = true
        flag_use_private_cacert       = false

        flag_enable_data_studio       = false
        flag_enable_groundswell       = false
        flag_use_wave_lite            = false
    """
    stage_tfvars(tf_modifiers)

    desired_files = ["ansible_02_update_file_configurations"]
    # Kept for consistency with config-file tests; ansible tests use inline string assertions.
    # assertion_modifiers = assertion_modifiers_template()

    tc_files = generate_tc_files(None, desired_files, sys._getframe().f_code.co_name)
    # tc_assertions = generate_assertions_all_disabled(tc_files, assertion_modifiers)

    ansible_file_02 = FileHelper.read_file(f"{tc_files['ansible_02_update_file_configurations']['filepath']}")
    assert "Populating external Platform DB." not in ansible_file_02
    assert "Populating Wave Lite Postgres." not in ansible_file_02
    assert "Populating external DB with Groundswell." not in ansible_file_02
    assert "Configuring private certificates." not in ansible_file_02
    assert "Creating data directory on host for Studios." not in ansible_file_02


## ------------------------------------------------------------------------------------
## MARK: File 005
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.ansible
def test_005_all_present(session_setup):  # teardown_tf_state_all):
    """Confirm that all conditional blocks are present."""
    tf_modifiers = """
        flag_create_external_db       = false
        flag_use_container_db         = true

        flag_enable_groundswell       = true
    """
    stage_tfvars(tf_modifiers)

    desired_files = ["ansible_05_patch_groundswell"]
    # Kept for consistency with config-file tests; ansible tests use inline string assertions.
    # assertion_modifiers = assertion_modifiers_template()

    tc_files = generate_tc_files(None, desired_files, sys._getframe().f_code.co_name)
    # tc_assertions = generate_assertions_all_active(tc_files, assertion_modifiers)

    ansible_file_05 = FileHelper.read_file(f"{tc_files['ansible_05_patch_groundswell']['filepath']}")
    assert "Patching container db with groundswell init script." in ansible_file_05


@pytest.mark.local
@pytest.mark.ansible
def test_005_none_present(session_setup):
    """Confirm that no conditional blocks are present."""
    tf_modifiers = """
        flag_create_external_db       = false
        flag_use_container_db         = true

        flag_enable_groundswell       = false
    """
    stage_tfvars(tf_modifiers)

    desired_files = ["ansible_05_patch_groundswell"]
    # Kept for consistency with config-file tests; ansible tests use inline string assertions.
    # assertion_modifiers = assertion_modifiers_template()

    tc_files = generate_tc_files(None, desired_files, sys._getframe().f_code.co_name)
    # tc_assertions = generate_assertions_all_disabled(tc_files, assertion_modifiers)

    ansible_file_05 = FileHelper.read_file(f"{tc_files['ansible_05_patch_groundswell']['filepath']}")
    assert "Patching container db with groundswell init script." not in ansible_file_05


## ------------------------------------------------------------------------------------
## MARK: File 006
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.ansible
def test_006_all_present(session_setup):
    """Confirm that all conditional blocks are present."""
    tf_modifiers = """
        flag_create_hosts_file_entry  = true
        flag_do_not_use_https         = true
    """
    stage_tfvars(tf_modifiers)

    desired_files = ["ansible_06_run_seqerakit"]
    # Kept for consistency with config-file tests; ansible tests use inline string assertions.
    # assertion_modifiers = assertion_modifiers_template()

    tc_files = generate_tc_files(None, desired_files, sys._getframe().f_code.co_name)
    # tc_assertions = generate_assertions_all_active(tc_files, assertion_modifiers)

    ansible_file_06 = FileHelper.read_file(f"{tc_files['ansible_06_run_seqerakit']['filepath']}")
    assert "Seqerakit - Using hosts file." in ansible_file_06
    assert "Seqerakit - Using insecure." in ansible_file_06
    assert "Seqerakit - Using truststore." not in ansible_file_06


@pytest.mark.local
@pytest.mark.ansible
def test_006_none_present(session_setup):
    """Confirm that no conditional blocks are present."""
    tf_modifiers = """
        flag_create_external_db       = false
        flag_use_container_db         = true

        flag_enable_groundswell       = false
    """
    stage_tfvars(tf_modifiers)

    desired_files = ["ansible_06_run_seqerakit"]
    # Kept for consistency with config-file tests; ansible tests use inline string assertions.
    # assertion_modifiers = assertion_modifiers_template()

    tc_files = generate_tc_files(None, desired_files, sys._getframe().f_code.co_name)
    # tc_assertions = generate_assertions_all_disabled(tc_files, assertion_modifiers)

    ansible_file_06 = FileHelper.read_file(f"{tc_files['ansible_06_run_seqerakit']['filepath']}")
    assert "Seqerakit - Using hosts file." not in ansible_file_06
    assert "Seqerakit - Using insecure." not in ansible_file_06
    assert "Seqerakit - Using truststore." in ansible_file_06
