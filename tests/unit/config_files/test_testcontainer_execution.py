import json
import os
import subprocess
import tempfile
import time
import urllib.error  # TODO: Assess if this is right or should use urllib3?
import urllib.request  # TODO: Assess if this is right or should use urllib3?

import pytest
from testcontainers.compose import DockerCompose
from testcontainers.mysql import MySqlContainer
from testcontainers.postgres import PostgresContainer
from tests.utils.config import FP
from tests.utils.filehandling.filehandling import FileHelper


# Container-side client images. Match the images Ansible uses (02_update_file_configurations.yml.tpl).
MYSQL_CLIENT_IMAGE = "mysql:8.4"
POSTGRES_CLIENT_IMAGE = "postgres:17.6"


## ------------------------------------------------------------------------------------
## MARK: Query helpers
## ------------------------------------------------------------------------------------
def run_mysql_query(query, user, password):
    """Run SQL against the testcontainer MySQL via a throwaway client container; return stdout.

    - Writes the SQL to a temporary file.
    - Mounts that file into a MySQL client container (for access to the CLI).
    - Connects to the testcontainer MySQL and runs the file.

    Fails the test if the client exits non-zero. `mysql` stops at the first failing statement.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as query_sql:
        query_sql.write(query)
        query_sql_path = query_sql.name

    mysql_invoke = (
        f"mysql --host host.docker.internal --port=3306 --user={user} --silent --skip-column-names < query.sql"
    )
    # Argument list, no host shell. The `<` redirect runs inside the client container's bash.
    mysql_cmd = [
        "docker", "run", "--rm", "-t",
        "-v", f"{query_sql_path}:/query.sql",
        "-e", f"MYSQL_PWD={password}",
        "--entrypoint", "/bin/bash",
        "--add-host", "host.docker.internal:host-gateway",
        MYSQL_CLIENT_IMAGE,
        "-c", mysql_invoke,
    ]  # fmt: skip
    result = subprocess.run(mysql_cmd, check=False, capture_output=True, text=True, timeout=30)  # noqa: S603  (docker from PATH; args are test fixtures)
    assert result.returncode == 0, f"mysql exited {result.returncode}: {result.stdout} {result.stderr}"
    return result.stdout.strip()


def run_postgres_query(query, user, password, database, stop_on_error=False):
    """Run SQL against the testcontainer Postgres via a throwaway client container; return stdout.

    If `stop_on_error` is true, psql exits non-zero on the first failing statement (`ON_ERROR_STOP=1`).
    Without it, psql keeps going and exits 0. That is how Ansible runs wave-lite-rds.sql.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as query_sql:
        query_sql.write(query)
        query_sql_path = query_sql.name

    on_error = "-v ON_ERROR_STOP=1 " if stop_on_error else ""
    # -t: tuples only (no headers/footers). -A: unaligned output (plain text).
    psql_invoke = (
        f"PGPASSWORD={password} psql {on_error}--host host.docker.internal --port=5432 "
        f"--user={user} -d {database} -t -A < query.sql"
    )
    # Argument list, no host shell. The `<` redirect runs inside the client container's bash.
    postgres_cmd = [
        "docker", "run", "--rm", "-t",
        "-v", f"{query_sql_path}:/query.sql",
        "-e", f"PGPASSWORD={password}",
        "--entrypoint", "/bin/bash",
        "--add-host", "host.docker.internal:host-gateway",
        POSTGRES_CLIENT_IMAGE,
        "-c", psql_invoke,
    ]  # fmt: skip
    result = subprocess.run(postgres_cmd, check=False, capture_output=True, text=True, timeout=30)  # noqa: S603  (docker from PATH; args are test fixtures)
    assert result.returncode == 0, f"psql exited {result.returncode}: {result.stdout} {result.stderr}"
    return result.stdout.strip()


## ------------------------------------------------------------------------------------
## MARK: MySQL (Platform)
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.testcontainer
def test_tower_sql_population(generated_test_files):
    """Test that tower.sql successfully populates a MySQL8 database as expected (via Testcontainer).

    Emulates execution of RDS prepping script in Ansible.

    Note:
    Container DB cant be connected to via master creds like standard RDS.
    Emulate by creating one user "test", then run the script that we'd normally run against RDS with the master user.
    Then try to log in with the "tower" user.

    Cant use `mysql_container.get_container_host_ip()` because it returns `localhost` and we need the host's actual IP.
    """
    # WARNING: DONT CHANGE THESE OR TEST FAILS.
    # https://hub.docker.com/_/mysql
    master_user = "root"
    master_password = "test"  # noqa: S105  (test fixture)
    master_db_name = "test"

    # User & Password set in 'tower_secrets'.
    tower_db_user = "tower_test_user"
    tower_db_password = "tower_test_password"  # noqa: S105  (test fixture)
    tower_db_name = "tower"

    with (
        MySqlContainer("mysql:8.4", root_password=master_password)
        .with_env("MYSQL_USER", master_user)
        .with_env("MYSQL_PASSWORD", master_password)
        .with_env("MYSQL_DATABASE", master_db_name)
        .with_bind_ports(3306, 3306)
    ) as mysql_container:  # noqa: F841  (kept for readability)
        # POPULATE
        # Run initial population script.
        query = generated_test_files["tower_sql"]["content"]
        db_result = run_mysql_query(query, master_user, master_password)

        # VERIFY
        # Verify database creation.
        query = f"SHOW DATABASES LIKE '{tower_db_name}';"
        db_result = run_mysql_query(query, master_user, master_password)
        assert db_result == tower_db_name

        # Verify user creation
        query = f"SELECT user FROM mysql.user WHERE user='{tower_db_user}';"  # noqa: S608  (test fixture; values hardcoded)
        user_result = run_mysql_query(query, master_user, master_password)
        assert user_result == tower_db_user

        # Verify user permissions
        query = f"SHOW GRANTS FOR '{tower_db_user}'@'%';"
        grants_result = run_mysql_query(query, master_user, master_password)
        assert "ALL PRIVILEGES" in grants_result
        assert f"`{tower_db_name}`" in grants_result

        # Verify connection with new user credentials by running a simple query
        query = "SELECT 1"
        test_result = run_mysql_query(query, tower_db_user, tower_db_password)
        assert test_result == "1"


@pytest.mark.local
@pytest.mark.testcontainer
def test_tower_sql_rerun(generated_test_files):
    """tower.sql populates on the first run, and a second run succeeds without changing the result (issue #434).

    Ansible re-runs tower.sql on every `terraform apply`, so the script must be idempotent.
    """
    # WARNING: DONT CHANGE THESE OR TEST FAILS. Same values as `test_tower_sql_population`.
    master_user = "root"
    master_password = "test"  # noqa: S105  (test fixture)
    tower_db_user = "tower_test_user"
    tower_db_password = "tower_test_password"  # noqa: S105  (test fixture)
    query = generated_test_files["tower_sql"]["content"]

    with (
        MySqlContainer("mysql:8.4", root_password=master_password)
        .with_env("MYSQL_USER", master_user)
        .with_env("MYSQL_PASSWORD", master_password)
        .with_env("MYSQL_DATABASE", "test")
        .with_bind_ports(3306, 3306)
    ):
        # FIRST RUN: must populate.
        run_mysql_query(query, master_user, master_password)
        assert run_mysql_query("SHOW DATABASES LIKE 'tower';", master_user, master_password) == "tower"
        assert run_mysql_query("SELECT 1", tower_db_user, tower_db_password) == "1"

        # SECOND RUN: must exit 0 (run_mysql_query asserts it) and leave the same end state.
        run_mysql_query(query, master_user, master_password)
        assert run_mysql_query("SHOW DATABASES LIKE 'tower';", master_user, master_password) == "tower"
        assert run_mysql_query("SELECT 1", tower_db_user, tower_db_password) == "1"


@pytest.mark.local
@pytest.mark.testcontainer
def test_tower_sql_rerun_resets_password(generated_test_files):
    """A re-run of tower.sql resets the Tower DB user's password to the SSM value (issue #434).

    Simulates a password changed directly in the DB. The `ALTER USER` in tower.sql must restore
    the password from the tower secrets, so Tower can connect again.
    """
    # WARNING: DONT CHANGE THESE OR TEST FAILS. Same values as `test_tower_sql_population`.
    master_user = "root"
    master_password = "test"  # noqa: S105  (test fixture)
    tower_db_user = "tower_test_user"
    tower_db_password = "tower_test_password"  # noqa: S105  (test fixture)
    drifted_password = "drifted_password"  # noqa: S105  (test fixture)
    query = generated_test_files["tower_sql"]["content"]

    with (
        MySqlContainer("mysql:8.4", root_password=master_password)
        .with_env("MYSQL_USER", master_user)
        .with_env("MYSQL_PASSWORD", master_password)
        .with_env("MYSQL_DATABASE", "test")
        .with_bind_ports(3306, 3306)
    ):
        # FIRST RUN: the user can log in with the SSM password.
        run_mysql_query(query, master_user, master_password)
        assert run_mysql_query("SELECT 1", tower_db_user, tower_db_password) == "1"

        # DRIFT: change the password directly in the DB. Confirm the drifted password is now the one that works.
        drift = f"ALTER USER '{tower_db_user}'@'%' IDENTIFIED BY '{drifted_password}';"
        run_mysql_query(drift, master_user, master_password)
        assert run_mysql_query("SELECT 1", tower_db_user, drifted_password) == "1"

        # SECOND RUN: the SSM password must work again.
        run_mysql_query(query, master_user, master_password)
        assert run_mysql_query("SELECT 1", tower_db_user, tower_db_password) == "1"


## ------------------------------------------------------------------------------------
## MARK: MySQL (Groundswell)
## ------------------------------------------------------------------------------------
# groundswell.sql runs against the Platform MySQL server: from 02 for an external DB, and from
# 05 plus the container's first-boot init for the container DB.
#
# No password-reset test here, on purpose: groundswell.sql uses the same `ALTER USER` line as
# tower.sql, which `test_tower_sql_rerun_resets_password` covers. Testcontainers are slow.
SWELL_MASTER_USER = "root"
SWELL_MASTER_PASSWORD = "test"  # noqa: S105  (test fixture)
SWELL_DB_NAME = "swell"
SWELL_DB_USER = "swell_test_user"  # Set in groundswell secrets.
SWELL_DB_PASSWORD = "swell_test_password"  # noqa: S105  (test fixture; set in groundswell secrets)


def assert_swell_db_populated():
    """Assert the swell DB and user exist, the user has ALL PRIVILEGES on it, and the user can connect."""
    query = f"SHOW DATABASES LIKE '{SWELL_DB_NAME}';"
    assert run_mysql_query(query, SWELL_MASTER_USER, SWELL_MASTER_PASSWORD) == SWELL_DB_NAME

    query = f"SELECT user FROM mysql.user WHERE user='{SWELL_DB_USER}';"  # noqa: S608  (test fixture; values hardcoded)
    assert run_mysql_query(query, SWELL_MASTER_USER, SWELL_MASTER_PASSWORD) == SWELL_DB_USER

    query = f"SHOW GRANTS FOR '{SWELL_DB_USER}'@'%';"
    grants_result = run_mysql_query(query, SWELL_MASTER_USER, SWELL_MASTER_PASSWORD)
    assert "ALL PRIVILEGES" in grants_result
    assert f"`{SWELL_DB_NAME}`" in grants_result

    assert run_mysql_query("SELECT 1", SWELL_DB_USER, SWELL_DB_PASSWORD) == "1"


def swell_mysql_container():
    """Return a MySQL testcontainer configured like the Platform container DB."""
    return (
        MySqlContainer("mysql:8.4", root_password=SWELL_MASTER_PASSWORD)
        .with_env("MYSQL_USER", SWELL_MASTER_USER)
        .with_env("MYSQL_PASSWORD", SWELL_MASTER_PASSWORD)
        .with_env("MYSQL_DATABASE", "test")
        .with_bind_ports(3306, 3306)
    )


@pytest.mark.local
@pytest.mark.testcontainer
@pytest.mark.groundswell
def test_groundswell_sql_population(generated_test_files):
    """groundswell.sql creates the swell DB and user, and grants the user ALL PRIVILEGES (via Testcontainer)."""
    query = generated_test_files["groundswell_sql"]["content"]

    with swell_mysql_container():
        run_mysql_query(query, SWELL_MASTER_USER, SWELL_MASTER_PASSWORD)
        assert_swell_db_populated()


@pytest.mark.local
@pytest.mark.testcontainer
@pytest.mark.groundswell
def test_groundswell_sql_rerun(generated_test_files):
    """groundswell.sql populates on the first run, and a second run succeeds without changing the result (issue #434).

    Ansible re-runs groundswell.sql on every `terraform apply` (02 for an external DB, 05 for the container DB).
    """
    query = generated_test_files["groundswell_sql"]["content"]

    with swell_mysql_container():
        # FIRST RUN: must populate.
        run_mysql_query(query, SWELL_MASTER_USER, SWELL_MASTER_PASSWORD)
        assert_swell_db_populated()

        # SECOND RUN: must exit 0 (run_mysql_query asserts it) and leave the same end state.
        run_mysql_query(query, SWELL_MASTER_USER, SWELL_MASTER_PASSWORD)
        assert_swell_db_populated()


## ------------------------------------------------------------------------------------
## MARK: Postgres (Wave)
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.testcontainer
def test_wave_sql_rds_population(generated_test_files):
    """Test that wave-lite-rds.sql successfully populates a Postgres database as expected (via Testcontainer).

    Emulates execution of RDS prepping script in Ansible.

    Note:
    Container DB cant be connected to via master creds like standard RDS.
    Emulate by creating one user "test", then run the script that we'd normally run against RDS with the master user.
    Then try to log in with the "tower" user.

    Cant use `mysql_container.get_container_host_ip()` because it returns `localhost` and we need the host's actual IP.
    """
    # https://hub.docker.com/_/postgres
    master_user = "wave_lite_test_master"
    master_password = "wave_lite_test_master_password"  # noqa: S105  (test fixture)
    master_db_name = "test"

    # User & Password set in wave_lite secrets.
    wave_db_user = "wave_lite_test_limited"
    wave_db_password = "wave_lite_test_limited_password"  # noqa: S105  (test fixture)
    wave_db_name = "wave"

    # Reference connection string.
    # `PGPASSWORD=abc123 psql --host localhost --port 5432 --user root -d wave`

    ## ==================================================================================
    ## SCENARIO 1: Execute RDS SQL against posttgres via other postgres container
    ## ==================================================================================
    with (
        PostgresContainer("postgres:17.6", username=master_user, password=master_password, dbname=master_db_name)
        .with_env("GRAHAM", "graham")
        .with_bind_ports(5432, 5432)
    ) as postgres_container:  # noqa: F841  (kept for readability)
        # POPULATE
        # Run initial population script.
        query = generated_test_files["wave_lite_rds"]["content"]
        run_postgres_query(query, master_user, master_password, master_db_name)

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
    init_sql_rds_path = generated_test_files["wave_lite_rds"]["filepath"]

    with (
        # PostgresContainer("postgres:17.6", username="postgres", password="postgres", dbname="wave")
        PostgresContainer("postgres:17.6", username=master_user, password=master_password, dbname=master_db_name)
        .with_env("GRAHAM", "graham")
        .with_bind_ports(5432, 5432)
        .with_volume_mapping(init_sql_rds_path, "/docker-entrypoint-initdb.d/01-init.sql")
    ) as postgres_container3:  # noqa: F841  (kept for readability)
        # POPULATE
        # No need to run explicit population step since volume mounting should hanlde for us on initial boot.

        # VERIFY
        # Test master user connection to wave database
        query = "SELECT current_database();"
        # master_conn_test = run_postgres_query(query, master_user, master_password, master_db_name)
        master_conn_test = run_postgres_query(query, master_user, master_password, master_db_name)  # "wave")
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


@pytest.mark.local
@pytest.mark.testcontainer
def test_wave_sql_rds_rerun(generated_test_files):
    """wave-lite-rds.sql populates on the first run, and a second run hits no SQL errors (issue #434).

    Uses ON_ERROR_STOP so a failing statement fails the test. Ansible runs psql without it,
    so errors there would pass silently.
    """
    # Same values as `test_wave_sql_rds_population` (set in wave_lite secrets).
    master_user = "wave_lite_test_master"
    master_password = "wave_lite_test_master_password"  # noqa: S105  (test fixture)
    master_db_name = "test"
    wave_db_user = "wave_lite_test_limited"
    wave_db_password = "wave_lite_test_limited_password"  # noqa: S105  (test fixture)
    wave_db_name = "wave"
    query = generated_test_files["wave_lite_rds"]["content"]
    create_check = "SELECT has_database_privilege(current_user, 'wave', 'CREATE');"

    with PostgresContainer(
        POSTGRES_CLIENT_IMAGE, username=master_user, password=master_password, dbname=master_db_name
    ).with_bind_ports(5432, 5432):
        # FIRST RUN: must populate.
        run_postgres_query(query, master_user, master_password, master_db_name, stop_on_error=True)
        assert run_postgres_query("SELECT current_database();", wave_db_user, wave_db_password, wave_db_name) == "wave"
        assert run_postgres_query(create_check, wave_db_user, wave_db_password, wave_db_name) == "t"

        # SECOND RUN: no statement may error, and the end state is unchanged.
        run_postgres_query(query, master_user, master_password, master_db_name, stop_on_error=True)
        assert run_postgres_query("SELECT current_database();", wave_db_user, wave_db_password, wave_db_name) == "wave"
        assert run_postgres_query(create_check, wave_db_user, wave_db_password, wave_db_name) == "t"


## ------------------------------------------------------------------------------------
## MARK: Compose (Wave)
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.testcontainer
def test_wave_containers(generated_test_files):
    """Ensure the entire Wave containerized ecosystem can run.

    How it works:
        1. Read in content of generated docker-compose file.
        2. Purge any key in ["services"] if it's not in
           ["wave-lite", "wave-lite-reverse-proxy", "wave-db", "wave-redis"]
        3. Purge ['wave-lite']['volumes'] and replace with path to test-generated YAML.
        4. Purge ['wave-lite-reverse-proxy']['volumes'] and replace with path to target. TODO: FIX THIS.
        5. Purge ['wave-db]['volumes'] and replace with path to test-generated SQL.
        6. Purge ['wave-redis']['volumes'].
    """

    def prepare_wave_only_docker_compose():
        docker_compose_data = FileHelper.read_yaml(generated_test_files["docker_compose"]["filepath"])

        # Purge all containers except those tied to Wave Lite.
        desired_services = ["wave-lite", "wave-lite-reverse-proxy", "wave-db", "wave-redis"]
        all_services = list(docker_compose_data["services"].keys())
        services_to_purge = [k for k in all_services if k not in desired_services]

        for k in services_to_purge:
            docker_compose_data["services"].pop(k)

        # Add generated Wave Lite YAML file
        wave_lite_yaml_path = generated_test_files["wave_lite_yml"]["filepath"]
        volume_mount = f"{wave_lite_yaml_path}:/work/config.yml"
        docker_compose_data["services"]["wave-lite"]["volumes"] = []
        docker_compose_data["services"]["wave-lite"]["volumes"].append(volume_mount)

        # TODO: Add NGINX CONFIG WHEN GENERATED AT AS TEMPLATEFILE
        volume_mount = f"{FP.ROOT}/assets/target/wave_lite_config/nginx.conf:/etc/nginx/nginx.conf:ro"
        docker_compose_data["services"]["wave-lite-reverse-proxy"]["volumes"] = []
        docker_compose_data["services"]["wave-lite-reverse-proxy"]["volumes"].append(volume_mount)

        # Add SQL & remove stateful storage from wave lite db
        wave_lite_rds_path = generated_test_files["wave_lite_rds"]["filepath"]
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
    # wait=False sends `up --detach`: podman-compose's `up --wait` never returns (podman-compose #1535).
    # Readiness is polled below instead.
    with DockerCompose(context=folder_path, compose_file_name=filename, pull=True, wait=False) as compose:  # noqa: F841  (kept for readability)
        # Test wave-lite service-info endpoint
        service_url = "http://localhost:9099/service-info"
        max_retries = 20  # Give more retries to give time for db & redis to start
        delay = 3

        for attempt in range(max_retries):
            try:
                # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
                with urllib.request.urlopen(service_url, timeout=10) as response:  # noqa: S310  (hardcoded localhost test URL)
                    assert response.status == 200, f"Expected HTTP 200, got {response.status}"
                    response_data = json.loads(response.read().decode("utf-8"))

                print(f"{response_data=}")
                assert "serviceInfo" in response_data
                service_info = response_data["serviceInfo"]
                assert "version" in service_info
                assert "commitId" in service_info
                break

            except (urllib.error.URLError, json.JSONDecodeError, AssertionError) as e:
                if attempt == max_retries - 1:
                    pytest.fail(
                        f"Failed to connect to wave-lite service at {service_url} after {max_retries} retries: {e}"
                    )
                time.sleep(delay)

        # TODO: Add other tests
        # 1. Test allow_instance_credentials=true
