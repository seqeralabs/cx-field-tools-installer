import pytest

from tests.utils.local import prepare_plan


## ------------------------------------------------------------------------------------
## URL Tests - ALB
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.urls
@pytest.mark.urls_secure
def test_urls_alb_all_ecosystem(backup_tfvars):
    """Test URLS when using ALB."""
    # Given
    connect_secure_override_data = """
        tower_server_url                                = "tower.example.com"

        flag_create_load_balancer                       = true
        flag_do_not_use_https                           = false

        flag_enable_groundswell                         = true
        flag_enable_data_studio                         = true
        flag_use_wave_lite                              = true

        wave_server_url                                 = "autowave.example.com"

        flag_studio_enable_path_routing                 = false
    """

    # When
    plan = prepare_plan(connect_secure_override_data)
    outputs = plan["planned_values"]["outputs"]

    tower_base_url             = outputs["tower_base_url"]["value"]
    tower_server_url           = outputs["tower_server_url"]["value"]
    tower_api_endpoint         = outputs["tower_api_endpoint"]["value"]

    tower_connect_dns          = outputs["tower_connect_dns"]["value"]
    tower_connect_wildcard_dns = outputs["tower_connect_wildcard_dns"]["value"]
    tower_connect_server_url   = outputs["tower_connect_server_url"]["value"]

    tower_wave_dns             = outputs["tower_wave_dns"]["value"]
    tower_wave_url             = outputs["tower_wave_url"]["value"]

    # Then
    assert "tower.example.com" == tower_base_url
    assert "https://tower.example.com" == tower_server_url
    assert "https://tower.example.com/api" == tower_api_endpoint

    assert "connect.tower.example.com" == tower_connect_dns
    assert "*.tower.example.com" == tower_connect_wildcard_dns
    assert "https://connect.tower.example.com" == tower_connect_server_url

    assert "autowave.example.com" == tower_wave_dns
    assert "https://autowave.example.com" == tower_wave_url



@pytest.mark.local
@pytest.mark.urls
@pytest.mark.urls_secure
def test_urls_alb_no_ecosystem(backup_tfvars):
    """Test URLS when using ALB."""
    # Given
    connect_secure_override_data = """
        tower_server_url                                = "tower.example.com"

        flag_create_load_balancer                       = true
        flag_do_not_use_https                           = false

        flag_enable_groundswell                         = false
        flag_enable_data_studio                         = false
        flag_use_wave_lite                              = false

        wave_server_url                                 = "autowave.example.com"

        flag_studio_enable_path_routing                 = false
    """

    # When
    plan = prepare_plan(connect_secure_override_data)
    outputs = plan["planned_values"]["outputs"]

    tower_base_url             = outputs["tower_base_url"]["value"]
    tower_server_url           = outputs["tower_server_url"]["value"]
    tower_api_endpoint         = outputs["tower_api_endpoint"]["value"]

    tower_connect_dns          = outputs["tower_connect_dns"]["value"]
    tower_connect_wildcard_dns = outputs["tower_connect_wildcard_dns"]["value"]
    tower_connect_server_url   = outputs["tower_connect_server_url"]["value"]

    tower_wave_dns             = outputs["tower_wave_dns"]["value"]
    tower_wave_url             = outputs["tower_wave_url"]["value"]

    # Then
    assert "tower.example.com" == tower_base_url
    assert "https://tower.example.com" == tower_server_url
    assert "https://tower.example.com/api" == tower_api_endpoint

    assert "N/A" == tower_connect_dns
    assert "N/A" == tower_connect_wildcard_dns
    assert "N/A" == tower_connect_server_url

    assert "N/A" == tower_wave_dns
    assert "N/A" == tower_wave_url

## ------------------------------------------------------------------------------------
## URL Tests - No HTTPS
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.urls
@pytest.mark.urls_insecure
def test_urls_no_https_all_ecoystem(backup_tfvars):
    """Check ecosystem URLS when no https active."""
    # Given
    connect_insecure_override_data = """
        tower_server_url                                = "tower.example.com"

        flag_create_load_balancer                       = false
        flag_do_not_use_https                           = true

        flag_enable_groundswell                         = true
        flag_enable_data_studio                         = true
        flag_use_wave_lite                              = true

        wave_server_url                                 = "autowave.example.com"
        
    """

    # When
    plan = prepare_plan(connect_insecure_override_data)
    outputs = plan["planned_values"]["outputs"]

    tower_base_url             = outputs["tower_base_url"]["value"]
    tower_server_url           = outputs["tower_server_url"]["value"]
    tower_api_endpoint         = outputs["tower_api_endpoint"]["value"]

    tower_connect_dns          = outputs["tower_connect_dns"]["value"]
    tower_connect_wildcard_dns = outputs["tower_connect_wildcard_dns"]["value"]
    tower_connect_server_url   = outputs["tower_connect_server_url"]["value"]
    tower_connect_redis_dns   = outputs["tower_connect_redis_dns"]["value"]
    tower_connect_redis_url   = outputs["tower_connect_redis_url"]["value"]

    tower_wave_dns             = outputs["tower_wave_dns"]["value"]
    tower_wave_url             = outputs["tower_wave_url"]["value"]
    wave_lite_db_dns           = outputs["wave_lite_db_dns"]["value"]
    wave_lite_db_url           = outputs["wave_lite_db_url"]["value"]
    wave_lite_redis_dns        = outputs["wave_lite_redis_dns"]["value"]
    wave_lite_redis_url        = outputs["wave_lite_redis_url"]["value"]

    # Then
    assert "tower.example.com" == tower_base_url
    assert "http://tower.example.com:8000" == tower_server_url
    assert "http://tower.example.com:8000/api" == tower_api_endpoint

    assert "N/A" == tower_connect_dns
    assert "N/A" == tower_connect_wildcard_dns
    assert "N/A" == tower_connect_server_url
    assert "N/A" == tower_connect_redis_dns
    assert "N/A" == tower_connect_redis_url

    assert "N/A" == tower_wave_dns
    assert "N/A" == tower_wave_url
    assert "N/A" == wave_lite_db_dns
    assert "N/A" == wave_lite_db_url
    assert "N/A" == wave_lite_redis_dns
    assert "N/A" == wave_lite_redis_url


@pytest.mark.local
@pytest.mark.urls
@pytest.mark.urls_insecure
def test_urls_no_https_no_ecoystem(backup_tfvars):
    """Check ecosystem URLS when no https active."""
    # Given
    connect_insecure_override_data = """
        tower_server_url                                = "tower.example.com"

        flag_create_load_balancer                       = false
        flag_do_not_use_https                           = true

        flag_enable_groundswell                         = false
        flag_enable_data_studio                         = false
        flag_use_wave_lite                              = false

        wave_server_url                                 = "autowave.example.com"
        
    """

    # When
    plan = prepare_plan(connect_insecure_override_data)
    outputs = plan["planned_values"]["outputs"]

    tower_base_url             = outputs["tower_base_url"]["value"]
    tower_server_url           = outputs["tower_server_url"]["value"]
    tower_api_endpoint         = outputs["tower_api_endpoint"]["value"]

    tower_connect_dns          = outputs["tower_connect_dns"]["value"]
    tower_connect_wildcard_dns = outputs["tower_connect_wildcard_dns"]["value"]
    tower_connect_server_url   = outputs["tower_connect_server_url"]["value"]
    tower_connect_redis_dns   = outputs["tower_connect_redis_dns"]["value"]
    tower_connect_redis_url   = outputs["tower_connect_redis_url"]["value"]

    tower_wave_dns             = outputs["tower_wave_dns"]["value"]
    tower_wave_url             = outputs["tower_wave_url"]["value"]
    wave_lite_db_dns           = outputs["wave_lite_db_dns"]["value"]
    wave_lite_db_url           = outputs["wave_lite_db_url"]["value"]
    wave_lite_redis_dns        = outputs["wave_lite_redis_dns"]["value"]
    wave_lite_redis_url        = outputs["wave_lite_redis_url"]["value"]

    # Then
    assert "tower.example.com" == tower_base_url
    assert "http://tower.example.com:8000" == tower_server_url
    assert "http://tower.example.com:8000/api" == tower_api_endpoint

    assert "N/A" == tower_connect_dns
    assert "N/A" == tower_connect_wildcard_dns
    assert "N/A" == tower_connect_server_url
    assert "N/A" == tower_connect_redis_dns
    assert "N/A" == tower_connect_redis_url

    assert "N/A" == tower_wave_dns
    assert "N/A" == tower_wave_url
    assert "N/A" == wave_lite_db_dns
    assert "N/A" == wave_lite_db_url
    assert "N/A" == wave_lite_redis_dns
    assert "N/A" == wave_lite_redis_url


## ------------------------------------------------------------------------------------
## URL Tests - Connect Path-Routing
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.urls
@pytest.mark.connect
def test_connect_alb_no_subdomain(backup_tfvars):
    """Test Conect path-based routing. Ensure default 'connect.' is not present.
    """
    # Given
    connect_dns_override_data = """
        tower_server_url                                = "tower.example.com"

        flag_create_load_balancer                       = true
        flag_do_not_use_https                           = false

        flag_studio_enable_path_routing                  = true
        data_studio_path_routing_url                     = "autoconnect.example.com"
    """

    # When
    plan = prepare_plan(connect_dns_override_data)
    outputs = plan["planned_values"]["outputs"]

    tower_connect_dns          = outputs["tower_connect_dns"]["value"]
    tower_connect_wildcard_dns = outputs["tower_connect_wildcard_dns"]["value"]
    tower_connect_server_url   = outputs["tower_connect_server_url"]["value"]

    # Then
    assert "autoconnect.example.com" == tower_connect_dns
    assert "autoconnect.example.com" == tower_connect_wildcard_dns
    assert "https://autoconnect.example.com" == tower_connect_server_url


@pytest.mark.local
@pytest.mark.urls
@pytest.mark.connect
def test_connect_ec2_no_subdomain(backup_tfvars):
    """Test Conect path-based routing. Ensure default 'connect.' is not present.
    """
    # Given
    connect_dns_override_data = """
        tower_server_url                                = "tower.example.com"

        flag_create_load_balancer                       = false
        flag_use_private_cacert                         = true
        flag_do_not_use_https                           = false

        flag_studio_enable_path_routing                  = true
        data_studio_path_routing_url                     = "autoconnect.example.com"
    """

    # When
    plan = prepare_plan(connect_dns_override_data)
    outputs = plan["planned_values"]["outputs"]

    tower_connect_dns          = outputs["tower_connect_dns"]["value"]
    tower_connect_wildcard_dns = outputs["tower_connect_wildcard_dns"]["value"]
    tower_connect_server_url   = outputs["tower_connect_server_url"]["value"]

    # Then
    assert "autoconnect.example.com" == tower_connect_dns
    assert "autoconnect.example.com" == tower_connect_wildcard_dns
    assert "https://autoconnect.example.com" == tower_connect_server_url
