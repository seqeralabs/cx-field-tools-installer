import pytest

from tests.utils.local import prepare_plan


# TODO: July 30/25 - enhance db tests to include connection string too.

## ------------------------------------------------------------------------------------
## New RDS
## ------------------------------------------------------------------------------------
# NOTE: Mock DNS values here are hardcoded into the modules/connection_strings/v1.0.0/main.tf file.
@pytest.mark.local
@pytest.mark.db
@pytest.mark.db_new
def test_external_new_db_url_full_ecoystem(session_setup):
    """Test URLs targeting a new RDS instance."""
    # Given
    override_data = """
        flag_create_external_db             = true
        flag_use_existing_external_db       = false
        flag_use_container_db               = false

        flag_enable_groundswell             = true
        flag_use_wave_lite                  = true
    """

    # When
    plan = prepare_plan(override_data)
    outputs = plan["planned_values"]["outputs"]

    tower_db_dns     = outputs["tower_db_dns"]["value"]
    tower_db_url     = outputs["tower_db_url"]["value"]
    swell_db_dns     = outputs["swell_db_dns"]["value"]
    swell_db_url     = outputs["swell_db_url"]["value"]
    wave_lite_db_dns = outputs["wave_lite_db_dns"]["value"]
    wave_lite_db_url = outputs["wave_lite_db_url"]["value"]

    # Then
    assert "mock.tower-db.com" == tower_db_dns
    assert "jdbc:mysql://mock.tower-db.com:3306/tower" in tower_db_url
    assert "mock.tower-db.com" == swell_db_dns
    assert "mysql://mock.tower-db.com:3306/swell" == swell_db_url
    assert swell_db_url != tower_db_url
    assert "mock.wave-db.com" == wave_lite_db_dns
    assert "jdbc:postgresql://mock.wave-db.com:5432/wave" == wave_lite_db_url
    assert wave_lite_db_url != tower_db_url


@pytest.mark.local
@pytest.mark.db
@pytest.mark.db_new
def test_external_new_db_url_no_ecoystem(session_setup):
    """Test URLs targeting a new RDS instance."""
    # Given
    override_data = """
        flag_create_external_db             = true
        flag_use_existing_external_db       = false
        flag_use_container_db               = false

        flag_enable_groundswell             = false
        flag_use_wave_lite                  = false
    """

    # When
    plan = prepare_plan(override_data)
    outputs = plan["planned_values"]["outputs"]

    tower_db_dns     = outputs["tower_db_dns"]["value"]
    tower_db_url     = outputs["tower_db_url"]["value"]
    swell_db_dns     = outputs["swell_db_dns"]["value"]
    swell_db_url     = outputs["swell_db_url"]["value"]
    wave_lite_db_dns = outputs["wave_lite_db_dns"]["value"]
    wave_lite_db_url = outputs["wave_lite_db_url"]["value"]

    # Then
    assert "mock.tower-db.com" == tower_db_dns
    assert "jdbc:mysql://mock.tower-db.com:3306/tower" in tower_db_url
    assert "N/A"== swell_db_dns
    assert "N/A" == swell_db_url
    assert swell_db_url != tower_db_url
    assert "N/A" == wave_lite_db_dns
    assert "N/A" == wave_lite_db_url
    assert wave_lite_db_url != tower_db_url


## ------------------------------------------------------------------------------------
## Existing RDS
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.db
@pytest.mark.db_existing
def test_external_existing_db_url_all_ecosystem(session_setup):
    """Test URLs targeting an existing RDS instance."""
    # Given
    override_data = """
        flag_create_external_db         = false
        flag_use_existing_external_db   = true
        flag_use_container_db           = false

        flag_enable_groundswell         = true
        flag_use_wave_lite              = true

        tower_db_url                    = "existing.tower-db.com"
    """

    # When
    plan = prepare_plan(override_data)
    outputs = plan["planned_values"]["outputs"]

    tower_db_dns     = outputs["tower_db_dns"]["value"]
    tower_db_url     = outputs["tower_db_url"]["value"]
    swell_db_dns     = outputs["swell_db_dns"]["value"]
    swell_db_url     = outputs["swell_db_url"]["value"]
    wave_lite_db_dns = outputs["wave_lite_db_dns"]["value"]
    wave_lite_db_url = outputs["wave_lite_db_url"]["value"]

    # Then
    assert "existing.tower-db.com" == tower_db_dns
    assert "jdbc:mysql://existing.tower-db.com:3306/tower" in tower_db_url
    assert "existing.tower-db.com" == swell_db_dns
    assert "mysql://existing.tower-db.com:3306/swell"== swell_db_url
    assert swell_db_url != tower_db_url
    # July 29/25 -- Wave-Lite feature does not currently support existing. If not creating new remote, uses local db.
    assert "wave-db" == wave_lite_db_dns
    assert "jdbc:postgresql://wave-db:5432/wave" == wave_lite_db_url
    assert wave_lite_db_url != tower_db_url


@pytest.mark.local
@pytest.mark.db
@pytest.mark.db_existing
def test_external_existing_db_url_no_ecosystem(session_setup):
    """Test URLs targeting an existing RDS instance."""
    # Given
    override_data = """
        flag_create_external_db         = false
        flag_use_existing_external_db   = true
        flag_use_container_db           = false

        flag_enable_groundswell         = false
        flag_use_wave_lite              = false

        tower_db_url                    = "existing.tower-db.com"
    """

    # When
    plan = prepare_plan(override_data)
    outputs = plan["planned_values"]["outputs"]

    tower_db_dns     = outputs["tower_db_dns"]["value"]
    tower_db_url     = outputs["tower_db_url"]["value"]
    swell_db_dns     = outputs["swell_db_dns"]["value"]
    swell_db_url     = outputs["swell_db_url"]["value"]
    wave_lite_db_dns = outputs["wave_lite_db_dns"]["value"]
    wave_lite_db_url = outputs["wave_lite_db_url"]["value"]

    # Then
    assert "existing.tower-db.com" == tower_db_dns
    assert "jdbc:mysql://existing.tower-db.com:3306/tower" in tower_db_url
    assert "N/A" == swell_db_dns
    assert "N/A" == swell_db_url
    assert swell_db_url != tower_db_url
    # July 29/25 -- Wave-Lite feature does not currently support existing. If not new, uses local.
    assert "N/A" == wave_lite_db_dns
    assert "N/A" == wave_lite_db_url
    assert wave_lite_db_url != tower_db_url
