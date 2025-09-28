import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request           #TODO: Assess if this is right or should use urllib3?
import urllib.error             #TODO: Assess if this is right or should use urllib3?

import pytest
from testcontainers.compose import DockerCompose
from testcontainers.mysql import MySqlContainer
from testcontainers.postgres import PostgresContainer

from tests.datafiles.expected_results.expected_results import assertion_modifiers_template
from tests.utils.config import root
from tests.utils.filehandling import read_yaml
from tests.utils.local import prepare_plan, generate_tc_files


## ------------------------------------------------------------------------------------
## MARK: MySQL (Platform)
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.testcontainer
def test_tower_sql_population(session_setup):
    """
    Test that tower.sql successfully populates a MySQL8 database as expected (via Testcontainer). 
    Emulates execution of RDS prepping script in Ansible.

    NOTE:
    Container DB cant be connected to via master creds like standard RDS.
    Emulate by creating one user "test", then run the script that we'd normally run against RDS with the master user.
    Then try to log in with the "tower" user.

    Cant use `mysql_container.get_container_host_ip()` because it returns `localhost` and we need the host's actual IP.
    """

    ## SETUP
    ## =======================================================================================
    tf_modifiers = """#NONE"""
    plan = prepare_plan(tf_modifiers)

    desired_files       = ["tower_sql"]
    tc_files = generate_tc_files(plan, desired_files, sys._getframe().f_code.co_name)

    # Not required right now
    # assertion_modifiers = assertion_modifiers_template()
    # tc_assertions = generate_assertions_all_active(tc_files, assertion_modifiers)
    # verify_all_assertions(tc_files, tc_assertions)

    # WARNING: DONT CHANGE THESE OR TEST FAILS.
    # https://hub.docker.com/_/mysql
    master_user             = "root"
    master_password         = "test"
    master_db_name          = "test"

    # User & Password set in 'tower_secrets'.
    tower_db_user           = "tower_test_user"
    tower_db_password       = "tower_test_password"
    tower_db_name           = "tower"


    def run_mysql_query(query, user=None, password=None, database=None):
        """
        Helper function to run MySQL queries using container commands
        -  Write desired SQL command to temporary file.
        -  Volume mounts temporary file into a runner MySQL8 container (for access to CLI).
        -  Establishes connection to testcontainer MySQL and runs command.
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as query_sql:
            query_sql.write(query)
            query_sql_path = query_sql.name

        mysql_cmd = f"""
            docker run --rm -t \
                -v {query_sql_path}:/query.sql \
                -e MYSQL_PWD={password} \
                --entrypoint /bin/bash \
                --add-host host.docker.internal:host-gateway \
                mysql:8.0 \
                -c 'mysql --host host.docker.internal --port=3306 --user={user} --silent --skip-column-names < query.sql'
        """
        result = subprocess.run(mysql_cmd, shell=True, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0
        return result.stdout.strip()


    with (
        MySqlContainer("mysql:8.0", root_password=master_password)
        .with_env("MYSQL_USER", master_user)
        .with_env("MYSQL_PASSWORD", master_password)
        .with_env("MYSQL_DATABASE", master_db_name)
        .with_bind_ports(3306, 3306)
    ) as mysql_container:


        # POPULATE
        # Run initial population script.
        query = tc_files["tower_sql"]["content"]
        db_result = run_mysql_query(query, master_user, master_password)


        # VERIFY
        # Verify database creation.
        query = f"SHOW DATABASES LIKE '{tower_db_name}';"
        db_result = run_mysql_query(query, master_user, master_password)
        assert db_result == tower_db_name

        # Verify user creation
        query = f"SELECT user FROM mysql.user WHERE user='{tower_db_user}';"
        user_result = run_mysql_query(query, master_user, master_password)
        assert user_result == tower_db_user

        # Verify user permissions
        query = f"SHOW GRANTS FOR '{tower_db_user}'@'%';"
        grants_result = run_mysql_query(query, master_user, master_password)
        assert "ALL PRIVILEGES" in grants_result
        assert f"`{tower_db_name}`" in grants_result

        # Verify connection with new user credentials by running a simple query
        query = "SELECT 1"
        test_result = run_mysql_query(query, tower_db_user, tower_db_password, tower_db_name)
        assert test_result == "1"


## ------------------------------------------------------------------------------------
## MARK: Postgres (Wave)
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.testcontainer
def test_wave_sql_rds_population(session_setup, config_baseline_settings_default):
    """
    Test that wave-lite-rds.sql successfully populates a Postgres database as expected (via Testcontainer). 
    Emulates execution of RDS prepping script in Ansible.

    NOTE:
    Container DB cant be connected to via master creds like standard RDS.
    Emulate by creating one user "test", then run the script that we'd normally run against RDS with the master user.
    Then try to log in with the "tower" user.

    Cant use `mysql_container.get_container_host_ip()` because it returns `localhost` and we need the host's actual IP.
    """

    ## SETUP
    ## =======================================================================================
    tf_modifiers = """#NONE"""
    plan = prepare_plan(tf_modifiers)

    desired_files       = ["docker_compose", "wave_lite_yml", "wave_lite_rds"]
    tc_files = generate_tc_files(plan, desired_files, sys._getframe().f_code.co_name)

    # Not required right now
    # assertion_modifiers = assertion_modifiers_template()
    # tc_assertions = generate_assertions_all_active(tc_files, assertion_modifiers)
    # verify_all_assertions(tc_files, tc_assertions)

    # https://hub.docker.com/_/postgres
    master_user             = "wave_lite_test_master"
    master_password         = "wave_lite_test_master_password"
    master_db_name          = "test"

    # User & Password set in wave_lite secrets.
    wave_db_user           = "wave_lite_test_limited"
    wave_db_password       = "wave_lite_test_limited_password"
    wave_db_name           = "wave"


    def run_postgres_query(query, user=wave_db_user, password=wave_db_password, database="wave"):
        """Helper function to run psql queries using container commands"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as query_sql:
            query_sql.write(query)
            query_sql_path = query_sql.name

        # -t — Tuples only (removes headers and footers)
        # -A — Unaligned output (removes column formatting, outputs plain text)
        postgres_cmd = f"""
            docker run --rm -t \
                -v {query_sql_path}:/query.sql \
                -e PGPASSWORD={password} \
                --entrypoint /bin/bash \
                --add-host host.docker.internal:host-gateway \
                postgres:17.6 \
                -c 'PGPASSWORD={password} psql --host host.docker.internal --port=5432 --user={user} -d {database} -t -A < query.sql'
        """
        result = subprocess.run(postgres_cmd, shell=True, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0
        return result.stdout.strip()


    # Reference connection string.
    # `PGPASSWORD=abc123 psql --host localhost --port 5432 --user root -d wave`

    ## ==================================================================================
    ## SCENARIO 1: Execute RDS SQL against posttgres via other postgres container
    ## ==================================================================================
    with (
        PostgresContainer("postgres:17.6", username=master_user, password=master_password, dbname=master_db_name)
        .with_env("GRAHAM", "graham")
        .with_bind_ports(5432, 5432)
    ) as postgres_container:

        # POPULATE
        # Run initial population script.
        query = tc_files["wave_lite_rds"]["content"]
        db_result = run_postgres_query(query, master_user, master_password, master_db_name)

        # VERIFY
        # Test master user connection to wave database
        query = "SELECT current_database();"
        master_conn_test = run_postgres_query(query, master_user, master_password, master_db_name)
        assert master_conn_test == "test"

        # Test Wave user connection to wave database
        query = "SELECT current_database();"
        limited_conn_test = run_postgres_query(query, wave_db_user, wave_db_password, wave_db_name)
        assert limited_conn_test == "wave"

        # Verify Wave user has expected permissions
        query = "SELECT has_database_privilege(current_user, 'wave', 'CREATE');"
        permissions_test = run_postgres_query(query, wave_db_user, wave_db_password, wave_db_name)
        assert "t" in permissions_test  # 't' means true in PostgreSQL

        # Test Wave user can create tables (verifying ALL privileges)
        query = "CREATE TABLE test_table (id INT); DROP TABLE test_table;"
        create_table_test = run_postgres_query(query, wave_db_user, wave_db_password, wave_db_name)
        assert "DROP TABLE" in create_table_test


    ## ==================================================================================
    ## SCENARIO3: Volume Mount RDS file to run on container init
    ## ==================================================================================
    init_sql_rds_path = tc_files["wave_lite_rds"]["filepath"]

    with (
        # PostgresContainer("postgres:17.6", username="postgres", password="postgres", dbname="wave")
        PostgresContainer("postgres:17.6", username=master_user, password=master_password, dbname=master_db_name)
        .with_env("GRAHAM", "graham")
        .with_bind_ports(5432, 5432)
        .with_volume_mapping(init_sql_rds_path, "/docker-entrypoint-initdb.d/01-init.sql")
    ) as postgres_container3:

        # POPULATE
        # No need to run explicit population step since volume mounting should hanlde for us on initial boot.

        # VERIFY
        # Test master user connection to wave database
        query = "SELECT current_database();"
        # master_conn_test = run_postgres_query(query, master_user, master_password, master_db_name)
        master_conn_test = run_postgres_query(query, master_user, master_password, master_db_name)  #"wave")
        assert master_conn_test == "test"

        # Test Wave user connection to wave database
        query = "SELECT current_database();"
        limited_conn_test = run_postgres_query(query, wave_db_user, wave_db_password, wave_db_name)
        assert limited_conn_test == "wave"

        # Verify Wave user has expected permissions
        query = "SELECT has_database_privilege(current_user, 'wave', 'CREATE');"
        permissions_test = run_postgres_query(query, wave_db_user, wave_db_password, wave_db_name)
        assert "t" in permissions_test  # 't' means true in PostgreSQL

        # Test Wave user can create tables (verifying ALL privileges)
        query = "CREATE TABLE test_table (id INT); DROP TABLE test_table;"
        create_table_test = run_postgres_query(query, wave_db_user, wave_db_password, wave_db_name)
        assert "DROP TABLE" in create_table_test


## ------------------------------------------------------------------------------------
## MARK: Compose (Wave)
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.testcontainer
def test_wave_containers(session_setup):
    """
    Ensure the entire Wave containerized ecosystem can run.

    How it works:
        1. Read in content of generated docker-compose file.
        2. Purge any key in ["services"] if it's not in ["wave-lite", "wave-lite-reverse-proxy", "wave-db", "wave-redis"]
        3. Purge ['wave-lite']['volumes'] and replace with path to test-generated YAML.
        4. Purge ['wave-lite-reverse-proxy']['volumes'] and replace with path to target. TODO: FIX THIS.
        5. Purge ['wave-db]['volumes'] and replace with path to test-generated SQL.
        6. Purge ['wave-redis']['volumes'].
    """

    ## SETUP
    ## =======================================================================================
    tf_modifiers = """#NONE"""
    plan = prepare_plan(tf_modifiers)

    desired_files       = ["docker_compose", "wave_lite_yml", "wave_lite_rds"]
    tc_files = generate_tc_files(plan, desired_files, sys._getframe().f_code.co_name)

    # Not required right now
    # assertion_modifiers = assertion_modifiers_template()
    # tc_assertions = generate_assertions_all_active(tc_files, assertion_modifiers)
    # verify_all_assertions(tc_files, tc_assertions)


    def prepare_wave_only_docker_compose():
        docker_compose_data = read_yaml(tc_files["docker_compose"]["filepath"])

        # Purge all containers except those tied to Wave Lite.
        desired_services = ["wave-lite", "wave-lite-reverse-proxy", "wave-db", "wave-redis"]
        all_services = list(docker_compose_data["services"].keys())
        services_to_purge = [k for k in all_services if k not in desired_services]

        for k in services_to_purge:
            docker_compose_data["services"].pop(k)

        # Add generated Wave Lite YAML file
        wave_lite_yaml_path = tc_files["wave_lite_yml"]["filepath"]
        volume_mount = f"{wave_lite_yaml_path}:/work/config.yml"
        docker_compose_data["services"]["wave-lite"]["volumes"] = []
        docker_compose_data["services"]["wave-lite"]["volumes"].append(volume_mount)

        # TODO: Add NGINX CONFIG WHEN GENERATED AT AS TEMPLATEFILE
        volume_mount = f"{root}/assets/target/wave_lite_config/nginx.conf:/etc/nginx/nginx.conf:ro"
        docker_compose_data["services"]["wave-lite-reverse-proxy"]["volumes"] = []
        docker_compose_data["services"]["wave-lite-reverse-proxy"]["volumes"].append(volume_mount)

        # Add SQL & remove stateful storage from wave lite db
        wave_lite_rds_path = tc_files["wave_lite_rds"]["filepath"]
        volume_mount = f"{wave_lite_rds_path}:/docker-entrypoint-initdb.d/01-init.sql"
        docker_compose_data["services"]["wave-db"]["volumes"] = []
        docker_compose_data["services"]["wave-db"]["volumes"].append(volume_mount)

        # Remove stateful storage from wave lite redis.
        docker_compose_data["services"]["wave-redis"]["volumes"] = []

        return docker_compose_data

    # Generate the Wave-Lite-only content
    wave_content = prepare_wave_only_docker_compose()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as wave_docker_compose:
        wave_docker_compose.write(str(wave_content))
        wave_docker_compose_path = wave_docker_compose.name

    folder_path = os.path.dirname(wave_docker_compose_path)
    filename = os.path.basename(wave_docker_compose_path)

    # Start docker-compose deployment and run tests
    with DockerCompose(context=folder_path, compose_file_name=filename, pull=True) as compose:

        # Test wave-lite service-info endpoint
        service_url = "http://localhost:9099/service-info"
        max_retries = 10
        delay = 3

        for attempt in range(max_retries):
            try:
                with urllib.request.urlopen(service_url, timeout=10) as response:
                    assert response.status == 200, f"Expected HTTP 200, got {response.status}"
                    response_data = json.loads(response.read().decode("utf-8"))

                print(f"{response_data=}")
                assert "serviceInfo" in response_data
                service_info = response_data["serviceInfo"]
                assert "version" in service_info
                assert "commitId" in service_info

            except (urllib.error.URLError, json.JSONDecodeError, AssertionError) as e:
                if attempt == max_retries:
                    pytest.fail(
                        f"Failed to connect to wave-lite service at {service_url} after {max_retries} retries: {e}"
                    )
                time.sleep(delay)

        # TODO: Add other tests
        # 1. Test allow_instance_credentials=true
