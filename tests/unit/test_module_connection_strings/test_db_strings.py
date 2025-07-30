import pytest

from tests.utils.local import prepare_plan


## ------------------------------------------------------------------------------------
## New RDS
## ------------------------------------------------------------------------------------
# NOTE: Mock DNS values here are hardcoded into the modules/connection_strings/v1.0.0/main.tf file.
@pytest.mark.local
@pytest.mark.db
@pytest.mark.db_new
def test_external_new_db_url_full_ecoystem(backup_tfvars):
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

    tower_db_root    = outputs["tower_db_root"]["value"]
    tower_db_url     = outputs["tower_db_url"]["value"]
    swell_db_url     = outputs["swell_db_url"]["value"]
    wave_lite_db_dns = outputs["wave_lite_db_dns"]["value"]
    wave_lite_db_url = outputs["wave_lite_db_url"]["value"]

    # Then
    assert "mock.towerdb.com" == tower_db_root
    assert "mock.towerdb.com" in tower_db_url
    assert "mock.towerdb.com" in swell_db_url
    assert "mock.wave-db.com" == wave_lite_db_dns
    assert "jdbc:postgresql://mock.wave-db.com/wave" == wave_lite_db_url
    assert wave_lite_db_url != tower_db_url


@pytest.mark.local
@pytest.mark.db
@pytest.mark.db_new
def test_external_new_db_url_no_ecoystem(backup_tfvars):
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

    tower_db_root    = outputs["tower_db_root"]["value"]
    tower_db_url     = outputs["tower_db_url"]["value"]
    swell_db_url     = outputs["swell_db_url"]["value"]
    wave_lite_db_dns = outputs["wave_lite_db_dns"]["value"]
    wave_lite_db_url = outputs["wave_lite_db_url"]["value"]

    # Then
    # TODO: FIX GROUNDSWELL entry
    assert "mock.towerdb.com" == tower_db_root
    assert "mock.towerdb.com" in tower_db_url
    assert "mock.towerdb.com" in swell_db_url
    assert "N/A" == wave_lite_db_dns
    assert "N/A" == wave_lite_db_url


## ------------------------------------------------------------------------------------
## Existing RDS
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.db
@pytest.mark.db_existing
def test_external_existing_db_url_all_ecosystem(backup_tfvars):
    """Test URLs targeting an existing RDS instance."""
    # Given
    override_data = """
        flag_create_external_db         = false
        flag_use_existing_external_db   = true
        flag_use_container_db           = false

        flag_enable_groundswell         = true
        flag_use_wave_lite              = true

        tower_db_url                    = "existing.towerdb.com"
    """

    # When
    plan = prepare_plan(override_data)
    outputs = plan["planned_values"]["outputs"]

    tower_db_root    = outputs["tower_db_root"]["value"]
    tower_db_url     = outputs["tower_db_url"]["value"]
    swell_db_url     = outputs["swell_db_url"]["value"]
    wave_lite_db_dns = outputs["wave_lite_db_dns"]["value"]
    wave_lite_db_url = outputs["wave_lite_db_url"]["value"]

    # Then
    assert "existing.towerdb.com" == tower_db_root
    assert "existing.towerdb.com" in tower_db_url
    assert "existing.towerdb.com" in swell_db_url
    # July 29/25 -- Wave-Lite feature does not currently support existing. If not creating new remote, uses local db.
    assert "wave-db:5432" == wave_lite_db_dns
    assert "jdbc:postgresql://wave-db:5432/wave" == wave_lite_db_url
    assert wave_lite_db_url != tower_db_url


@pytest.mark.local
@pytest.mark.db
@pytest.mark.db_existing
def test_external_existing_db_url_no_ecosystem(backup_tfvars):
    """Test URLs targeting an existing RDS instance."""
    # Given
    override_data = """
        flag_create_external_db         = false
        flag_use_existing_external_db   = true
        flag_use_container_db           = false

        flag_enable_groundswell         = false
        flag_use_wave_lite              = false

        tower_db_url                    = "existing.towerdb.com"
    """

    # When
    plan = prepare_plan(override_data)
    outputs = plan["planned_values"]["outputs"]

    tower_db_root    = outputs["tower_db_root"]["value"]
    tower_db_url     = outputs["tower_db_url"]["value"]
    swell_db_url     = outputs["swell_db_url"]["value"]
    wave_lite_db_dns = outputs["wave_lite_db_dns"]["value"]
    wave_lite_db_url = outputs["wave_lite_db_url"]["value"]

    # Then
    assert "existing.towerdb.com" == tower_db_root
    assert "existing.towerdb.com" in tower_db_url
    assert "existing.towerdb.com" in swell_db_url           # TODO: Fix groundswell
    # July 29/25 -- Wave-Lite feature does not currently support existing. If not new, uses local.
    assert "N/A" == wave_lite_db_dns
    assert "N/A" == wave_lite_db_url
    assert wave_lite_db_url != tower_db_url

## ------------------------------------------------------------------------------------
## Container DB
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.db
@pytest.mark.db_container
@pytest.mark.container
def test_container_db_url_full_ecosystem(backup_tfvars):
    """Test URLs targeting container database mode."""
    # Given
    override_data = """
        flag_create_external_db         = false
        flag_use_existing_external_db   = false
        flag_use_container_db           = true

        flag_enable_groundswell         = true
        flag_use_wave_lite              = true
    """

    # When
    plan = prepare_plan(override_data)
    outputs = plan["planned_values"]["outputs"]

    tower_db_root    = outputs["tower_db_root"]["value"]
    tower_db_url     = outputs["tower_db_url"]["value"]
    swell_db_url     = outputs["swell_db_url"]["value"]
    wave_lite_db_dns = outputs["wave_lite_db_dns"]["value"]
    wave_lite_db_url = outputs["wave_lite_db_url"]["value"]

    # Then
    # Container DB should use the docker service name
    assert "db:3306" == tower_db_root
    assert "db:3306" in tower_db_url
    assert "db:3306" in swell_db_url
    assert "wave-db:5432" == wave_lite_db_dns
    assert "jdbc:postgresql://wave-db:5432/wave" == wave_lite_db_url
    assert wave_lite_db_url != tower_db_url


@pytest.mark.local
@pytest.mark.db
@pytest.mark.db_container
@pytest.mark.container
def test_container_db_url_no_ecosystem(backup_tfvars):
    """Test Wave-Lite database URL with container database."""
    # Given
    override_data = """
        flag_create_external_db         = false
        flag_use_existing_external_db   = false
        flag_use_container_db           = true

        flag_enable_groundswell         = false
        flag_use_wave_lite              = false
    """

    # When
    plan = prepare_plan(override_data)
    outputs = plan["planned_values"]["outputs"]

    tower_db_root    = outputs["tower_db_root"]["value"]
    tower_db_url     = outputs["tower_db_url"]["value"]
    swell_db_url     = outputs["swell_db_url"]["value"]
    wave_lite_db_dns = outputs["wave_lite_db_dns"]["value"]
    wave_lite_db_url = outputs["wave_lite_db_url"]["value"]

    # Then
    # Container DB should use the docker service name
    assert "db:3306" == tower_db_root
    assert "db:3306" in tower_db_url
    assert "db:3306" in swell_db_url
    assert "N/A" == wave_lite_db_dns
    assert "N/A" == wave_lite_db_url
    assert wave_lite_db_url != tower_db_url

