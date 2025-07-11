import pytest
import subprocess

from tests.utils.local import root
from tests.utils.local import prepare_plan, run_terraform_apply, execute_subprocess
from tests.utils.local import parse_key_value_file


## ------------------------------------------------------------------------------------
## Tower Config keys
## ------------------------------------------------------------------------------------
# NOTE: To avoid creating VPC assets, use an existing VPC in the account the AWS provider is configured to use.


@pytest.mark.local
@pytest.mark.config_keyss
@pytest.mark.vpc_existing
@pytest.mark.quick
def test_default_config_tower_env(backup_tfvars, config_baseline_settings_default):  # teardown_tf_state_all):
    """
    Test the target folder generated from default test terraform.tfvars and base-override.auto.tfvars.
    """

    # Given
    print("Testing target/ folder generated from default settings.")

    # When
    outputs = config_baseline_settings_default["planned_values"]["outputs"]
    variables = config_baseline_settings_default["variables"]

    tower_env_file = parse_key_value_file(f"{root}/assets/target/tower_config/tower.env")
    print(f"{tower_env_file.items()=}")
    keys = tower_env_file.keys()

    """
    WARNING!!!!!!
      - Plan keys are in Python dictionary form, so JSON "true" becomes True.
            AFFECTS: `outputs` and `variables`
      - tower_env_file values are directly cracked from HCL so they are "true".
    """

    # ------------------------------------------------------------------------------------
    # Test tower.env - assert all core keys exist
    # ------------------------------------------------------------------------------------
    key = "TOWER_ENABLE_AWS_SSM"
    value = "true"
    assert key in keys
    assert tower_env_file[key] == value

    key = "LICENSE_SERVER_URL"
    value = "https://licenses.seqera.io"
    assert key in keys
    assert tower_env_file[key] == value

    key = "TOWER_SERVER_URL"
    value = outputs["tower_server_url"]["value"]
    assert key in keys
    assert tower_env_file[key] == value

    key = "TOWER_CONTACT_EMAIL"
    value = variables["tower_contact_email"]["value"]
    assert key in keys
    assert tower_env_file[key] == value

    key = "TOWER_ENABLE_PLATFORMS"
    value = variables["tower_enable_platforms"]["value"]
    assert key in keys
    assert tower_env_file[key] == value

    key = "TOWER_ROOT_USERS"
    value = variables["tower_root_users"]["value"]
    assert key in keys
    assert tower_env_file[key] == value

    key = "TOWER_DB_URL"
    value = outputs["tower_db_url"]["value"]
    assert key in keys
    assert tower_env_file[key] == value

    key = "TOWER_DB_DRIVER"
    value = variables["tower_db_driver"]["value"]
    assert key in keys
    assert tower_env_file["TOWER_DB_DRIVER"] == value

    key = "TOWER_DB_DIALECT"
    value = variables["tower_db_dialect"]["value"]
    assert key in keys
    assert tower_env_file["TOWER_DB_DIALECT"] == value

    key = "TOWER_DB_MIN_POOL_SIZE"
    value = variables["tower_db_min_pool_size"]["value"]
    assert key in keys
    assert tower_env_file["TOWER_DB_MIN_POOL_SIZE"] == str(value)

    key = "TOWER_DB_MAX_POOL_SIZE"
    value = variables["tower_db_max_pool_size"]["value"]
    assert key in keys
    assert tower_env_file["TOWER_DB_MAX_POOL_SIZE"] == str(value)

    key = "TOWER_DB_MAX_LIFETIME"
    value = variables["tower_db_max_lifetime"]["value"]
    assert key in keys
    assert tower_env_file["TOWER_DB_MAX_LIFETIME"] == str(value)

    key = "FLYWAY_LOCATIONS"
    value = variables["flyway_locations"]["value"]
    assert key in keys
    assert tower_env_file["FLYWAY_LOCATIONS"] == value

    key = "TOWER_REDIS_URL"
    value = outputs["tower_redis_url"]["value"]
    assert key in keys
    assert tower_env_file["TOWER_REDIS_URL"] == value

    key = "WAVE_SERVER_URL"
    value = outputs["tower_wave_url"]["value"]
    assert key in keys
    assert tower_env_file[key] == value

    # ------------------------------------------------------------------------------------
    # Test always-present conditionals
    # ------------------------------------------------------------------------------------
    key = "TOWER_ENABLE_AWS_SES"
    value = variables["flag_use_aws_ses_iam_integration"]["value"]
    assert key in keys
    assert tower_env_file[key] == ("true" if value else "false")

    key = "TOWER_ENABLE_UNSAFE_MODE"
    value = variables["flag_do_not_use_https"]["value"]
    assert key in keys
    assert tower_env_file[key] == ("true" if value else "false")

    key = "TOWER_ENABLE_WAVE"
    value = variables["flag_use_wave"]["value"]
    assert key in keys
    assert tower_env_file[key] == ("true" if value else "false")

    key = "TOWER_ENABLE_GROUNDSWELL"
    value = variables["flag_enable_groundswell"]["value"]
    assert key in keys
    assert tower_env_file[key] == ("true" if value else "false")

    key = "TOWER_DATA_EXPLORER_ENABLED"
    value = variables["flag_data_explorer_enabled"]["value"]
    assert key in keys
    assert tower_env_file[key] == ("true" if value else "false")

    # ------------------------------------------------------------------------------------
    # Test tower.env - assert some core keys NOT present
    # ------------------------------------------------------------------------------------
    key = "TOWER_DB_USER"
    assert key not in keys

    key = "TOWER_DB_PASSWORD"
    assert key not in keys

    key = "TOWER_SMTP_USER"
    assert key not in keys

    key = "TOWER_SMTP_PASSWORD"
    assert key not in keys

    # ------------------------------------------------------------------------------------
    # Test sometimes-present conditionals
    # ------------------------------------------------------------------------------------
    key = "TOWER_SMTP_HOST"
    value = variables["tower_smtp_host"]["value"]
    flag_use_existing_smtp = variables["flag_use_existing_smtp"]["value"]
    if flag_use_existing_smtp:
        assert key in keys
        assert tower_env_file[key] == value
    else:
        assert key not in keys

    key = "TOWER_SMTP_PORT"
    value = variables["tower_smtp_port"]["value"]
    flag_use_existing_smtp = variables["flag_use_existing_smtp"]["value"]
    if flag_use_existing_smtp:
        assert key in keys
        assert tower_env_file[key] == value
    else:
        assert key not in keys

    key = "GROUNDSWELL_SERVER_URL"
    value = outputs["swell_db_url"]["value"]
    flag_enable_groundswell = variables["flag_enable_groundswell"]["value"]
    if flag_enable_groundswell:
        assert key in keys
        assert tower_env_file[key] == value
    else:
        assert key not in keys

    key = "TOWER_DATA_EXPLORER_CLOUD_DISABLED_WORKSPACES"
    value = variables["data_explorer_disabled_workspaces"]["value"]
    flag_data_explorer_enabled = variables["flag_data_explorer_enabled"]["value"]
    if flag_data_explorer_enabled:
        assert key in keys
        assert tower_env_file[key] == value
    else:
        assert key not in keys

    # ------------------------------------------------------------------------------------
    # Test sometimes-present conditionals - Data studio
    # ------------------------------------------------------------------------------------
    # All keys locked behind the `flag_enable_data_studio` flag.
    flag_enable_data_studio = variables["flag_enable_data_studio"]["value"]

    key = "TOWER_DATA_STUDIO_ALLOWED_WORKSPACES"
    value = variables["data_studio_eligible_workspaces"]["value"]
    flag_limit_data_studio_to_some_workspaces = variables["flag_limit_data_studio_to_some_workspaces"]["value"]
    if flag_enable_data_studio and flag_limit_data_studio_to_some_workspaces:
        assert key in keys
        assert tower_env_file[key] == value
    else:
        assert key not in keys

    key = "TOWER_DATA_STUDIO_CONNECT_URL"
    value = outputs["tower_connect_server_url"]["value"]
    if flag_enable_data_studio:
        assert key in keys
        assert tower_env_file[key] == value
    else:
        assert key not in keys

    key = "TOWER_OIDC_PEM_PATH"
    value = "/data-studios-rsa.pem"
    if flag_enable_data_studio:
        assert key in keys
        assert tower_env_file[key] == value
    else:
        assert key not in keys

    key = "TOWER_OIDC_REGISTRATION_INITIAL_ACCESS_TOKEN"
    value = "ipsemlorem"
    if flag_enable_data_studio:
        assert key in keys
        assert tower_env_file[key] == value
    else:
        assert key not in keys

    # TODO: Align this edgecase in project?
    for studio in variables["data_studio_options"]["value"]:
        if flag_enable_data_studio:
            for qualifier in ["ICON", "REPOSITORY", "TOOL", "STATUS"]:
                key = "TOWER_DATA_STUDIO_TEMPLATES_${studio}_{qualifier}"
                # EDGECASE: Called it 'container' in terrafrom tfvars, but setting is REPOSITORY
                if qualifier == "REPOSITORY":
                    value = variables["data_studio_options"]["value"][studio]["container"]
                else:
                    value = variables["data_studio_options"]["value"][studio][key.lower()]
            assert key in keys
            assert tower_env_file[key] == value
        else:
            assert key not in keys
