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

from testcontainers.mysql import MySqlContainer

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
## MARK: Testcontainer: MySQL
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.db
@pytest.mark.mysql_container
@pytest.mark.long
@pytest.mark.testcontainer
def test_tower_sql_mysql_container_execution(session_setup):
    """
    Test that tower.sql successfully populates a MySQL8 database as expected (via Testcontainer). 
    Emulates execution of RDS prepping script in Ansilble.

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


    def run_mysql_query(query, user=master_user, password=master_password, database=None):
        """
        Helper function to run MySQL queries using container commands
        -  Write desired SQL command to temporary file.
        -  Volume mounts temporary file into a runner MySQL8 container (for access to CLI).
        -  Establishes connection to testcontainer MySQL and runs command.
        """

        # Create temporary SQL file for docker volume mount (avoids nested quotes nightmare)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as query_sql:
            query_sql.write(query)
            query_sql_path = query_sql.name

        mysql_cmd = f"""
            docker run --rm -t \
                -v {query_sql_path}:/query.sql \
                -e MYSQL_PWD={password} \
                --entrypoint /bin/bash \
                --add-host host.docker.internal:host-gateway mysql:8.0 \
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
