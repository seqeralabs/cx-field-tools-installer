import pytest

from tests.utils.local import prepare_plan


## ------------------------------------------------------------------------------------
## Wave Service URL Tests
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.urls
@pytest.mark.wave
def test_wave_url_wave_lite_enabled(backup_tfvars):
    """Test Wave URL when Wave-Lite is enabled (should use wave_lite_server_url)."""
    # Given
    override_data = """
        flag_use_wave_lite                              = true
        wave_lite_server_url                            = "https://wave-lite.example.com"
        wave_server_url                                 = "https://wave.seqera.io"
    """

    # When
    plan = prepare_plan(override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    # Should use Wave-Lite URL when flag_use_wave_lite = true
    assert "https://wave-lite.example.com" == outputs["tower_wave_url"]["value"]


@pytest.mark.local
@pytest.mark.urls
@pytest.mark.wave
def test_wave_url_wave_lite_disabled(backup_tfvars):
    """Test Wave URL when Wave-Lite is disabled (should use wave_server_url)."""
    # Given
    override_data = """
        flag_use_wave_lite                              = false
        wave_lite_server_url                            = "https://wave-lite.example.com"
        wave_server_url                                 = "https://wave.seqera.io"
    """

    # When
    plan = prepare_plan(override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    # Should use regular Wave URL when flag_use_wave_lite = false
    assert "https://wave.seqera.io" == outputs["tower_wave_url"]["value"]


## ------------------------------------------------------------------------------------
## Wave DNS Tests (DNS Extraction)
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.urls
@pytest.mark.wave
def test_tower_wave_dns_wave_lite_enabled(backup_tfvars):
    """Test Wave DNS extraction when Wave-Lite is enabled."""
    # Given
    override_data = """
        flag_use_wave_lite                              = true
        wave_lite_server_url                            = "https://wave-lite.example.com"
        wave_server_url                                 = "https://wave.seqera.io"
    """

    # When
    plan = prepare_plan(override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    # Should extract DNS from Wave-Lite URL (strip https:// prefix)
    assert "wave-lite.example.com" == outputs["tower_wave_dns"]["value"]
    # Should NOT contain protocol prefix
    assert "https://" not in outputs["tower_wave_dns"]["value"]


@pytest.mark.local
@pytest.mark.urls
@pytest.mark.wave
def test_tower_wave_dns_wave_lite_disabled(backup_tfvars):
    """Test Wave DNS extraction when Wave-Lite is disabled."""
    # Given
    override_data = """
        flag_use_wave_lite                              = false
        wave_lite_server_url                            = "https://wave-lite.example.com"
        wave_server_url                                 = "https://wave.seqera.io"
    """

    # When
    plan = prepare_plan(override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    # Should extract DNS from regular Wave URL (strip https:// prefix)
    assert "wave.seqera.io" == outputs["tower_wave_dns"]["value"]
    # Should NOT contain protocol prefix
    assert "https://" not in outputs["tower_wave_dns"]["value"]


@pytest.mark.local
@pytest.mark.urls
@pytest.mark.wave
def test_tower_wave_dns_protocol_stripping(backup_tfvars):
    """Test that Wave DNS properly strips protocol prefixes from various URL formats."""
    # Given
    override_data = """
        flag_use_wave_lite                              = true
        wave_lite_server_url                            = "https://wave-lite.example.com"
        wave_server_url                                 = "https://wave.seqera.io"
    """

    # When
    plan = prepare_plan(override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    # Should strip https:// protocol prefix
    assert "wave-lite.example.com" == outputs["tower_wave_dns"]["value"]
    # Validate no protocol remains
    assert not outputs["tower_wave_dns"]["value"].startswith("http")
    assert "://" not in outputs["tower_wave_dns"]["value"]


## ------------------------------------------------------------------------------------
## Wave URL Validation Tests
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.urls
@pytest.mark.wave
def test_wave_url_consistency(backup_tfvars):
    """Test that tower_wave_url and tower_wave_dns are consistent."""
    # Given
    override_data = """
        flag_use_wave_lite                              = true
        wave_lite_server_url                            = "https://wave-lite.example.com"
        wave_server_url                                 = "https://wave.seqera.io"
    """

    # When
    plan = prepare_plan(override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    wave_url = outputs["tower_wave_url"]["value"]
    wave_dns = outputs["tower_wave_dns"]["value"]

    # tower_wave_dns should be tower_wave_url with protocol stripped
    assert wave_url == f"https://{wave_dns}"
    # Ensure they reference the same domain
    assert "wave-lite.example.com" in wave_url
    assert "wave-lite.example.com" == wave_dns
