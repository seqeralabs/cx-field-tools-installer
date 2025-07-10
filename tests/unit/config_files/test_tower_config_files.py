import pytest
import subprocess

from tests.utils.local import root
from tests.utils.local import prepare_plan, run_terraform_apply, execute_subprocess
from tests.utils.local import parse_key_value_file


## ------------------------------------------------------------------------------------
## Tower Config keyss
## ------------------------------------------------------------------------------------
# NOTE: To avoid creating VPC assets, use an existing VPC in the account the AWS provider is configured to use.


@pytest.mark.local
@pytest.mark.config_keyss
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
    variables = config_baseline_settings_default["variables"]
    # execute_subprocess(f"terraform state list > terraform_state_list.txt")

    # Crack actual created keys
    tower_env_file = parse_key_value_file(
        f"{root}/assets/target/tower_config/tower.env"
    )
    print(f"{tower_env_file.items()=}")

    keys = tower_env_file.keys()
    # Test tower.env - assert all core keys exist
    assert "LICENSE_SERVER_URL" in keys
    assert "TOWER_SERVER_URL" in keys
    assert "TOWER_CONTACT_EMAIL" in keys
    assert "TOWER_ENABLE_PLATFORMS" in keys
    assert "TOWER_ROOT_USERS" in keys
    assert "TOWER_DB_URL" in keys
    assert "TOWER_DB_DRIVER" in keys
    assert "TOWER_DB_DIALECT" in keys
    assert "TOWER_DB_MIN_POOL_SIZE" in keys
    assert "TOWER_DB_MAX_POOL_SIZE" in keys
    assert "TOWER_DB_MAX_LIFETIME" in keys
    assert "FLYWAY_LOCATIONS" in keys
    assert "TOWER_REDIS_URL" in keys
    assert "WAVE_SERVER_URL" in keys
    assert "TOWER_DATA_EXPLORER_CLOUD_DISABLED_WORKSPACES" in keys

    # Test tower.env - assert some core keys NOT present
    assert "TOWER_DB_USER" not in keys
    assert "TOWER_DB_PASSWORD" not in keys
    assert "TOWER_SMTP_USER" not in keys
    assert "TOWER_SMTP_PASSWORD" not in keys

    ## Value checks

    # Test always-present conditionals
    # NOTE: Plan outputs are in Python dictionary form, so JSON "true" becomes True.
    assert "TOWER_ENABLE_AWS_SES" in keys
    if variables["flag_use_aws_ses_iam_integration"]["value"] == True:
        assert tower_env_file["TOWER_ENABLE_AWS_SES"] == "true"
    else:
        assert tower_env_file["TOWER_ENABLE_AWS_SES"] == "false"

    assert "TOWER_ENABLE_AWS_SSM" in keys
    assert "TOWER_ENABLE_UNSAFE_MODE" in keys
    assert "TOWER_ENABLE_WAVE" in keys
    assert "TOWER_ENABLE_GROUNDSWELL" in keys
    assert "TOWER_DATA_EXPLORER_ENABLED" in keys

    # Test sometimes-present conditionals
    # assert "TOWER_SMTP_HOST" in keys
    # assert "TOWER_SMTP_PORT" in keys
    # assert "GROUNDSWELL_SERVER_URL" in keys
    # assert "TOWER_DATA_STUDIO_ALLOWED_WORKSPACES" in keys
    # assert "TOWER_DATA_STUDIO_CONNECT_URL" in keys
    # assert "TOWER_OIDC_PEM_PATH" in keys
    # assert "TOWER_OIDC_REGISTRATION_INITIAL_ACCESS_TOKEN" in keys

    # assert "TOWER_DATA_STUDIO_TEMPLATES_${ds.qualifier}_ICON" in keys
    # assert "TOWER_DATA_STUDIO_TEMPLATES_${ds.qualifier}_REPOSITORY" in keys
    # assert "TOWER_DATA_STUDIO_TEMPLATES_${ds.qualifier}_TOOL" in keys
    # assert "TOWER_DATA_STUDIO_TEMPLATES_${ds.qualifier}_STATUS" in keys
