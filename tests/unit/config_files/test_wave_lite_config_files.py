import pytest
import subprocess
import json

from tests.utils.local import root, test_tfvars_target, test_tfvars_override_target, test_case_override_target
from tests.utils.local import prepare_plan, run_terraform_apply, execute_subprocess
from tests.utils.local import parse_key_value_file, read_file, read_yaml, read_json
from tests.utils.local import get_reconciled_tfvars

from tests.utils.local import ssm_tower, ssm_groundswell, ssm_seqerakit, ssm_wave_lite

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
