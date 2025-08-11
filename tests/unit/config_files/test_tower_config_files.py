import pytest
import subprocess
import json
import os
import tempfile
import time
import hashlib
from pathlib import Path
import sys
from copy import deepcopy

from types import SimpleNamespace

from tests.utils.local import root, test_tfvars_target, test_tfvars_override_target, test_case_override_target
from tests.utils.local import prepare_plan, run_terraform_apply, execute_subprocess
from tests.utils.local import parse_key_value_file, read_file, read_yaml, read_json, write_file
from tests.utils.local import get_reconciled_tfvars

from tests.utils.local import ssm_tower, ssm_groundswell, ssm_seqerakit, ssm_wave_lite
from tests.utils.local import templatefile_cache_dir

from tests.utils.local import generate_namespaced_dictionaries, generate_interpolated_templatefiles, all_template_files
from tests.utils.local import set_up_testcase
from tests.utils.local import assert_present_and_omitted

from tests.datafiles.expected_results import generate_baseline_all_entries

from testcontainers.mysql import MySqlContainer


# NOTE: To avoid creating VPC assets, use an existing VPC in the account the AWS provider is configured to use.



overrides_template = {
    "tower_env"         : {},
    "tower_yml"         : {},
    "data_studios_env"  : {},
    "tower_sql"         : {},
    "docker_compose"    : {},
}

file_targets_all = {
    "tower_env"         : "kv",
    "tower_yml"         : "yml",
    "data_studios_env"  : "kv",
    "tower_sql"         : "sql",
    "docker_compose"    : "yml",
}
# REFERENCE: How to target a subset of files in each testcase versus full set."""
# target_keys = ["docker_compose"]
# needed_template_files = {k: v for k,v in all_template_files.items() if k in target_keys}
# test_template_files = set_up_testcase(plan, needed_template_files)


## ------------------------------------------------------------------------------------
## MARK: Baseline: All Active
## ------------------------------------------------------------------------------------
def test_baseline_all_enabled(session_setup):
    """
    Baseline check of configuration.
        - All services enabled (Wave Lite, Groundswell, Data Explorer, Studios)
        - Use of machine identity whenever possible (SES).
        - Use of HTTPS
        - Use of container Redis & DB
        - TODO: No OIDC (have not figured out how to configure in public yet -- maybe use pre-generated environment variables?)
    """

    override_data = """
        # No override values needed. Using base template and base-overrides only.
    """
    # Plan with ALL resources rather than targeted, to get all outputs in plan document.
    plan = prepare_plan(override_data)

    needed_template_files = all_template_files
    test_template_files = set_up_testcase(plan, needed_template_files)

    overrides = deepcopy(overrides_template)
    baseline_all_entries = generate_baseline_all_entries(test_template_files, overrides)

    # ------------------------------------------------------------------------------------
    # Test files
    # ------------------------------------------------------------------------------------
    keys = {
        "tower_env"         : "kv",
        "tower_yml"         : "yml",
        "data_studios_env"  : "kv",
        "tower_sql"         : "sql",
        "docker_compose"    : "yml",
    }
    
    for key, type in keys.items():
        print(f"Testing {sys._getframe().f_code.co_name}.{key} generated from default settings.")
        file = test_template_files[key]["content"]
        entries = baseline_all_entries[key]
        assert_present_and_omitted(entries, file, type)


## ------------------------------------------------------------------------------------
## MARK: Baseline: None Active
## ------------------------------------------------------------------------------------
def test_baseline_all_disabled(session_setup):
    """
    Baseline check of configuration.
        - All services disabled (Wave Lite, Groundswell, Data Explorer, Studios)
        - No machine identity (SES).
        - Use of HTTPS
        - Use of container Redis & DB
        - TODO: No OIDC (have not figured out how to configure in public yet -- maybe use pre-generated environment variables?)
    """

    override_data = """
        flag_use_aws_ses_iam_integration    = false
        flag_use_existing_smtp              = true
        flag_enable_groundswell             = false
        flag_data_explorer_enabled          = false
        flag_enable_data_studio             = false
        flag_use_wave                       = false
        flag_use_wave_lite                  = false
    """
    # Plan with ALL resources rather than targeted, to get all outputs in plan document.
    plan = prepare_plan(override_data)

    needed_template_files = all_template_files
    test_template_files = set_up_testcase(plan, needed_template_files)


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
            # OIDC                                          : N/A
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
            "TOWER_ENABLE_AWS_SES"  : "false",
            "TOWER_SMTP_HOST"       : "email-smtp.us-east-1.amazonaws.com",
            "TOWER_SMTP_PORT"       : "587",
        },
        "omitted": {
            ## "TOWER_SMTP_USER"     : N/A DO NOT UNCOMMENT,
            # "TOWER_SMTP_PASSWORD"     : N/A DO NOT UNCOMMENT,
        }
    }
    assert_present_and_omitted(entries, tower_env_file)


    entries = {
        "present": {
            "TOWER_ENABLE_WAVE"           : "false",
            "WAVE_SERVER_URL"             : "N/A",
        },
        "omitted": {}
    }
    assert_present_and_omitted(entries, tower_env_file)


    entries = {
        "present": {
            "TOWER_ENABLE_GROUNDSWELL"  : "false",
        },
        "omitted": {
            "GROUNDSWELL_SERVER_URL"    : "N/A",
        }
    }
    assert_present_and_omitted(entries, tower_env_file)


    entries = {
        "present": {
            "TOWER_DATA_EXPLORER_ENABLED"                   : "false",
        },
        "omitted": {
            "TOWER_DATA_EXPLORER_CLOUD_DISABLED_WORKSPACES" : "",
        }
    }
    assert_present_and_omitted(entries, tower_env_file)


    entries = {
        "present": {
            "# STUDIOS_NOT_ENABLED"                           : "DO_NOT_UNCOMMENT",
        },
        "omitted": {
            "TOWER_DATA_STUDIO_ENABLE_PATH_ROUTING"         : "",
            "TOWER_DATA_STUDIO_CONNECT_URL"                 : "",
            "TOWER_OIDC_PEM_PATH"                           : "",
            "TOWER_OIDC_REGISTRATION_INITIAL_ACCESS_TOKEN"  : "",

            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-0_ICON"          : "",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-0_REPOSITORY"    : "",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-0_TOOL"          : "",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-0_STATUS"        : "",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-5_ICON"          : "",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-5_REPOSITORY"    : "",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-5_TOOL"          : "",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-5_STATUS"        : "",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-8-5_ICON"         : "",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-8-5_REPOSITORY"   : "",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-8-5_TOOL"         : "",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-8-5_STATUS"       : "",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-8-5_ICON"         : "",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-8-5_REPOSITORY"   : "",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-8-5_TOOL"         : "",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-8-5_STATUS"       : "",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-83-0-0-8-0_ICON"          : "",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-83-0-0-8-0_REPOSITORY"    : "",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-83-0-0-8-0_TOOL"          : "",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-83-0-0-8-0_STATUS"        : "",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R0-0-8-0_ICON"            : "",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R0-0-8-0_REPOSITORY"      : "",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R0-0-8-0_TOOL"            : "",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R0-0-8-0_STATUS"          : "",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R2-1-0-8-5_ICON"          : "",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R2-1-0-8-5_REPOSITORY"    : "",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R2-1-0-8-5_TOOL"          : "",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R2-1-0-8-5_STATUS"        : "",
            "# TOWER_DATA_STUDIO_ALLOWED_WORKSPACES"                        : ""
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
            tower_yml_file["tower"]["trustedEmails"][0]                             : "'graham.wright@seqera.io,gwright99@hotmail.com'",
            tower_yml_file["tower"]["trustedEmails"][1]                             : "'*@abc.com,*@def.com'",
            tower_yml_file["tower"]["trustedEmails"][2]                             : "'123@abc.com,456@def.com'",
        },
        "omitted": {
            "auth"          : tower_yml_file["tower"].keys(),
            "data-studio"   : tower_yml_file["tower"].keys(),
        }
    }
    assert_present_and_omitted(entries, tower_yml_file, "yml")


    # ------------------------------------------------------------------------------------
    # Test data_studios.env
    # ------------------------------------------------------------------------------------
    print(f"Testing {sys._getframe().f_code.co_name}.data-studio.env generated from default settings.")
    ds_env_file = test_template_files["data_studios_env"]["content"]

    entries = {
        "present": {
            "# STUDIOS_NOT_ENABLED"                     : "DO_NOT_UNCOMMENT",
        },
        "omitted": {
            "PLATFORM_URL"                              : "",
            "CONNECT_HTTP_PORT"                         : "",
            "CONNECT_TUNNEL_URL"                        : "",
            "CONNECT_PROXY_URL"                         : "",
            "CONNECT_REDIS_ADDRESS"                     : "",
            "CONNECT_REDIS_DB"                          : "",
            "CONNECT_OIDC_CLIENT_REGISTRATION_TOKEN"    : "",
        } 
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


    # ------------------------------------------------------------------------------------
    # Test docker-compose.yml
    # ------------------------------------------------------------------------------------
    print(f"Testing {sys._getframe().f_code.co_name}.docker-compose.yml generated without reverseproxy.")
    docker_compose_file = test_template_files["docker_compose"]["content"]

    entries = {
        "present": {},
        "omitted": {
            "reverseproxy"  : docker_compose_file["services"].keys(),
        }
    }



## ------------------------------------------------------------------------------------
## MARK: Studios: Path Routing
## ------------------------------------------------------------------------------------
def test_studio_path_routing_enabled(session_setup):
    """
    Confirm configurations when Studio active and path-routing enabled.
    Requires Studios to be active so use 'generate_baseline_all_entries'.
    Affects files: 
        - tower.env
        - data_studios.env
    """

    override_data = """
        flag_enable_data_studio         = true
        flag_studio_enable_path_routing = true
        data_studio_path_routing_url    = "connect-example.com"
    """
    # Plan with ALL resources rather than targeted, to get all outputs in plan document.
    plan = prepare_plan(override_data)

    needed_template_files = all_template_files
    test_template_files = set_up_testcase(plan, needed_template_files)

    overrides = deepcopy(overrides_template)
    overrides["tower_env"]= {
        "present": {
            "TOWER_DATA_STUDIO_ENABLE_PATH_ROUTING"     : "true",
            "TOWER_DATA_STUDIO_CONNECT_URL"             : "https://connect-example.com"
        },
        "omitted": {}
    }

    overrides["data_studios_env"]= {
        "present": {
            "CONNECT_PROXY_URL"                         : "https://connect-example.com"
        },
        "omitted": {}
    }

    baseline_all_entries = generate_baseline_all_entries(test_template_files, overrides)

    # ------------------------------------------------------------------------------------
    # Test files
    # ------------------------------------------------------------------------------------
    keys = file_targets_all
    
    for key, type in keys.items():
        print(f"Testing {sys._getframe().f_code.co_name}.{key} generated from default settings.")
        file = test_template_files[key]["content"]
        entries = baseline_all_entries[key]
        assert_present_and_omitted(entries, file, type)


## ------------------------------------------------------------------------------------
## MARK: Private CA: Active
## ------------------------------------------------------------------------------------
def test_private_ca_reverse_proxy_active(session_setup):
    """
    Confirm configurations when Private CA cert must be served by local reverse-proxy.
    Affects files: 
        - docker-compose.yml
    """

    override_data = """
        flag_create_load_balancer        = false
        flag_use_private_cacert          = true
        flag_do_not_use_https            = false
    """
    # Plan with ALL resources rather than targeted, to get all outputs in plan document.
    plan = prepare_plan(override_data)

    needed_template_files = all_template_files
    test_template_files = set_up_testcase(plan, needed_template_files)
    
    # Edgecase! YAML files can't have values overriden same way since we need access to the file, since the test involves
    # running the YAML in the file and comparing against existing result.
    # IDEA: Define overrides as stringified dictionary, pass in to assertion call, extend each file function call with ast.literal_eval? 
    # A    : Nope too hard and errors galore. Just extract the YAML files for setup.
    #        I don't love a YAML-only flow, but it's clean(ish) and mostly mirrors other flow.
    docker_compose_file = test_template_files["docker_compose"]["content"]

    overrides = deepcopy(overrides_template)
    overrides["docker_compose"]= {
        "present": {
            "reverseproxy" : docker_compose_file["services"]["reverseproxy"]["container_name"]
        },
        "omitted": {}
    }
    baseline_all_entries = generate_baseline_all_entries(test_template_files, overrides)

    # ------------------------------------------------------------------------------------
    # Test docker-compose.yml
    # ------------------------------------------------------------------------------------
    keys = file_targets_all

    for key, type in keys.items():
        print(f"Testing {sys._getframe().f_code.co_name}.{key} generated from default settings.")
        file = test_template_files[key]["content"]
        entries = baseline_all_entries[key]
        assert_present_and_omitted(entries, file, type)


## ------------------------------------------------------------------------------------
## MARK: Testcontainer: MySQL
## ------------------------------------------------------------------------------------
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
