import pytest

from conftest import prepare_plan


## ------------------------------------------------------------------------------------
## New RDS
## ------------------------------------------------------------------------------------
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


# GAP: Wave-Lite with pre-existing database.
