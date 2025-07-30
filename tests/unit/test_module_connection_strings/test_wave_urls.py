import pytest

from tests.utils.local import prepare_plan


## ------------------------------------------------------------------------------------
## Wave Service DNS & URL Tests
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.urls
@pytest.mark.wave
def test_wave_url_wave_lite_enabled(backup_tfvars):
    """Test Wave URL when Wave-Lite is enabled."""
    # Given
    override_data = """
        flag_use_wave                                   = false
        flag_use_wave_lite                              = true
        wave_server_url                                 = "wave-lite.example.com"
    """

    # When
    plan = prepare_plan(override_data)
    outputs = plan["planned_values"]["outputs"]

    wave_url = outputs["tower_wave_url"]["value"]
    wave_dns = outputs["tower_wave_dns"]["value"]

    # Then
    assert "wave-lite.example.com" == wave_dns
    assert "https://" not in wave_dns

    # Should use Wave-Lite URL when flag_use_wave_lite = true
    assert "https://wave-lite.example.com" == wave_url
    assert f"https://{wave_dns}" == wave_url


@pytest.mark.local
@pytest.mark.urls
@pytest.mark.wave
def test_wave_url_wave_lite_disabled(backup_tfvars):
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

    wave_url = outputs["tower_wave_url"]["value"]
    wave_dns = outputs["tower_wave_dns"]["value"]

    # Then
    assert "wave.seqera.io" == wave_dns
    assert "https://" not in wave_dns

    # Should use regular Wave URL when flag_use_wave_lite = false
    assert "https://wave.seqera.io" == wave_url


@pytest.mark.local
@pytest.mark.urls
@pytest.mark.wave
def test_wave_nothing_enabled(backup_tfvars):
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

    wave_url = outputs["tower_wave_url"]["value"]
    wave_dns = outputs["tower_wave_dns"]["value"]

    # Then
    assert "N/A" == wave_dns
    assert "https://" not in wave_dns

    # Should be "N/A" when neither Wave nor Wave-Lite is enabled.
    assert "N/A" == wave_url


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
