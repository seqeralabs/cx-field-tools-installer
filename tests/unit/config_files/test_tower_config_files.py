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
## Tower Config File Checks
## ------------------------------------------------------------------------------------
# NOTE: To avoid creating VPC assets, use an existing VPC in the account the AWS provider is configured to use.


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
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
    # TODO: Refactor this to be more compact / efficient
    key = "TOWER_ENABLE_AWS_SSM"
    value = "true"
    assert tower_env_file[key] == value

    key = "LICENSE_SERVER_URL"
    value = "https://licenses.seqera.io"
    assert tower_env_file[key] == value

    key = "TOWER_SERVER_URL"
    value = outputs["tower_server_url"]["value"]
    assert tower_env_file[key] == value

    key = "TOWER_CONTACT_EMAIL"
    value = variables["tower_contact_email"]["value"]
    assert tower_env_file[key] == value

    key = "TOWER_ENABLE_PLATFORMS"
    value = variables["tower_enable_platforms"]["value"]
    assert tower_env_file[key] == value

    key = "TOWER_ROOT_USERS"
    value = variables["tower_root_users"]["value"]
    assert tower_env_file[key] == value

    key = "TOWER_DB_URL"
    value = outputs["tower_db_url"]["value"]
    assert tower_env_file[key] == value

    key = "TOWER_DB_DRIVER"
    value = variables["tower_db_driver"]["value"]
    assert tower_env_file["TOWER_DB_DRIVER"] == value

    key = "TOWER_DB_DIALECT"
    value = variables["tower_db_dialect"]["value"]
    assert tower_env_file["TOWER_DB_DIALECT"] == value

    key = "TOWER_DB_MIN_POOL_SIZE"
    value = variables["tower_db_min_pool_size"]["value"]
    assert tower_env_file["TOWER_DB_MIN_POOL_SIZE"] == str(value)

    key = "TOWER_DB_MAX_POOL_SIZE"
    value = variables["tower_db_max_pool_size"]["value"]
    assert tower_env_file["TOWER_DB_MAX_POOL_SIZE"] == str(value)

    key = "TOWER_DB_MAX_LIFETIME"
    value = variables["tower_db_max_lifetime"]["value"]
    assert tower_env_file["TOWER_DB_MAX_LIFETIME"] == str(value)

    key = "FLYWAY_LOCATIONS"
    value = variables["flyway_locations"]["value"]
    assert tower_env_file["FLYWAY_LOCATIONS"] == value

    key = "TOWER_REDIS_URL"
    value = outputs["tower_redis_url"]["value"]
    assert tower_env_file["TOWER_REDIS_URL"] == value

    key = "WAVE_SERVER_URL"
    value = outputs["tower_wave_url"]["value"]
    assert tower_env_file[key] == value

    # ------------------------------------------------------------------------------------
    # Test always-present conditionals
    # ------------------------------------------------------------------------------------
    key = "TOWER_ENABLE_AWS_SES"
    value = variables["flag_use_aws_ses_iam_integration"]["value"]
    assert tower_env_file[key] == ("true" if value else "false")

    key = "TOWER_ENABLE_UNSAFE_MODE"
    value = variables["flag_do_not_use_https"]["value"]
    assert tower_env_file[key] == ("true" if value else "false")

    key = "TOWER_ENABLE_WAVE"
    value1 = variables["flag_use_wave"]["value"]
    value2 = variables["flag_use_wave_lite"]["value"]
    assert tower_env_file[key] == ("true" if value1 or value2 else "false")

    key = "TOWER_ENABLE_GROUNDSWELL"
    value = variables["flag_enable_groundswell"]["value"]
    assert tower_env_file[key] == ("true" if value else "false")

    key = "TOWER_DATA_EXPLORER_ENABLED"
    value = variables["flag_data_explorer_enabled"]["value"]
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
        assert tower_env_file[key] == value
    else:
        assert key not in keys

    key = "TOWER_SMTP_PORT"
    value = variables["tower_smtp_port"]["value"]
    flag_use_existing_smtp = variables["flag_use_existing_smtp"]["value"]
    if flag_use_existing_smtp:
        assert tower_env_file[key] == value
    else:
        assert key not in keys

    key = "GROUNDSWELL_SERVER_URL"
    value = "http://groundswell:8090"
    flag_enable_groundswell = variables["flag_enable_groundswell"]["value"]
    if flag_enable_groundswell:
        assert tower_env_file[key] == value
    else:
        assert key not in keys

    key = "TOWER_DATA_EXPLORER_CLOUD_DISABLED_WORKSPACES"
    value = variables["data_explorer_disabled_workspaces"]["value"]
    flag_data_explorer_enabled = variables["flag_data_explorer_enabled"]["value"]
    if flag_data_explorer_enabled:
        assert tower_env_file[key] == value
    else:
        assert key not in keys

    # ------------------------------------------------------------------------------------
    # Test sometimes-present conditionals - Data studio
    # ------------------------------------------------------------------------------------
    # All keys locked behind the `flag_enable_data_studio` flag.
    flag_enable_data_studio = variables["flag_enable_data_studio"]["value"]
    flag_studio_enable_path_routing = variables["flag_studio_enable_path_routing"]["value"]
    flag_limit_data_studio_to_some_workspaces = variables["flag_limit_data_studio_to_some_workspaces"]["value"]

    key = "TOWER_DATA_STUDIO_ENABLE_PATH_ROUTING"
    if flag_enable_data_studio and not flag_studio_enable_path_routing:
        assert tower_env_file[key] == "false"

    key = "TOWER_DATA_STUDIO_ALLOWED_WORKSPACES"
    value = variables["data_studio_eligible_workspaces"]["value"]
    if flag_enable_data_studio and flag_limit_data_studio_to_some_workspaces:
        assert tower_env_file[key] == value
    else:
        assert key not in keys

    key = "TOWER_DATA_STUDIO_CONNECT_URL"
    value = outputs["tower_connect_server_url"]["value"]
    if flag_enable_data_studio:
        assert tower_env_file[key] == value
        assert "connect." in tower_env_file[key]
    else:
        assert key not in keys

    key = "TOWER_OIDC_PEM_PATH"
    value = "/data-studios-rsa.pem"
    if flag_enable_data_studio:
        assert tower_env_file[key] == value
    else:
        assert key not in keys

    key = "TOWER_OIDC_REGISTRATION_INITIAL_ACCESS_TOKEN"
    value = "ipsemlorem"
    if flag_enable_data_studio:
        assert tower_env_file[key] == value
    else:
        assert key not in keys

    # TODO: Align this edgecase in project?
    for studio in variables["data_studio_options"]["value"]:
        if flag_enable_data_studio:
            for qualifier in ["ICON", "REPOSITORY", "TOOL", "STATUS"]:
                key = f"TOWER_DATA_STUDIO_TEMPLATES_{studio}_{qualifier}"
                # EDGECASE: Called it 'container' in terrafrom tfvars, but setting is REPOSITORY
                if qualifier == "REPOSITORY":
                    value = variables["data_studio_options"]["value"][studio]["container"]
                else:
                    value = variables["data_studio_options"]["value"][studio][qualifier.lower()]
            assert key.upper() in keys
            assert tower_env_file[key.upper()] == value
        else:
            assert key not in keys


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
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
    if flag_enable_data_studio and not flag_limit_data_studio_to_some_workspaces:
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
@pytest.mark.long
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
    assert ds_env_file[key] == value

    key = "CONNECT_HTTP_PORT"
    value = 9090
    assert ds_env_file[key] == str(value)

    key = "CONNECT_TUNNEL_URL"
    value = "connect-server:7070"
    assert ds_env_file[key] == value

    key = "CONNECT_PROXY_URL"
    value = outputs["tower_connect_server_url"]["value"]
    assert ds_env_file[key] == value
    assert "connect." in ds_env_file[key]

    key = "CONNECT_REDIS_ADDRESS"
    value = outputs["tower_redis_url"]["value"]
    assert f"redis://{ds_env_file[key]}" == value

    key = "CONNECT_REDIS_DB"
    value = 1
    assert ds_env_file[key] == str(value)

    key = "CONNECT_OIDC_CLIENT_REGISTRATION_TOKEN"
    value = "ipsemlorem"
    assert ds_env_file[key] == value

    # TODO: Figure out how to use local.studio_uses_distroless for better targeting.
    key = "CONNECT_LOG_LEVEL"
    key2 = "CONNECT_SERVER_LOG_LEVEL"
    if key in keys:
        assert key2 not in keys
    else:
        assert key2 in keys


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
def test_default_config_tower_sql(backup_tfvars, config_baseline_settings_default):
    """
    Test the target tower.sql generated from default test terraform.tfvars and base-override.auto.tfvars.
    """

    # Given
    tfvars = get_reconciled_tfvars()

    # Get values for comparison
    db_database_name = tfvars["db_database_name"]
    ssm_data = read_json(ssm_tower)
    sql_content = read_file(f"{root}/assets/target/tower_config/tower.sql")

    # Remove quotes from database name if present
    expected_db_name = db_database_name
    expected_user = ssm_data["TOWER_DB_USER"]["value"]
    expected_password = ssm_data["TOWER_DB_PASSWORD"]["value"]

    # ------------------------------------------------------------------------------------
    # Test tower.sql - validate all interpolated variables are properly replaced
    # ------------------------------------------------------------------------------------
    assert f"CREATE DATABASE {expected_db_name};" in sql_content
    assert f"ALTER DATABASE {expected_db_name} CHARACTER SET utf8 COLLATE utf8_bin;" in sql_content
    assert f'GRANT ALL PRIVILEGES ON {expected_db_name}.* TO {expected_user}@"%";' in sql_content

    # Test that user credentials are properly interpolated
    assert f'CREATE USER "{expected_user}" IDENTIFIED BY "{expected_password}";' in sql_content

    # Additional validation: ensure no template variables remain
    assert "${db_database_name}" not in sql_content
    assert "${db_tower_user}" not in sql_content
    assert "${db_tower_password}" not in sql_content


@pytest.mark.local
@pytest.mark.db
@pytest.mark.mysql_container
@pytest.mark.long
@pytest.mark.testcontainer
def test_tower_sql_mysql_container_execution(backup_tfvars, config_baseline_settings_default):
    """
    Test that tower.sql successfully populates a MySQL8 database using Testcontainers.
    This validates the SQL file can create the database, user, and grant permissions.

    NOTE:
    Container DB cant be connected to via master creds like standard RDS.
    Emulate by creating one user "test", then run the script that we'd normally run against RDS with the master user.
    Then try to log in with the "tower" user.

    Cant use `mysql_container.get_container_host_ip()` because it returns `localhost` and we need the host's actual IP.
    """

    # Given
    tfvars = get_reconciled_tfvars()
    ssm_data = read_json(ssm_tower)
    sql_content = read_file(f"{root}/assets/target/tower_config/tower.sql")

    # Note: Hack to emulate RDS master user / password.
    # TODO: Use the master user / password from the SSM values.
    mock_master_user = "root"
    mock_master_password = "test"
    mock_db_name = "test"

    tower_db_user = ssm_data["TOWER_DB_USER"]["value"]
    tower_db_password = ssm_data["TOWER_DB_PASSWORD"]["value"]
    tower_db_name = tfvars["db_database_name"]

    # When - Execute SQL against MySQL container
    with (
        MySqlContainer("mysql:8.0", root_password=mock_master_password)
        .with_env("MYSQL_USER", mock_master_user)
        .with_env("MYSQL_PASSWORD", mock_master_password)
        .with_env("MYSQL_DATABASE", mock_db_name)
        .with_bind_ports(3306, 3306)
    ) as mysql_container:
        # Create temporary SQL file for docker volume mount
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as temp_sql:
            temp_sql.write(sql_content)
            temp_sql_path = temp_sql.name

        try:
            # Emulate execution of RDS prepping script in Ansilble.
            # NOTE: Since we cant change the container master user from 'root', fudging login with another "master" user.
            #   This is a hack, but it serves its purpose given the constraints.
            docker_cmd = f"""
                docker run --rm -t -v {temp_sql_path}:/tower.sql \
                  -e MYSQL_PWD={mock_master_password} --entrypoint /bin/bash \
                  --add-host host.docker.internal:host-gateway mysql:8.0 \
                  -c 'mysql --host host.docker.internal --port=3306 --user={mock_master_user} < tower.sql'
            """
            result = subprocess.run(docker_cmd, shell=True, capture_output=True, text=True, timeout=60)
            assert result.returncode == 0

            # Then - Verify database operations using MySQL container commands
            def run_mysql_query(query, user=mock_master_user, password=mock_master_password, database=None):
                """Helper function to run MySQL queries using container commands"""

                # Create temporary SQL file for docker volume mount (avoids nested quotes nightmare)
                with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as query_sql:
                    query_sql.write(query)
                    query_sql_path = query_sql.name

                mysql_cmd = f"""
                    docker run --rm -t -v {query_sql_path}:/query.sql \
                      -e MYSQL_PWD={password} --entrypoint /bin/bash \
                      --add-host host.docker.internal:host-gateway mysql:8.0 \
                      -c 'mysql --host host.docker.internal --port=3306 --user={user} --silent --skip-column-names < query.sql'
                """
                result = subprocess.run(mysql_cmd, shell=True, capture_output=True, text=True, timeout=30)
                assert result.returncode == 0
                return result.stdout.strip()

            # Verify database creation
            db_result = run_mysql_query(f"SHOW DATABASES LIKE '{tower_db_name}';")
            assert db_result == tower_db_name

            # Verify user creation
            user_result = run_mysql_query(f"SELECT user FROM mysql.user WHERE user='{tower_db_user}';")
            assert user_result == tower_db_user

            # Verify user permissions
            grants_result = run_mysql_query(f"SHOW GRANTS FOR '{tower_db_user}'@'%';")
            assert "ALL PRIVILEGES" in grants_result
            assert f"`{tower_db_name}`" in grants_result

            # Verify connection with new user credentials by running a simple query
            test_result = run_mysql_query(
                "SELECT 1;", user=tower_db_user, password=tower_db_password, database=tower_db_name
            )
            assert test_result == "1"

        finally:
            # Clean up temporary SQL file
            if os.path.exists(temp_sql_path):
                os.unlink(temp_sql_path)



# ----------------------------------- NON-DEFAULT TESTS
@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
def test_custom_config_tower_env(backup_tfvars, config_baseline_settings_custom):  # teardown_tf_state_all):
    """
    Test the target tower.env generated from default test terraform.tfvars and base-override.auto.tfvars,
    PLUS custom overrides.
    """

    # When
    outputs = config_baseline_settings_custom["planned_values"]["outputs"]
    variables = config_baseline_settings_custom["variables"]

    tower_env_file = parse_key_value_file(f"{root}/assets/target/tower_config/tower.env")
    keys = tower_env_file.keys()

    """
    WARNING!!!!!!
      - Plan keys are in Python dictionary form, so JSON "true" becomes True.
            AFFECTS: `outputs` and `variables`
      - tower_env_file values are directly cracked from HCL so they are "true".
    """

# ------------------------------------------------------------------------------------
    # Test sometimes-present conditionals - Data studio
    # ------------------------------------------------------------------------------------
    # All keys locked behind the `flag_enable_data_studio` flag.
    flag_enable_data_studio = variables["flag_enable_data_studio"]["value"]
    flag_studio_enable_path_routing = variables["flag_studio_enable_path_routing"]["value"]
    data_studio_path_routing_url = variables["data_studio_path_routing_url"]["value"]

    # By default, path-routing not enabled so wont use custom connect domain.
    key = "TOWER_DATA_STUDIO_CONNECT_URL"
    value = outputs["tower_connect_server_url"]["value"]
    if flag_enable_data_studio:
        assert tower_env_file[key] == value
        assert tower_env_file[key] != data_studio_path_routing_url
    else:
        assert key not in keys

    key = "TOWER_DATA_STUDIO_ENABLE_PATH_ROUTING"
    if flag_enable_data_studio:
        if flag_studio_enable_path_routing:
            assert tower_env_file[key] == "true"
        else:
            assert tower_env_file[key] == "false"


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
def test_custom_config_data_studios_env(backup_tfvars, config_baseline_settings_custom):
    """
    Test the target data-studio.env generated from default test terraform.tfvars and base-override.auto.tfvars,
    PLUS custom overrides.
    """

    # When
    outputs = config_baseline_settings_custom["planned_values"]["outputs"]
    variables = config_baseline_settings_custom["variables"]

    ds_env_file = parse_key_value_file(f"{root}/assets/target/tower_config/data-studios.env")
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
    data_studio_path_routing_url = variables["data_studio_path_routing_url"]["value"]

    key = "CONNECT_PROXY_URL"
    value = outputs["tower_connect_server_url"]["value"]
    assert ds_env_file[key] == value
    assert data_studio_path_routing_url in ds_env_file[key]


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
def test_custom_config_docker_compose_with_reverse_proxy(backup_tfvars, config_baseline_settings_custom_docker_compose_reverse_proxy):
    """
    Test the target docker-compose.yml generated from default test terraform.tfvars and base-override.auto.tfvars,
    PLUS custom overrides.
    """

    # When
    outputs = config_baseline_settings_custom_docker_compose_reverse_proxy["planned_values"]["outputs"]
    variables = config_baseline_settings_custom_docker_compose_reverse_proxy["variables"]

    dc_file = read_yaml(f"{root}/assets/target/docker_compose/docker-compose.yml")

    """
    WARNING!!!!!!
      - Plan keys are in Python dictionary form, so JSON "true" becomes True.
            AFFECTS: `outputs` and `variables`
      - tower_env_file values are directly cracked from HCL so they are "true".
    """

    # ------------------------------------------------------------------------------------
    # Test data-studios.env - assert all core keys exist
    # ------------------------------------------------------------------------------------
    assert "reverseproxy" in dc_file["services"].keys()


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
def test_custom_config_docker_compose_with_no_https(backup_tfvars, config_baseline_settings_custom_docker_compose_no_https):
    """
    Test the target docker-compose.yml generated from default test terraform.tfvars and base-override.auto.tfvars,
    PLUS custom overrides.
    """

    # When
    outputs = config_baseline_settings_custom_docker_compose_no_https["planned_values"]["outputs"]
    variables = config_baseline_settings_custom_docker_compose_no_https["variables"]

    dc_file = read_yaml(f"{root}/assets/target/docker_compose/docker-compose.yml")

    """
    WARNING!!!!!!
      - Plan keys are in Python dictionary form, so JSON "true" becomes True.
            AFFECTS: `outputs` and `variables`
      - tower_env_file values are directly cracked from HCL so they are "true".
    """

    # ------------------------------------------------------------------------------------
    # Test data-studios.env - assert all core keys exist
    # ------------------------------------------------------------------------------------
    assert "reverseproxy" not in dc_file["services"].keys()
