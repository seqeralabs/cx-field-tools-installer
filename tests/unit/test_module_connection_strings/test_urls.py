import pytest

from tests.utils.local import prepare_plan


## ------------------------------------------------------------------------------------
## Tower Core URL Tests
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.urls
def test_tower_base_url(backup_tfvars):
    """Verify that the base URL for Tower is correctly constructed."""
    # Given
    urls_static_override_data = """
        tower_server_url                                = "tower.example.com"
    """

    # When
    plan = prepare_plan(urls_static_override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    assert "tower.example.com" in outputs["tower_base_url"]["value"]


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
        tower_server_url                                = "tower.example.com"
        flag_create_load_balancer                       = false
        flag_do_not_use_https                           = true
    """

    # When
    plan = prepare_plan(urls_insecure_override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    assert "http://tower.example.com:8000" in outputs["tower_server_url"]["value"]


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
        tower_server_url                                = "tower.example.com"
        flag_create_load_balancer                       = true
        flag_do_not_use_https                           = false
    """

    # When
    plan = prepare_plan(urls_secure_override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    assert "https://tower.example.com" == outputs["tower_server_url"]["value"]


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
        tower_server_url                                = "tower.example.com"
        flag_create_load_balancer                       = false
        flag_do_not_use_https                           = true
    """

    # When
    plan = prepare_plan(api_insecure_override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    assert "http://tower.example.com:8000/api" == outputs["tower_api_endpoint"]["value"]


@pytest.mark.local
@pytest.mark.urls
@pytest.mark.urls_secure
def test_tower_api_endpoint_secure(backup_tfvars):
    """Test Tower API endpoint construction for secure mode."""
    # Given
    api_secure_override_data = """
        tower_server_url                                = "tower.example.com"
        flag_create_load_balancer                       = true
        flag_do_not_use_https                           = false
    """

    # When
    plan = prepare_plan(api_secure_override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    assert "https://tower.example.com/api" == outputs["tower_api_endpoint"]["value"]


## ------------------------------------------------------------------------------------
## Tower Connect DNS Tests (ALB Host-Matching)
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.urls
@pytest.mark.connect
def test_connect_alb_dns(backup_tfvars):
    """Test Tower Connect DNS construction for ALB host-matching.
    NOTE: `connect` subdomain is hardcoded right now.
    """
    # Given
    connect_dns_override_data = """
        tower_server_url                                = "tower.example.com"
        flag_create_load_balancer                       = true
        flag_do_not_use_https                           = false
        flag_studio_enable_path_routing                  = false

    """

    # When
    plan = prepare_plan(connect_dns_override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    assert "connect.tower.example.com" == outputs["tower_connect_dns"]["value"]


@pytest.mark.local
@pytest.mark.urls
@pytest.mark.connect
def test_connect_alb_dns_no_subdomain(backup_tfvars):
    """Test Tower Connect DNS construction for ALB host-matching.
    NOTE: Ensure 'connect.' is not present when path-based routing is specified.
    """
    # Given
    connect_dns_override_data = """
        tower_server_url                                = "tower.example.com"
        flag_create_load_balancer                       = true
        flag_do_not_use_https                           = false
        flag_studio_enable_path_routing                  = true
    """

    # When
    plan = prepare_plan(connect_dns_override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    assert "connect." not in outputs["tower_connect_dns"]["value"]


@pytest.mark.local
@pytest.mark.urls
@pytest.mark.connect
def test_connect_wildcard_dns(backup_tfvars):
    """Test Tower Connect wildcard DNS construction for ALB host-matching."""
    # Given
    connect_wildcard_override_data = """
        tower_server_url                                = "tower.example.com"
        flag_create_load_balancer                       = true
        flag_do_not_use_https                           = false
    """

    # When
    plan = prepare_plan(connect_wildcard_override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    assert "*.tower.example.com" == outputs["tower_connect_wildcard_dns"]["value"]


## ------------------------------------------------------------------------------------
## Tower Connect Server URL Tests (Connect Protocol Logic)
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.urls
@pytest.mark.urls_insecure
@pytest.mark.connect
def test_connect_server_direct_url_insecure(backup_tfvars):
    """Test Tower Connect server URL construction for insecure mode."""
    # Given
    connect_insecure_override_data = """
        tower_server_url                                = "tower.example.com"
        flag_create_load_balancer                       = false
        flag_do_not_use_https                           = true
    """

    # When
    plan = prepare_plan(connect_insecure_override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    assert (
        "http://tower.example.com:9090" == outputs["tower_connect_server_url"]["value"]
    )


@pytest.mark.local
@pytest.mark.urls
@pytest.mark.urls_secure
@pytest.mark.connect
def test_tower_connect_server_direct_url_secure(backup_tfvars):
    """Test Tower Connect server URL construction for secure mode."""
    # Given
    connect_secure_override_data = """
        tower_server_url                                = "tower.example.com"
        flag_create_load_balancer                       = true
        flag_do_not_use_https                           = false
    """

    # When
    plan = prepare_plan(connect_secure_override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    assert (
        "https://connect.tower.example.com"
        == outputs["tower_connect_server_url"]["value"]
    )
