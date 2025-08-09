import pytest

from tests.utils.local import prepare_plan


## ------------------------------------------------------------------------------------
## Wave Service DNS & URL Tests
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.urls
@pytest.mark.wave
def test_wave_url_wave_lite_enabled(session_setup):
    """Test Wave URL when Wave-Lite is enabled."""
    # Given
    override_data = """
        flag_use_wave                                   = false
        flag_use_wave_lite                              = true

        wave_server_url                                 = "autowave.example.com"
    """

    # When
    plan = prepare_plan(override_data)
    outputs = plan["planned_values"]["outputs"]

    tower_wave_dns             = outputs["tower_wave_dns"]["value"]
    tower_wave_url             = outputs["tower_wave_url"]["value"]

    # Then
    assert "autowave.example.com" == tower_wave_dns
    assert "https://autowave.example.com" == tower_wave_url


@pytest.mark.local
@pytest.mark.urls
@pytest.mark.wave
def test_wave_url_wave_lite_disabled(session_setup):
    """Test Wave URL when Wave-Lite is disabled."""
    # Given
    override_data = """
        flag_use_wave                                   = true
        flag_use_wave_lite                              = false

        wave_server_url                                 = "wave.seqera.io"
    """

    # When
    plan = prepare_plan(override_data)
    outputs = plan["planned_values"]["outputs"]

    tower_wave_dns             = outputs["tower_wave_dns"]["value"]
    tower_wave_url             = outputs["tower_wave_url"]["value"]
    wave_lite_db_dns           = outputs["wave_lite_db_dns"]["value"]
    wave_lite_db_url           = outputs["wave_lite_db_url"]["value"]
    wave_lite_redis_dns        = outputs["wave_lite_redis_dns"]["value"]
    wave_lite_redis_url        = outputs["wave_lite_redis_url"]["value"]

    # Then
    assert "wave.seqera.io" == tower_wave_dns
    assert "https://wave.seqera.io" == tower_wave_url
    assert "wave-db" == wave_lite_db_dns
    assert "jdbc:postgresql://wave-db:5432/wave" == wave_lite_db_url
    assert "wave-redis" == wave_lite_redis_dns
    assert "redis://wave-redis:6379" ==  wave_lite_redis_url


@pytest.mark.local
@pytest.mark.urls
@pytest.mark.wave
def test_wave_nothing_enabled(session_setup):
    """Test Wave URL when Wave & Wave-Lite disabled."""
    # Given
    override_data = """
        flag_use_wave                                   = false
        flag_use_wave_lite                              = false

        wave_server_url                                 = "wave.seqera.io"
    """

    # When
    plan = prepare_plan(override_data)
    outputs = plan["planned_values"]["outputs"]

    tower_wave_dns             = outputs["tower_wave_dns"]["value"]
    tower_wave_url             = outputs["tower_wave_url"]["value"]
    wave_lite_db_dns           = outputs["wave_lite_db_dns"]["value"]
    wave_lite_db_url           = outputs["wave_lite_db_url"]["value"]
    wave_lite_redis_dns        = outputs["wave_lite_redis_dns"]["value"]
    wave_lite_redis_url        = outputs["wave_lite_redis_url"]["value"]

    assert "N/A" == tower_wave_dns
    assert "N/A" == tower_wave_url
    assert "N/A" == wave_lite_db_dns
    assert "N/A" == wave_lite_db_url
    assert "N/A" == wave_lite_redis_dns
    assert "N/A" ==  wave_lite_redis_url


    
