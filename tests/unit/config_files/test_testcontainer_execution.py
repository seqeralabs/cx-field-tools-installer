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

from tests.datafiles.expected_results import generate_baseline_entries_all_active, generate_baseline_entries_all_disabled

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
## MARK: Testcontainer: MySQL
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.db
@pytest.mark.mysql_container
@pytest.mark.long
@pytest.mark.testcontainer
def test_tower_sql_mysql_container_execution(session_setup):
    """
    Test that tower.sql successfully populates a MySQL8 database using Testcontainers.
    This validates the SQL file can create the database, user, and grant permissions.

    NOTE:
    Container DB cant be connected to via master creds like standard RDS.
    Emulate by creating one user "test", then run the script that we'd normally run against RDS with the master user.
    Then try to log in with the "tower" user.

    Cant use `mysql_container.get_container_host_ip()` because it returns `localhost` and we need the host's actual IP.
    """

    # return ([vars, outputs, vars_dict, outputs_dict], 
    #         [tower_secrets_sn, groundswell_secrets_sn, seqerakit_secrets_sn, wave_lite_secrets_sn])

    # Given
    override_data = """
        # No override values needed. Using base template and base-overrides only.
    """
    # Plan with ALL resources rather than targeted, to get all outputs in plan document.
    plan = prepare_plan(override_data)
    plan, secrets = generate_namespaced_dictionaries(plan)
    vars, outputs, vars_dict, _ = plan
    tower_secrets, groundswell_secrets, seqerakit_secrets, wave_lite_secrets = secrets
    namespaces = [vars, outputs, tower_secrets, groundswell_secrets, seqerakit_secrets, wave_lite_secrets]

    # Create hash of tfvars files (used by function 'generate_interpolated_templatefile' to speed up operations).
    content_to_hash = f"{vars}\n{outputs}\n{tower_secrets}\n{groundswell_secrets}\n{seqerakit_secrets}\n{wave_lite_secrets}"
    hash = hashlib.sha256(content_to_hash.encode("utf-8")).hexdigest()[:16]

    needed_template_files = {k: v for k,v in all_template_files.items() if k in ["tower_sql"]}
    test_template_files = generate_interpolated_templatefiles(hash, namespaces, needed_template_files)

    sql_content = test_template_files["tower_sql"]["content"]


    # ssm_data = read_json(ssm_tower)
    # sql_content = read_file(f"{root}/assets/target/tower_config/tower.sql")

    # Note: Hack to emulate RDS master user / password.
    # TODO: Use the master user / password from the SSM values. WARNING: DONT CHANGE THESE OR TEST FAILS.
    mock_master_user = "root"
    mock_master_password = "test"
    mock_db_name = "test"

    # User & Password pulled from 'tower_secrets'
    tower_db_user = "tower_test_user"
    tower_db_password = "tower_test_password"
    tower_db_name = "tower"

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
