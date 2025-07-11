import pytest
import subprocess

from tests.utils.local import root
from tests.utils.local import prepare_plan, run_terraform_apply, execute_subprocess
from tests.utils.local import read_yaml
from tests.utils.local import parse_key_value_file


## ------------------------------------------------------------------------------------
## Tower Config File Checks
## ------------------------------------------------------------------------------------
# NOTE: To avoid creating VPC assets, use an existing VPC in the account the AWS provider is configured to use.


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.quick
def test_default_config_tower_env(backup_tfvars, config_baseline_settings_default):  # teardown_tf_state_all):
    """
    Test the target tower.env generated from default test terraform.tfvars and base-override.auto.tfvars.
    """

    # Given
    print("Testing tower.env generated from default settings.")

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


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.quick
def test_default_config_tower_yml(backup_tfvars, config_baseline_settings_default):  # teardown_tf_state_all):
    """
    Test the target tower.yml generated from default test terraform.tfvars and base-override.auto.tfvars.
    """

    # Given
    print("Testing tower.yml generated from default settings.")

    # When
    outputs = config_baseline_settings_default["planned_values"]["outputs"]
    variables = config_baseline_settings_default["variables"]

    tower_yml_file = read_yaml(f"{root}/assets/target/tower_config/tower.yml")

    """
    WARNING!!!!!!
      - Plan keys are in Python dictionary form, so JSON "true" becomes True.
            AFFECTS: `outputs` and `variables`
      - tower_env_file values are directly cracked from HCL so they are "true".
    """

    # ------------------------------------------------------------------------------------
    # Test tower.yml
    # ------------------------------------------------------------------------------------
    key = tower_yml_file["mail"]["smtp"]["auth"]
    value = variables["tower_smtp_auth"]["value"]
    assert key == value

    key = tower_yml_file["mail"]["smtp"]["starttls"]["enable"]
    value = variables["tower_smtp_starttls_enable"]["value"]
    assert key == value

    key = tower_yml_file["mail"]["smtp"]["starttls"]["required"]
    value = variables["tower_smtp_starttls_required"]["value"]
    assert key == value

    key = tower_yml_file["mail"]["smtp"]["ssl"]["protocols"]
    value = variables["tower_smtp_ssl_protocols"]["value"]
    assert key == value

    key = tower_yml_file["micronaut"]["application"]["name"]
    value = variables["app_name"]["value"]
    assert key == value

    if variables["flag_disable_email_login"]["value"]:
        key = tower_yml_file["tower"]["auth"]["disable-email"]
        assert key
    else:
        assert "auth" not in tower_yml_file["tower"].keys()

    # Note this has time segment at end.
    key = tower_yml_file["tower"]["cron"]["audit-log"]["clean-up"]["time-offset"]
    value = variables["tower_audit_retention_days"]["value"]
    assert key == f"{value}d"

    # TODO verify why I did this in the template
    flag_enable_data_studio = variables["flag_enable_data_studio"]["value"]
    flag_limit_data_studio_to_some_workspaces = variables["flag_limit_data_studio_to_some_workspaces"]["value"]
    if flag_enable_data_studio and flag_limit_data_studio_to_some_workspaces:
        key = tower_yml_file["tower"]["data-studio"]["allowed-workspaces"]
        assert key == None
    else:
        assert "data-studio" not in tower_yml_file["tower"].keys()

    # Remove middle whitespace from vars since it seems to be stripped from the template interpolation.
    key = tower_yml_file["tower"]["trustedEmails"]
    tower_root_users = variables["tower_root_users"]["value"].replace(" ", "")
    tower_email_trusted_orgs = variables["tower_email_trusted_orgs"]["value"].replace(" ", "")
    tower_email_trusted_users = variables["tower_email_trusted_users"]["value"].replace(" ", "")

    # assert all(val in key for val in [tower_root_users, tower_email_trusted_orgs, tower_email_trusted_users])
    assert tower_root_users in key
    assert tower_email_trusted_orgs in key
    assert tower_email_trusted_users in key


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.quick
def test_default_config_data_studios_env(backup_tfvars, config_baseline_settings_default):
    """
    Test the target data-studio.env generated from default test terraform.tfvars and base-override.auto.tfvars.
    """

    # Given
    print("Testing data-studio.env generated from default settings.")

    # When
    outputs = config_baseline_settings_default["planned_values"]["outputs"]
    variables = config_baseline_settings_default["variables"]

    ds_env_file = parse_key_value_file(f"{root}/assets/target/tower_config/data-studios.env")
    print(f"{ds_env_file.items()=}")
    keys = ds_env_file.keys()

    """
    WARNING!!!!!!
      - Plan keys are in Python dictionary form, so JSON "true" becomes True.
            AFFECTS: `outputs` and `variables`
      - tower_env_file values are directly cracked from HCL so they are "true".
    """

    # ------------------------------------------------------------------------------------
    # Test data-studios.env - assert all core keys exist
    # ------------------------------------------------------------------------------------
    key = "PLATFORM_URL"
    value = outputs["tower_server_url"]["value"]
    assert key in keys
    assert ds_env_file[key] == value

    key = "CONNECT_HTTP_PORT"
    value = 9090
    assert key in keys
    assert ds_env_file[key] == str(value)

    key = "CONNECT_TUNNEL_URL"
    value = "connect-server:7070"
    assert key in keys
    assert ds_env_file[key] == value

    key = "CONNECT_PROXY_URL"
    value = outputs["tower_connect_server_url"]["value"]
    assert key in keys
    assert ds_env_file[key] == value

    key = "CONNECT_REDIS_ADDRESS"
    value = outputs["tower_redis_url"]["value"]
    assert key in keys
    assert f"redis://{ds_env_file[key]}" == value

    key = "CONNECT_REDIS_DB"
    value = 1
    assert key in keys
    assert ds_env_file[key] == str(value)

    key = "CONNECT_OIDC_CLIENT_REGISTRATION_TOKEN"
    value = '"ipsemlorem"'  # TODO: Find better solution for this. Hacky.
    assert key in keys
    assert ds_env_file[key] == value

    # TODO: Figure out how to use local.studio_uses_distroless for better targeting.
    key = "CONNECT_LOG_LEVEL"
    key2 = "CONNECT_SERVER_LOG_LEVEL"
    if key in keys:
        assert key2 not in keys
    else:
        assert key2 in keys
