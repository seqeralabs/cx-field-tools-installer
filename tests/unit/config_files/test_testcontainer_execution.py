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

from tests.utils.config import root, test_tfvars_target, test_tfvars_override_target, test_case_override_target
from tests.utils.config import ssm_tower, ssm_groundswell, ssm_seqerakit, ssm_wave_lite
from tests.utils.config import templatefile_cache_dir, all_template_files

from tests.utils.local import prepare_plan, run_terraform_apply, execute_subprocess
from tests.utils.local import get_reconciled_tfvars


from tests.utils.local import generate_namespaced_dictionaries, generate_interpolated_templatefiles
from tests.utils.local import set_up_testcase, assert_present_and_omitted

from tests.datafiles.expected_results.expected_results import generate_baseline_entries_all_active, generate_baseline_entries_all_disabled

from testcontainers.compose import DockerCompose
from testcontainers.mysql import MySqlContainer
from testcontainers.postgres import PostgresContainer

from tests.utils.filehandling import read_json, read_yaml, read_file
from tests.utils.filehandling import write_file, move_file, copy_file
from tests.utils.filehandling import parse_key_value_file


# NOTE: To avoid creating VPC assets, use an existing VPC in the account the AWS provider is configured to use.



overrides_template = {
    "tower_env"                 : {},
    "tower_yml"                 : {},
    "data_studios_env"          : {},
    "tower_sql"                 : {},
    "docker_compose"            : {},
    "wave_lite_yml"             : {},
    "wave_lite_container_1"     : {},
    "wave_lite_container_2"     : {},
    "wave_lite_rds"             : {},
}

file_targets_all = {
    "tower_env"                 : "kv",
    "tower_yml"                 : "yml",
    "data_studios_env"          : "kv",
    "tower_sql"                 : "sql",
    "docker_compose"            : "yml",
    "wave_lite_yml"             : "yml",
    "wave_lite_container_1"     : "sql",
    "wave_lite_container_2"     : "sql",
    "wave_lite_rds"             : "sql",
}

# REFERENCE: How to target a subset of files in each testcase versus full set."""
# target_keys = ["docker_compose"]
# needed_template_files = {k: v for k,v in all_template_files.items() if k in target_keys}
# test_template_files = set_up_testcase(plan, needed_template_files)


## ------------------------------------------------------------------------------------
## MARK: MySQL (Platform)
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.sql
@pytest.mark.mysql_container
@pytest.mark.long
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
    override_data = """
        # No override values needed. Using base template and base-overrides only.
    """
    # Plan with ALL resources rather than targeted, to get all outputs in plan document.
    plan = prepare_plan(override_data)
    needed_template_files = all_template_files
    test_template_files = set_up_testcase(plan, needed_template_files, sys._getframe().f_code.co_name)

    overrides = deepcopy(overrides_template)
    baseline_all_entries = generate_baseline_entries_all_active(test_template_files, overrides)

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
        query = test_template_files["tower_sql"]["content"]
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
@pytest.mark.sql
@pytest.mark.vpc_existing
@pytest.mark.long
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
    override_data = """
        # No override values needed. Using base template and base-overrides only.
    """
    # Plan with ALL resources rather than targeted, to get all outputs in plan document.
    plan = prepare_plan(override_data)
    needed_template_files = all_template_files
    test_template_files = set_up_testcase(plan, needed_template_files, sys._getframe().f_code.co_name)

    overrides = deepcopy(overrides_template)
    baseline_all_entries = generate_baseline_entries_all_active(test_template_files, overrides)

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
                postgres:latest \
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
        PostgresContainer("postgres:latest", username=master_user, password=master_password, dbname=master_db_name)
        .with_env("GRAHAM", "graham")
        .with_bind_ports(5432, 5432)
    ) as postgres_container:

        # POPULATE
        # Run initial population script.
        query = test_template_files["wave_lite_rds"]["content"]
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
    ## SCENARIO 2: Volume Mount x2 SQL files to run on container init
    ## TODO: Delete this as part of Issue 239 resolution: https://github.com/seqeralabs/cx-field-tools-installer/issues/239
    ## ==================================================================================
    """
    I can get this to work if I hack.
    The wave-lite-container-1.sql will fail with "CREATE DATABASE cannot be executed from a function" if I try to run it and the starting DB is NOT called "wave" (
        I suspect this is because it already exists as the starting DB and thus the create-if-not-exists wins out). 
    Since I change the core-db I need to change anything else involving the master user too. 
    This is bad since I'm granted the limited user all permissions on the 'wave' DB -- not a big deal if it's not the master table, but big deal if it's not.
    Good news is that this only affects the containerized Wave flow. To remediate I think:
        1. Abandon generation and use of the non-RDS files.
        1. Use RDS file for both the population of the container and RDS instance.

    THis should simplify file generation / testing / and harmonize behaviours between the two.
    """

    init_sql_01_path = test_template_files["wave_lite_container_1"]["filepath"]
    init_sql_02_path = test_template_files["wave_lite_container_2"]["filepath"]

    # Changing dbname to "wave" avoiding the transaction exeuction error in sql-1 due to `CREATE DATABASE cannot be executed from a function`
    with (
        # PostgresContainer("postgres:latest", username="postgres", password="postgres", dbname="wave")
        PostgresContainer("postgres:latest", username=master_user, password=master_password, dbname="wave")
        .with_env("GRAHAM", "graham")
        .with_bind_ports(5432, 5432)
        .with_volume_mapping(init_sql_01_path, "/docker-entrypoint-initdb.d/01-init.sql")
        .with_volume_mapping(init_sql_02_path, "/docker-entrypoint-initdb.d/02-init.sql")
    ) as postgres_container2:

        # POPULATE
        # No need to populate since volume mounting should hanlde for us on initial boot.

        # VERIFY
        # Test master user connection to wave database
        query = "SELECT current_database();"
        # master_conn_test = run_postgres_query(query, master_user, master_password, master_db_name)
        master_conn_test = run_postgres_query(query, master_user, master_password, "wave")
        # assert master_conn_test == "test"
        assert master_conn_test == "wave"

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
    init_sql_rds_path = test_template_files["wave_lite_rds"]["filepath"]

    with (
        # PostgresContainer("postgres:latest", username="postgres", password="postgres", dbname="wave")
        PostgresContainer("postgres:latest", username=master_user, password=master_password, dbname=master_db_name)
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
