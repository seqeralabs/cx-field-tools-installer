import pytest
import subprocess
import json
import os
import tempfile
import time
import hashlib
from pathlib import Path
import sys

from types import SimpleNamespace

from tests.utils.local import root, test_tfvars_target, test_tfvars_override_target, test_case_override_target
from tests.utils.local import prepare_plan, run_terraform_apply, execute_subprocess
from tests.utils.local import parse_key_value_file, read_file, read_yaml, read_json, write_file
from tests.utils.local import get_reconciled_tfvars

from tests.utils.local import ssm_tower, ssm_groundswell, ssm_seqerakit, ssm_wave_lite
from tests.utils.local import templatefile_cache_dir

from tests.utils.local import generate_namespaced_dictionaries, generate_interpolated_templatefiles, all_template_files
from tests.utils.local import testcase_setup
from tests.utils.local import assert_present_and_omitted

from testcontainers.mysql import MySqlContainer


# NOTE: To avoid creating VPC assets, use an existing VPC in the account the AWS provider is configured to use.

## ------------------------------------------------------------------------------------
## Baseline Configuration File Check
## ------------------------------------------------------------------------------------
def test_poc(session_setup):
    """
    Trying to create files directly via Terraform console.
    """

    override_data = """
        # No override values needed. Testing baseline only.
    """
    # Plan with ALL resources rather than targeted, to get all outputs in plan document.
    plan = prepare_plan(override_data)

    needed_template_files = all_template_files
    test_template_files = testcase_setup(plan, needed_template_files)


    # ------------------------------------------------------------------------------------
    # Test tower.env
    # ------------------------------------------------------------------------------------
    print(f"Testing {sys._getframe().f_code.co_name}.tower.env generated from default settings.")
    tower_env_file = test_template_files["tower_env"]["content"]

    entries = {
        "present": {
            "TOWER_ENABLE_AWS_SSM"        : "true",
            "LICENSE_SERVER_URL"          : "https://licenses.seqera.io",
            "TOWER_SERVER_URL"            : "https://autodc.dev-seqera.net",
            "TOWER_CONTACT_EMAIL"         : "graham.wright@seqera.io",
            "TOWER_ENABLE_PLATFORMS"      : "awsbatch-platform,slurm-platform",
            "TOWER_ROOT_USERS"            : "graham.wright@seqera.io,gwright99@hotmail.com",
            "TOWER_DB_URL"                : "jdbc:mysql://db:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true",
            "TOWER_DB_DRIVER"             : "org.mariadb.jdbc.Driver",
            "TOWER_DB_DIALECT"            : "io.seqera.util.MySQL55DialectCollateBin",
            "TOWER_DB_MIN_POOL_SIZE"      : 5,
            "TOWER_DB_MAX_POOL_SIZE"      : 10,
            "TOWER_DB_MAX_LIFETIME"       : 18000000,
            "FLYWAY_LOCATIONS"            : "classpath:db-schema/mysql",
            "TOWER_REDIS_URL"             : "redis://redis:6379",
            "TOWER_ENABLE_UNSAFE_MODE"    : "false",
            "WAVE_SERVER_URL"             : "https://wave.stage-seqera.io",
            "TOWER_ENABLE_WAVE"           : "true",
            # OIDC                                          : N/A
            "TOWER_DATA_STUDIO_ENABLE_PATH_ROUTING"         : "false",
            "TOWER_DATA_STUDIO_CONNECT_URL"                 : "https://connect.autodc.dev-seqera.net",
            "TOWER_OIDC_PEM_PATH"                           : "/data-studios-rsa.pem",
            "TOWER_OIDC_REGISTRATION_INITIAL_ACCESS_TOKEN"  : "ipsemlorem"
        },
        "omitted": {}
    }
    assert_present_and_omitted(entries, tower_env_file)


    # ------------------------------------------------------------------------------------
    # Test tower.env - assert some core keys NOT present ever
    # ------------------------------------------------------------------------------------
    entries = {
        "present": {},
        "omitted": {
            "TOWER_DB_USER"         : "",
            "TOWER_DB_PASSWORD"     : "", 
            "TOWER_SMTP_USER"       : "",
            "TOWER_SMTP_PASSWORD"   : "",
        }
    }
    assert_present_and_omitted(entries, tower_env_file)


    # ------------------------------------------------------------------------------------
    # Test tower.env - assert sometimes-present conditionals:
    # ------------------------------------------------------------------------------------
    entries = {
        "present" : {
            "TOWER_ENABLE_AWS_SES"  : "true",
        },
        "omitted": {
            "TOWER_SMTP_HOST"       : "",
            "TOWER_SMTP_PORT"       : "",
            # "TOWER_SMTP_PORT"     : N/A DO NOT UNCOMMENT,
            # "TOWER_SMTP_PORT"     : N/A DO NOT UNCOMMENT,
        }
    }
    assert_present_and_omitted(entries, tower_env_file)


    entries = {
        "present": {
            "TOWER_ENABLE_GROUNDSWELL"  : "true",
            "GROUNDSWELL_SERVER_URL"    : "http://groundswell:8090",
        },
        "omitted": {}
    }
    assert_present_and_omitted(entries, tower_env_file)


    entries = {
        "present": {
            "TOWER_DATA_EXPLORER_ENABLED"                   : "true",
            "TOWER_DATA_EXPLORER_CLOUD_DISABLED_WORKSPACES" : "",
        },
        "omitted": {}
    }
    assert_present_and_omitted(entries, tower_env_file)


    entries = {
        "present": {
            "TOWER_DATA_STUDIO_ENABLE_PATH_ROUTING"         : "false",
            "TOWER_DATA_STUDIO_CONNECT_URL"                 : "https://connect.autodc.dev-seqera.net",
            "TOWER_OIDC_PEM_PATH"                           : "/data-studios-rsa.pem",
            "TOWER_OIDC_REGISTRATION_INITIAL_ACCESS_TOKEN"  : "ipsemlorem",

            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-0_ICON"          : "jupyter",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-0_REPOSITORY"    : "public.cr.seqera.io/platform/data-studio-jupyter:4.2.5-0.8.0",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-0_TOOL"          : "jupyter",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-0_STATUS"        : "deprecated",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-5_ICON"          : "jupyter",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-5_REPOSITORY"    : "public.cr.seqera.io/platform/data-studio-jupyter:4.2.5-0.8.5",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-5_TOOL"          : "jupyter",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-5_STATUS"        : "recommended",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-8-5_ICON"         : "rstudio",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-8-5_REPOSITORY"   : "public.cr.seqera.io/platform/data-studio-ride:2025.04.1-0.8.5",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-8-5_TOOL"         : "rstudio",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-8-5_STATUS"       : "recommended",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-8-5_ICON"         : "vscode",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-8-5_REPOSITORY"   : "public.cr.seqera.io/platform/data-studio-vscode:1.101.2-0.8.5",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-8-5_TOOL"         : "vscode",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-8-5_STATUS"       : "recommended",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-83-0-0-8-0_ICON"          : "vscode",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-83-0-0-8-0_REPOSITORY"    : "public.cr.seqera.io/platform/data-studio-vscode:1.83.0-0.8.0",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-83-0-0-8-0_TOOL"          : "vscode",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-83-0-0-8-0_STATUS"        : "deprecated",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R0-0-8-0_ICON"            : "xpra",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R0-0-8-0_REPOSITORY"      : "public.cr.seqera.io/platform/data-studio-xpra:6.0-r0-1-0.8.0",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R0-0-8-0_TOOL"            : "xpra",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R0-0-8-0_STATUS"          : "recommended",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R2-1-0-8-5_ICON"          : "xpra",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R2-1-0-8-5_REPOSITORY"    : "public.cr.seqera.io/platform/data-studio-xpra:6.2.0-r2-1-0.8.5",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R2-1-0-8-5_TOOL"          : "xpra",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R2-1-0-8-5_STATUS"        : "recommended",
        },
        "omitted": {
            "TOWER_DATA_STUDIO_ALLOWED_WORKSPACES"          : ""
        }
    }
    assert_present_and_omitted(entries, tower_env_file, type="kv")


    # ------------------------------------------------------------------------------------
    # Test tower.yml
    # ------------------------------------------------------------------------------------
    print(f"Testing {sys._getframe().f_code.co_name}.tower.yml generated from default settings.")
    tower_yml_file = test_template_files["tower_yml"]["content"]

    # Reminder: YAML files converted to python dictionary so use True / False for comparison
    entries = {
        "present": {
            tower_yml_file["mail"]["smtp"]["auth"]                                  : True,
            tower_yml_file["mail"]["smtp"]["starttls"]["enable"]                    : True,
            tower_yml_file["mail"]["smtp"]["starttls"]["required"]                  : True,
            tower_yml_file["mail"]["smtp"]["ssl"]["protocols"]                      : "TLSv1.2",
            tower_yml_file["micronaut"]["application"]["name"]                      : "tower-testing",
            tower_yml_file["tower"]["cron"]["audit-log"]["clean-up"]["time-offset"] : "1095d",
            tower_yml_file["tower"]["data-studio"]["allowed-workspaces"]            : None,
            tower_yml_file["tower"]["trustedEmails"][0]                             : "'graham.wright@seqera.io,gwright99@hotmail.com'",
            tower_yml_file["tower"]["trustedEmails"][1]                             : "'*@abc.com,*@def.com'",
            tower_yml_file["tower"]["trustedEmails"][2]                             : "'123@abc.com,456@def.com'",
        },
        "omitted": {
            "auth"          : tower_yml_file["tower"].keys(),
            # "data-studio"   : tower_yml_file["tower"].keys(),
        }
    }
    assert_present_and_omitted(entries, tower_yml_file, "yaml")


    # ------------------------------------------------------------------------------------
    # Test data_studios.env
    # ------------------------------------------------------------------------------------
    print(f"Testing {sys._getframe().f_code.co_name}.data-studio.env generated from default settings.")
    ds_env_file = test_template_files["data_studios_env"]["content"]

    entries = {
        "present": {
            "PLATFORM_URL"                              : f"https://autodc.dev-seqera.net",
            "CONNECT_HTTP_PORT"                         : 9090,    # str()
            "CONNECT_TUNNEL_URL"                        : "connect-server:7070",
            "CONNECT_PROXY_URL"                         : f"https://connect.autodc.dev-seqera.net",
            "CONNECT_REDIS_ADDRESS"                     : "redis:6379",
            "CONNECT_REDIS_DB"                          : 1,
            "CONNECT_OIDC_CLIENT_REGISTRATION_TOKEN"    : "ipsemlorem"
        },
        "omitted": {}
    }
    assert_present_and_omitted(entries, ds_env_file, type="kv")


    # ------------------------------------------------------------------------------------
    # Test tower.sql - validate all interpolated variables are properly replaced
    # ------------------------------------------------------------------------------------
    print(f"Testing {sys._getframe().f_code.co_name}.tower.sql generated from default settings.")
    tower_sql_file = test_template_files["tower_sql"]["content"]

    # I know it's a bit dumb to have kv pairs here since we only care about keys buuut ... it helps consistency.
    entries = {
        "present": {
            f"""CREATE DATABASE tower;"""                                               : "n/a",
            f"""ALTER DATABASE tower CHARACTER SET utf8 COLLATE utf8_bin;"""            : "n/a",
            f"""CREATE USER "tower_test_user" IDENTIFIED BY "tower_test_password";"""   : "n/a",
            f"""GRANT ALL PRIVILEGES ON tower.* TO tower_test_user@"%";"""              : "n/a"
        },
        "omitted": {}
    }
    assert_present_and_omitted(entries, tower_sql_file, "sql")


## ------------------------------------------------------------------------------------
## Custom Check - Studios Path-Based Routing Enabled
## ------------------------------------------------------------------------------------
def test_poc_custom(session_setup):
    """
    Trying to create files directly via Terraform console.
    """

    override_data = """
        flag_enable_data_studio         = true
        flag_studio_enable_path_routing = true
        data_studio_path_routing_url    = "connect-example.com"
    """
    # Plan with ALL resources rather than targeted, to get all outputs in plan document.
    plan = prepare_plan(override_data)

    target_keys = ["tower_env", "data_studios_env"]
    needed_template_files = {k: v for k,v in all_template_files.items() if k in target_keys}
    test_template_files = testcase_setup(plan, needed_template_files)


    # ------------------------------------------------------------------------------------
    # Test tower.env
    # ------------------------------------------------------------------------------------
    print(f"Testing {sys._getframe().f_code.co_name}.tower.env generated from default settings.")
    tower_env_file = test_template_files["tower_env"]["content"]

    entries = {
        "present": {
            "TOWER_DATA_STUDIO_ENABLE_PATH_ROUTING"         : "true",
            "TOWER_DATA_STUDIO_CONNECT_URL"                 : "https://connect-example.com",
            # NO NEED TO TEST ANY OTHER STUDIOS CONFIG SINCE THESE DONT CHANGE.
        },
        "omitted": {}
    }
    assert_present_and_omitted(entries, tower_env_file, type="kv")


    # ------------------------------------------------------------------------------------
    # Test data_studios.env
    # ------------------------------------------------------------------------------------
    print(f"Testing {sys._getframe().f_code.co_name}.data_studios.env generated from default settings.")
    ds_env_file = test_template_files["data_studios_env"]["content"]

    entries = {
        "present": {
            "CONNECT_PROXY_URL"                             : "https://connect-example.com",
            # NO NEED TO TEST ANY OTHER STUDIOS CONFIG SINCE THESE DONT CHANGE.
        },
        "omitted": {}
    }
    assert_present_and_omitted(entries, ds_env_file, type="kv")





# ------------------------------------------------------------------------------------
# CUSTOM CONFIG TESTS
# ------------------------------------------------------------------------------------



@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
def test_custom_config_files_02(session_setup, config_baseline_settings_custom_02):
    """
    Test the target tower.env generated from default test terraform.tfvars and base-override.auto.tfvars,
    PLUS custom overrides.

    - Data Studios active & Path routing inactive
    """

    # When
    tower_env_file = parse_key_value_file(f"{root}/assets/target/tower_config/tower.env")
    ds_env_file = parse_key_value_file(f"{root}/assets/target/tower_config/data-studios.env")


    # ------------------------------------------------------------------------------------
    # Test conditionals - Tower Env File And Data Studios Env file
    # ------------------------------------------------------------------------------------
    assert tower_env_file["TOWER_DATA_STUDIO_ENABLE_PATH_ROUTING"]  == "false"
    assert tower_env_file["TOWER_DATA_STUDIO_CONNECT_URL"]          == "https://connect.autodc.dev-seqera.net"
    assert ds_env_file["CONNECT_PROXY_URL"]                         == "https://connect.autodc.dev-seqera.net"


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
def test_custom_config_files_03(session_setup, config_baseline_settings_custom_03):
    """
    Test the target tower.env generated from default test terraform.tfvars and base-override.auto.tfvars,
    PLUS custom overrides.

    - Data Studios inactive & Path routing inactive
    """

    # When
    tower_env_file = parse_key_value_file(f"{root}/assets/target/tower_config/tower.env")
    tower_env_file_keys = tower_env_file.keys()

    ds_env_file = parse_key_value_file(f"{root}/assets/target/tower_config/data-studios.env")
    ds_env_file_keys = ds_env_file.keys()


    # ------------------------------------------------------------------------------------
    # Test conditionals - Tower Env File And Data Studios Env file
    # ------------------------------------------------------------------------------------
    assert "TOWER_DATA_STUDIO_ENABLE_PATH_ROUTING" not in tower_env_file_keys
    assert "TOWER_DATA_STUDIO_CONNECT_URL" not in tower_env_file_keys

    assert "CONNECT_PROXY_URL" in ds_env_file_keys


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
def test_custom_config_docker_compose_with_reverse_proxy(session_setup, config_baseline_settings_custom_docker_compose_reverse_proxy):
    """
    Test the target docker-compose.yml generated from default test terraform.tfvars and base-override.auto.tfvars,
    PLUS custom overrides.
    """

    # When
    # n/a

    dc_file = read_yaml(f"{root}/assets/target/docker_compose/docker-compose.yml")

    # ------------------------------------------------------------------------------------
    # Test data-studios.env - assert all core keys exist
    # ------------------------------------------------------------------------------------
    assert "reverseproxy" in dc_file["services"].keys()


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
def test_custom_config_docker_compose_with_no_https(session_setup, config_baseline_settings_custom_docker_compose_no_https):
    """
    Test the target docker-compose.yml generated from default test terraform.tfvars and base-override.auto.tfvars,
    PLUS custom overrides.
    """

    # When
    # n/a

    dc_file = read_yaml(f"{root}/assets/target/docker_compose/docker-compose.yml")

    # ------------------------------------------------------------------------------------
    # Test data-studios.env - assert all core keys exist
    # ------------------------------------------------------------------------------------
    assert "reverseproxy" not in dc_file["services"].keys()






@pytest.mark.local
@pytest.mark.db
@pytest.mark.mysql_container
@pytest.mark.long
@pytest.mark.testcontainer
def test_tower_sql_mysql_container_execution(session_setup, config_baseline_settings_default):
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
    vars, _, _, _ = generate_namespaced_dictionaries(config_baseline_settings_default)
    ssm_data = read_json(ssm_tower)
    sql_content = read_file(f"{root}/assets/target/tower_config/tower.sql")

    # Note: Hack to emulate RDS master user / password.
    # TODO: Use the master user / password from the SSM values. WARNING: DONT CHANGE THESE OR TEST FAILS.
    mock_master_user = "root"
    mock_master_password = "test"
    mock_db_name = "test"

    tower_db_user = ssm_data["TOWER_DB_USER"]["value"]
    tower_db_password = ssm_data["TOWER_DB_PASSWORD"]["value"]
    tower_db_name = vars.db_database_name

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
