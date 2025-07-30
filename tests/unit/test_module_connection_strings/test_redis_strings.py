import pytest

from tests.utils.local import prepare_plan


## ------------------------------------------------------------------------------------
## New Redis
## ------------------------------------------------------------------------------------
# NOTE: Mock DNS values here are hardcoded into the modules/connection_strings/v1.0.0/main.tf file.


@pytest.mark.local
@pytest.mark.redis
@pytest.mark.redis_external
@pytest.mark.tower
def test_external_redis_url_full_ecosystem(backup_tfvars):
    # Given
    override_data = """
        flag_create_external_redis                      = true
        flag_use_container_redis                        = false

        flag_enable_data_studio                         = true
        flag_use_wave_lite                              = true
    """

    # When
    plan         = prepare_plan(override_data)
    outputs                 = plan["planned_values"]["outputs"]

    tower_redis_url         = outputs["tower_redis_url"]["value"]
    tower_connect_redis_url = outputs["tower_connect_redis_url"]["value"]
    wave_lite_redis_dns     = outputs["wave_lite_redis_dns"]["value"]
    wave_lite_redis_url     = outputs["wave_lite_redis_url"]["value"]

    # Then
    assert "redis://mock-new-tower-redis.example.com:6379" == tower_redis_url
    assert "mock-new-connect-redis.example.com" in tower_connect_redis_url
    assert "mock.wave-redis.com" == wave_lite_redis_dns
    assert "rediss://mock.wave-redis.com" == wave_lite_redis_url
    assert wave_lite_redis_url != tower_redis_url


@pytest.mark.local
@pytest.mark.redis
@pytest.mark.redis_external
@pytest.mark.tower
def test_external_redis_url_no_ecosystem(backup_tfvars):
    # Given
    override_data = """
        flag_create_external_redis                      = true
        flag_use_container_redis                        = false

        flag_enable_data_studio                         = false
        flag_use_wave_lite                              = false
    """

    # When
    plan         = prepare_plan(override_data)
    outputs                 = plan["planned_values"]["outputs"]

    tower_redis_url         = outputs["tower_redis_url"]["value"]
    tower_connect_redis_url = outputs["tower_connect_redis_url"]["value"]
    wave_lite_redis_dns     = outputs["wave_lite_redis_dns"]["value"]
    wave_lite_redis_url     = outputs["wave_lite_redis_url"]["value"]

    # Then
    assert "redis://mock-new-tower-redis.example.com:6379" == tower_redis_url
    assert "mock-new-connect-redis.example.com" in tower_connect_redis_url
    assert "N/A" == wave_lite_redis_dns
    assert "N/A" == wave_lite_redis_url


## ------------------------------------------------------------------------------------
## Container Redis
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.redis
@pytest.mark.redis_container
@pytest.mark.container
@pytest.mark.tower
def test_container_redis_url_all_ecosystem(backup_tfvars):
    """Test Tower with container Redis.
    NOTE: Studios and Wave-Lite default to local container paths when not activated.
    """
    # Given
    override_data = """
        flag_create_external_redis                      = false
        flag_use_container_redis                        = true

        flag_enable_data_studio                         = true
        flag_use_wave_lite                              = true
    """

    # When
    plan         = prepare_plan(override_data)
    outputs                 = plan["planned_values"]["outputs"]

    tower_redis_url         = outputs["tower_redis_url"]["value"]
    tower_connect_redis_url = outputs["tower_connect_redis_url"]["value"]
    wave_lite_redis_dns     = outputs["wave_lite_redis_dns"]["value"]
    wave_lite_redis_url     = outputs["wave_lite_redis_url"]["value"]

    # Then
    # Tower Redis should use container service name
    assert "redis://redis:6379" == tower_redis_url
    assert "redis:6379" in tower_connect_redis_url
    assert "wave-redis:6379" == wave_lite_redis_dns
    assert "redis://wave-redis:6379" == wave_lite_redis_url
    assert wave_lite_redis_url != tower_redis_url


@pytest.mark.local
@pytest.mark.redis
@pytest.mark.redis_container
@pytest.mark.container
@pytest.mark.tower
def test_container_redis_url_no_ecosystem(backup_tfvars):
    """Test Tower with container Redis.
    NOTE: Studios and Wave-Lite default to local container paths when not activated.
    """
    # Given
    override_data = """
        flag_create_external_redis                      = false
        flag_use_container_redis                        = true

        flag_enable_data_studio                         = false
        flag_use_wave_lite                              = false
    """

    # When
    plan         = prepare_plan(override_data)
    outputs                 = plan["planned_values"]["outputs"]

    tower_redis_url         = outputs["tower_redis_url"]["value"]
    tower_connect_redis_url = outputs["tower_connect_redis_url"]["value"]
    wave_lite_redis_dns     = outputs["wave_lite_redis_dns"]["value"]
    wave_lite_redis_url     = outputs["wave_lite_redis_url"]["value"]

    # Then
    # Tower Redis should use container service name
    assert "redis://redis:6379" == tower_redis_url
    assert "redis:6379" in tower_connect_redis_url  #TODO: Fix this
    assert "N/A" == wave_lite_redis_dns
    assert "N/A" == wave_lite_redis_url
    assert wave_lite_redis_url != tower_redis_url
