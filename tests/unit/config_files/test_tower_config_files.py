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
@pytest.mark.vpc_existing
@pytest.mark.quick
def test_config_baseline_settings_default(
    backup_tfvars, config_baseline_settings_default
):  # teardown_tf_state_all):
    """
    Test the target folder generated from default test terraform.tfvars and base-override.auto.tfvars.
    """

    # Given
    print("Testing target/ folder generated from default settings.")

    # When
    outputs = config_baseline_settings_default["planned_values"]["outputs"]
    # execute_subprocess(f"terraform state list > terraform_state_list.txt")

    # Crack actual created file
    file = parse_key_value_file(f"{root}/assets/target/tower_config/tower.env")

    # THOUGHT: THIS SHOULD ACTUALLY BE A session fixture so I can do the plan once and then break up test cases across files.

    print(f"{file.keys()=}")

    # Test tower.env - assert all core keys exist
    assert "LICENSE_SERVER_URL" in file
    assert "TOWER_SERVER_URL" in file
    assert "TOWER_CONTACT_EMAIL" in file
    assert "TOWER_ENABLE_PLATFORMS" in file
    assert "TOWER_ROOT_USERS" in file
    assert "TOWER_DB_URL" in file
    assert "TOWER_DB_DRIVER" in file
    assert "TOWER_DB_DIALECT" in file
    assert "TOWER_DB_MIN_POOL_SIZE" in file
    assert "TOWER_DB_MAX_POOL_SIZE" in file
    assert "TOWER_DB_MAX_LIFETIME" in file
    assert "FLYWAY_LOCATIONS" in file
    assert "TOWER_REDIS_URL" in file
    assert "WAVE_SERVER_URL" in file
    assert "TOWER_DATA_EXPLORER_CLOUD_DISABLED_WORKSPACES" in file

    # Test tower.env - assert some core keys NOT present
    assert "TOWER_DB_USER" not in file
    assert "TOWER_DB_PASSWORD" not in file
    assert "TOWER_SMTP_USER" not in file
    assert "TOWER_SMTP_PASSWORD" not in file

    ## Value checks

    # Test always-present conditionals
    assert "TOWER_ENABLE_AWS_SSM" in file
    assert "TOWER_ENABLE_AWS_SES" in file
    assert "TOWER_ENABLE_UNSAFE_MODE" in file
    assert "TOWER_ENABLE_WAVE" in file
    assert "TOWER_ENABLE_GROUNDSWELL" in file
    assert "TOWER_DATA_EXPLORER_ENABLED" in file

    # Test sometimes-present conditionals
    # assert "TOWER_SMTP_HOST" in file
    # assert "TOWER_SMTP_PORT" in file
    # assert "GROUNDSWELL_SERVER_URL" in file
    # assert "TOWER_DATA_STUDIO_ALLOWED_WORKSPACES" in file
    # assert "TOWER_DATA_STUDIO_CONNECT_URL" in file
    # assert "TOWER_OIDC_PEM_PATH" in file
    # assert "TOWER_OIDC_REGISTRATION_INITIAL_ACCESS_TOKEN" in file

    # assert "TOWER_DATA_STUDIO_TEMPLATES_${ds.qualifier}_ICON" in file
    # assert "TOWER_DATA_STUDIO_TEMPLATES_${ds.qualifier}_REPOSITORY" in file
    # assert "TOWER_DATA_STUDIO_TEMPLATES_${ds.qualifier}_TOOL" in file
    # assert "TOWER_DATA_STUDIO_TEMPLATES_${ds.qualifier}_STATUS" in file
