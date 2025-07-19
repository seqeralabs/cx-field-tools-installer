import pytest
import subprocess
import json
import tempfile
import os
import time
import yaml
import urllib.request
import urllib.error

from tests.utils.local import root, test_tfvars_target, test_tfvars_override_target, test_case_override_target
from tests.utils.local import prepare_plan, run_terraform_apply, execute_subprocess
from tests.utils.local import parse_key_value_file, read_file, read_yaml, read_json
from tests.utils.local import get_reconciled_tfvars

from tests.utils.local import ssm_tower, ssm_groundswell, ssm_seqerakit, ssm_wave_lite

from testcontainers.compose import DockerCompose
from testcontainers.postgres import PostgresContainer

from tests.utils.docker_compose import prepare_wave_only_docker_compose
from tests.utils.local import test_docker_compose_file

## ------------------------------------------------------------------------------------
## Wave Lite Config File Checks
## ------------------------------------------------------------------------------------
# NOTE: To avoid creating VPC assets, use an existing VPC in the account the AWS provider is configured to use.


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
def test_default_config_wave_lite_container_1_sql(backup_tfvars, config_baseline_settings_default):
    """
    Test the target wave-lite-container-1.sql generated from default test terraform.tfvars and base-override.auto.tfvars.
    """

    # Given
    tfvars = get_reconciled_tfvars()

    # Get values for comparison
    ssm_data = read_json(ssm_wave_lite)
    sql_content = read_file(f"{root}/assets/target/wave_lite_config/wave-lite-container-1.sql")

    # Get expected values
    expected_user = ssm_data["WAVE_LITE_DB_LIMITED_USER"]["value"]
    expected_password = ssm_data["WAVE_LITE_DB_LIMITED_PASSWORD"]["value"]

    # ------------------------------------------------------------------------------------
    # Test wave-lite-container-1.sql - validate all interpolated variables are properly replaced
    # ------------------------------------------------------------------------------------

    # Verify PostgreSQL user creation with conditional logic
    assert f"WHERE rolname = '{expected_user}'" in sql_content
    assert f"CREATE ROLE {expected_user} LOGIN PASSWORD '{expected_password}'" in sql_content

    # Verify database creation
    assert "CREATE DATABASE wave" in sql_content
    assert "WHERE datname = 'wave'" in sql_content

    # Ensure no placeholder values remain
    assert "replace_me_wave_lite_db_limited_user" not in sql_content
    assert "replace_me_wave_lite_db_limited_password" not in sql_content


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
def test_default_config_wave_lite_container_2_sql(backup_tfvars, config_baseline_settings_default):
    """
    Test the target wave-lite-container-2.sql generated from default test terraform.tfvars and base-override.auto.tfvars.
    """

    # Given
    tfvars = get_reconciled_tfvars()

    # Get values for comparison
    ssm_data = read_json(ssm_wave_lite)
    sql_content = read_file(f"{root}/assets/target/wave_lite_config/wave-lite-container-2.sql")

    # Get expected values
    expected_user = ssm_data["WAVE_LITE_DB_LIMITED_USER"]["value"]

    # ------------------------------------------------------------------------------------
    # Test wave-lite-container-2.sql - validate all interpolated variables are properly replaced
    # ------------------------------------------------------------------------------------

    # Verify GRANT statements contain correct username
    assert f"GRANT ALL PRIVILEGES ON DATABASE wave TO {expected_user}" in sql_content
    assert f"GRANT ALL ON SCHEMA public TO {expected_user}" in sql_content
    assert f"GRANT ALL ON ALL TABLES IN SCHEMA public TO {expected_user}" in sql_content
    assert f"GRANT ALL ON ALL PRIVILEGES IN SCHEMA public TO {expected_user}" in sql_content

    # Verify database connection command
    assert "\\c wave" in sql_content

    # Ensure no placeholder values remain
    assert "replace_me_wave_lite_db_limited_user" not in sql_content
    assert "replace_me_wave_lite_db_limited_password" not in sql_content


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
def test_default_config_wave_lite_rds_sql(backup_tfvars, config_baseline_settings_default):
    """
    Test the target wave-lite-rds.sql generated from default test terraform.tfvars and base-override.auto.tfvars.
    """

    # Given
    tfvars = get_reconciled_tfvars()

    # Get values for comparison
    ssm_data = read_json(ssm_wave_lite)
    sql_content = read_file(f"{root}/assets/target/wave_lite_config/wave-lite-rds.sql")

    # Get expected values
    expected_user = ssm_data["WAVE_LITE_DB_LIMITED_USER"]["value"]
    expected_password = ssm_data["WAVE_LITE_DB_LIMITED_PASSWORD"]["value"]

    # ------------------------------------------------------------------------------------
    # Test wave-lite-rds.sql - validate all interpolated variables are properly replaced
    # ------------------------------------------------------------------------------------

    # Verify RDS-specific user creation with \gexec syntax
    assert f"CREATE ROLE {expected_user} LOGIN PASSWORD ''{expected_password}''" in sql_content
    assert f"WHERE rolname = '{expected_user}'" in sql_content
    assert "\\gexec" in sql_content

    # Verify database creation with \gexec syntax
    assert "CREATE DATABASE wave" in sql_content
    assert "WHERE datname = 'wave'" in sql_content

    # Verify permissions and privileges
    assert f"GRANT ALL PRIVILEGES ON DATABASE wave TO {expected_user}" in sql_content
    assert f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {expected_user}" in sql_content
    assert f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {expected_user}" in sql_content
    assert f"GRANT USAGE, CREATE ON SCHEMA public TO {expected_user}" in sql_content
    assert f"GRANT ALL PRIVILEGES ON TABLES TO {expected_user}" in sql_content

    # Verify database connection command
    assert "\\c wave" in sql_content

    # Ensure no placeholder values remain
    assert "replace_me_wave_lite_db_limited_user" not in sql_content
    assert "replace_me_wave_lite_db_limited_password" not in sql_content


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
def test_default_config_wave_lite_yml(backup_tfvars, config_baseline_settings_default):
    """
    Test the target wave-lite.yml generated from default test terraform.tfvars and base-override.auto.tfvars.
    Tests only interpolated variables, not static configuration values.
    """

    # Given
    tfvars = get_reconciled_tfvars()

    # When
    outputs = config_baseline_settings_default["planned_values"]["outputs"]
    variables = config_baseline_settings_default["variables"]

    wave_lite_yml_file = read_yaml(f"{root}/assets/target/wave_lite_config/wave-lite.yml")
    ssm_data = read_json(ssm_wave_lite)

    # ------------------------------------------------------------------------------------
    # Test interpolated variables only
    # ------------------------------------------------------------------------------------
    # Wave server URL
    assert wave_lite_yml_file["wave"]["server"]["url"] == outputs["tower_wave_url"]["value"]

    # Database configuration
    expected_db_uri = f"jdbc:postgresql://{outputs['wave_lite_db_url']['value']}/wave"
    assert wave_lite_yml_file["wave"]["db"]["uri"] == expected_db_uri
    assert wave_lite_yml_file["wave"]["db"]["user"] == ssm_data["WAVE_LITE_DB_LIMITED_USER"]["value"]
    assert wave_lite_yml_file["wave"]["db"]["password"] == ssm_data["WAVE_LITE_DB_LIMITED_PASSWORD"]["value"]

    # Redis configuration
    assert wave_lite_yml_file["redis"]["uri"] == outputs["wave_lite_redis_url"]["value"]
    assert wave_lite_yml_file["redis"]["password"] == ssm_data["WAVE_LITE_REDIS_AUTH"]["value"]

    # Mail configuration
    assert wave_lite_yml_file["mail"]["from"] == variables["tower_contact_email"]["value"]

    # Tower endpoint
    expected_tower_endpoint = f"{outputs['tower_server_url']['value']}/api"
    assert wave_lite_yml_file["tower"]["endpoint"]["url"] == expected_tower_endpoint


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
def test_wave_lite_sql_files_with_postgres_container(backup_tfvars, config_baseline_settings_default):
    """
    Test that the wave_lite_config SQL files successfully populate a PostgreSQL container.
    Uses testcontainers to spin up a local PostgreSQL instance with the same configuration
    as the wave-db service in docker-compose.yml.tpl.
    """

    # Get values from SSM test data
    ssm_data = read_json(ssm_wave_lite)
    master_user = ssm_data["WAVE_LITE_DB_MASTER_USER"]["value"]
    master_password = ssm_data["WAVE_LITE_DB_MASTER_PASSWORD"]["value"]
    limited_user = ssm_data["WAVE_LITE_DB_LIMITED_USER"]["value"]
    limited_password = ssm_data["WAVE_LITE_DB_LIMITED_PASSWORD"]["value"]

    # Read SQL files that will be executed
    sql_container_init_path = f"{root}/assets/target/wave_lite_config/wave-lite-rds.sql"

    # Start PostgreSQL container with same config as docker-compose wave-db service
    with (
        # Reference connection string.
        # `PGPASSWORD=abc123 psql --host localhost --port 5432 --user root -d wave`
        PostgresContainer("postgres:latest", username=master_user, password=master_password, dbname="test")
        .with_env("GRAHAM", "graham")
        .with_bind_ports(5432, 5432)
        .with_volume_mapping(sql_container_init_path, "/docker-entrypoint-initdb.d/01-init.sql")
    ) as postgres_container:

        def run_psql_query(query, user=limited_user, password=limited_password, database="wave"):
            """Helper function to run psql queries using container commands"""

            # Create temporary SQL file for docker volume mount (avoids nested quotes nightmare)
            with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as query_sql:
                query_sql.write(query)
                query_sql_path = query_sql.name

            # -t — Tuples only (removes headers and footers)
            # -A — Unaligned output (removes column formatting, outputs plain text)
            postgres_cmd = f"""
                docker run --rm -t -v {query_sql_path}:/query.sql \
                  -e PGPASSWORD={password} --entrypoint /bin/bash \
                  --add-host host.docker.internal:host-gateway postgres:latest \
                  -c 'PGPASSWORD={password} psql --host host.docker.internal --port=5432 --user={user} -d {database} -t -A < query.sql'
            """
            result = subprocess.run(postgres_cmd, shell=True, capture_output=True, text=True, timeout=30)
            assert result.returncode == 0
            print(f"result: {result.stdout.strip()}")
            return result.stdout.strip()

        # Test master user connection to wave database
        master_conn_test = run_psql_query(
            "SELECT current_database();", user=master_user, password=master_password, database="test"
        )
        assert master_conn_test == "test"

        # Test limited user connection to wave database
        limited_conn_test = run_psql_query("SELECT current_database();")
        assert limited_conn_test == "wave"

        # Verify limited user has expected permissions
        permissions_test = run_psql_query("SELECT has_database_privilege(current_user, 'wave', 'CREATE');")
        assert "t" in permissions_test  # 't' means true in PostgreSQL

        # Test limited user can create tables (verifying ALL privileges)
        create_table_test = run_psql_query("CREATE TABLE test_table (id INT); DROP TABLE test_table;")
        assert "DROP TABLE" in create_table_test


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
def test_wave_lite_compose_deployment(backup_tfvars, config_baseline_settings_default):
    """
    Test Wave containers (x4) in local docker-compose deployment.
    Creates a cut-down version of the full docker-compose.yml file generated for the EC2.
    Compose file is run and we ensure the service-info endpoint (via reverse proxy) is available.
    """

    # Prepare docker-compose file
    prepare_wave_only_docker_compose(root)
    folder_path = os.path.dirname(test_docker_compose_file)
    filename = os.path.basename(test_docker_compose_file)

    # Start docker-compose deployment
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
