import pytest

from conftest import prepare_plan


## ------------------------------------------------------------------------------------
## Tower Core URL Tests
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.urls
def test_tower_base_url(backup_tfvars):
    """Verify that the base URL for Tower is correctly constructed."""
    # Given
    urls_static_override_data = """
        tower_server_url                                = "mock-tower-base-static.example.com"
        flag_use_container_redis                        = false
    """

    # When
    plan = prepare_plan(urls_static_override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    assert "mock-tower-base-static.example.com" in outputs["tower_base_url"]["value"]


## ------------------------------------------------------------------------------------
## Tower Core URL Tests - Insecure
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.urls
@pytest.mark.urls_insecure
def test_tower_insecure_urls(backup_tfvars):
    """Test Tower insecure url output."""
    # Given
    urls_insecure_override_data = """
        tower_server_url                                = "mock-tower-base-insecure.example.com"
        flag_create_load_balancer                       = false
        flag_do_not_use_https				            = true
    """

    # When
    plan = prepare_plan(urls_insecure_override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    assert (
        "http://mock-tower-base-insecure.example.com:8000"
        in outputs["tower_server_url"]["value"]
    )


## ------------------------------------------------------------------------------------
## Tower Core URL Tests - Secure
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.urls
@pytest.mark.urls_secure
def test_tower_secure_urls(backup_tfvars):
    """Test Tower secure url output."""
    # Given
    urls_secure_override_data = """
        tower_server_url                                = "mock-tower-base-secure.example.com"
        flag_create_load_balancer                       = true
        flag_do_not_use_https                           = false
    """

    # When
    plan = prepare_plan(urls_secure_override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    assert (
        "https://mock-tower-base-secure.example.com"
        == outputs["tower_server_url"]["value"]
    )


## ------------------------------------------------------------------------------------
## Tower API Endpoint Tests
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.urls
@pytest.mark.urls_insecure
def test_tower_api_endpoint_insecure(backup_tfvars):
    """Test Tower API endpoint construction for insecure mode."""
    # Given
    api_insecure_override_data = """
        tower_server_url                                = "mock-tower-api-insecure.example.com"
        flag_create_load_balancer                       = false
        flag_do_not_use_https                           = true
    """

    # When
    plan = prepare_plan(api_insecure_override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    assert (
        "http://mock-tower-api-insecure.example.com:8000/api"
        == outputs["tower_api_endpoint"]["value"]
    )


@pytest.mark.local
@pytest.mark.urls
@pytest.mark.urls_secure
def test_tower_api_endpoint_secure(backup_tfvars):
    """Test Tower API endpoint construction for secure mode."""
    # Given
    api_secure_override_data = """
        tower_server_url                                = "mock-tower-api-secure.example.com"
        flag_create_load_balancer                       = true
        flag_do_not_use_https                           = false
    """

    # When
    plan = prepare_plan(api_secure_override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    assert (
        "https://mock-tower-api-secure.example.com/api"
        == outputs["tower_api_endpoint"]["value"]
    )
