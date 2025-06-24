import pytest


## ------------------------------------------------------------------------------------
## Tower Core URL Tests
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.urls
def test_tower_base_url(plan_assets_urls_static):
    """Test tower_base_url output.
    This test verifies that the base URL for Tower is correctly constructed.
    """
    # The base URL should be constructed from the mock values in the test fixtures
    assert (
        "mock-tower-base-static.example.com"
        in plan_assets_urls_static.outputs["tower_base_url"]
    )


## ------------------------------------------------------------------------------------
## Tower Core URL Tests - Insecure
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.urls
@pytest.mark.urls_insecure
def test_tower_insecure_urls(plan_assets_urls_insecure):
    """Test tower insecure url output."""
    assert (
        "http://mock-tower-base-insecure.example.com:8000"
        in plan_assets_urls_insecure.outputs["tower_server_url"]
    )
