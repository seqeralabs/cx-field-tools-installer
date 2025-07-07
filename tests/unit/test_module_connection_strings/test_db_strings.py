import pytest

from tests.utils.local import prepare_plan


## ------------------------------------------------------------------------------------
## New RDS
## ------------------------------------------------------------------------------------
# NOTE: Mock DNS values here are hardcoded into the modules/connection_strings/v1.0.0/main.tf file.
@pytest.mark.local
@pytest.mark.db
@pytest.mark.db_new
def test_external_new_db_url(backup_tfvars):
    """Test URLs targeting a new RDS instance."""
    # Given
    new_db_override_data = """
        flag_create_external_db             = true
        flag_use_existing_external_db       = false
        flag_use_container_db               = false
    """

    # When
    plan = prepare_plan(new_db_override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    assert "mock-new-tower-db.example.com" == outputs["tower_db_root"]["value"]
    assert "mock-new-tower-db.example.com" in outputs["tower_db_url"]["value"]
    assert "mock-new-tower-db.example.com" in outputs["swell_db_url"]["value"]
    assert "mock-new-wave-lite-db.example.com" in outputs["wave_lite_db_url"]["value"]


@pytest.mark.local
@pytest.mark.db
@pytest.mark.db_new
def test_wave_lite_new_db_url(backup_tfvars):
    """Test Wave-Lite database URL with new RDS instance."""
    # Given
    wave_lite_new_db_override_data = """
        flag_create_external_db         = true
        flag_use_existing_external_db   = false
        flag_use_container_db           = false
        flag_use_wave_lite              = true
    """

    # When
    plan = prepare_plan(wave_lite_new_db_override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    # Wave-Lite should use its own dedicated database instance
    assert "mock-new-wave-lite-db.example.com" in outputs["wave_lite_db_url"]["value"]
    # Ensure it's different from Tower's database
    assert outputs["wave_lite_db_url"]["value"] != outputs["tower_db_url"]["value"]


## ------------------------------------------------------------------------------------
## Existing RDS
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.db
@pytest.mark.db_existing
def test_external_existing_db_url(backup_tfvars):
    """Test URLs targeting an existing RDS instance."""
    # Given
    existing_db_override_data = """
        flag_create_external_db         = false
        flag_use_existing_external_db   = true
        flag_use_container_db           = false

        tower_db_url                    = "mock-existing-tower-db.example.com"
    """

    # When
    plan = prepare_plan(existing_db_override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    assert "mock-existing-tower-db.example.com" == outputs["tower_db_root"]["value"]
    assert "mock-existing-tower-db.example.com" in outputs["tower_db_url"]["value"]
    assert "mock-existing-tower-db.example.com" in outputs["swell_db_url"]["value"]


## ------------------------------------------------------------------------------------
## Container DB
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.db
@pytest.mark.db_container
@pytest.mark.container
def test_container_db_url(backup_tfvars):
    """Test URLs targeting container database mode."""
    # Given
    container_db_override_data = """
        flag_create_external_db         = false
        flag_use_existing_external_db   = false
        flag_use_container_db           = true
    """

    # When
    plan = prepare_plan(container_db_override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    # Container DB should use the docker service name
    assert "db:3306" == outputs["tower_db_root"]["value"]
    assert "db:3306" in outputs["tower_db_url"]["value"]
    assert "db:3306" in outputs["swell_db_url"]["value"]


@pytest.mark.local
@pytest.mark.db
@pytest.mark.db_container
@pytest.mark.container
def test_wave_lite_container_db_url(backup_tfvars):
    """Test Wave-Lite database URL with container database."""
    # Given
    wave_lite_container_db_override_data = """
        flag_create_external_db         = false
        flag_use_existing_external_db   = false
        flag_use_container_db           = true
        flag_use_wave_lite              = true
    """

    # When
    plan = prepare_plan(wave_lite_container_db_override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    # Wave-Lite should use container database service name
    assert "wave-db:5432" in outputs["wave_lite_db_url"]["value"]
    # Ensure it's different from Tower's database (different port for PostgreSQL)
    assert outputs["wave_lite_db_url"]["value"] != outputs["tower_db_url"]["value"]


# GAP: Wave-Lite with pre-existing database.
