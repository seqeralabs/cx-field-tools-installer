import pytest

from conftest import prepare_plan


## ------------------------------------------------------------------------------------
## New Redis
## ------------------------------------------------------------------------------------
# NOTE: Mock DNS values here are hardcoded into the modules/connection_strings/v1.0.0/main.tf file.


@pytest.mark.local
@pytest.mark.redis
@pytest.mark.redis_external
@pytest.mark.tower
def test_external_tower_redis_url(backup_tfvars):
    # Given
    override_data = """
        flag_create_external_redis                      = true
        flag_use_container_redis                        = false
        flag_enable_data_studio                         = false
        flag_use_wave_lite                              = false
    """

    # When
    plan = prepare_plan(override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    assert (
        "redis://mock-new-tower-redis.example.com"
        in outputs["tower_redis_url"]["value"]
    )

    assert (
        "rediss://mock-new-wave-lite-redis.example.com"
        in outputs["wave_lite_redis_url"]["value"]
    )

    assert (
        "mock-new-connect-redis.example.com"
        in outputs["tower_connect_redis_url"]["value"]
    )


@pytest.mark.local
@pytest.mark.redis
@pytest.mark.redis_external
@pytest.mark.connect
def test_external_connect_redis_url(backup_tfvars):
    # Given
    override_data = """
        flag_create_external_redis                      = true
        flag_use_container_redis                        = false
        flag_enable_data_studio                         = true
        flag_use_wave_lite                              = false
    """

    # When
    plan = prepare_plan(override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    assert (
        "mock-new-connect-redis.example.com"
        in outputs["tower_connect_redis_url"]["value"]
    )


@pytest.mark.local
@pytest.mark.redis
@pytest.mark.redis_external
@pytest.mark.wave_lite
def test_external_wave_lite_redis_url(backup_tfvars):
    """Test Wave-Lite Redis URL with external Redis instance."""
    # Given
    override_data = """
        flag_create_external_redis                      = true
        flag_use_container_redis                        = false
        flag_enable_data_studio                         = false
        flag_use_wave_lite                              = true
    """

    # When
    plan = prepare_plan(override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    # Wave-Lite should use secure Redis connection (rediss://)
    assert (
        "rediss://mock-new-wave-lite-redis.example.com"
        in outputs["wave_lite_redis_url"]["value"]
    )

    # Ensure it's different from Tower's Redis (which uses redis://)
    assert (
        outputs["wave_lite_redis_url"]["value"] != outputs["tower_redis_url"]["value"]
    )

    # Validate secure vs insecure protocol difference
    assert "rediss://" in outputs["wave_lite_redis_url"]["value"]
    assert "redis://" in outputs["tower_redis_url"]["value"]


## ------------------------------------------------------------------------------------
## Container Redis
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.redis
@pytest.mark.redis_container
@pytest.mark.container
@pytest.mark.tower
def test_container_tower_redis_url(backup_tfvars):
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
    plan = prepare_plan(override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    # Tower Redis should use container service name
    assert "redis://redis:6379" in outputs["tower_redis_url"]["value"]

    # Connect Redis should use the same container service
    assert "redis://redis:6379" in outputs["tower_connect_redis_url"]["value"]

    # Wave-Lite Redis should use dedicated container service with secure connection
    assert "rediss://wave-redis:6379" in outputs["wave_lite_redis_url"]["value"]


@pytest.mark.local
@pytest.mark.redis
@pytest.mark.redis_container
@pytest.mark.container
@pytest.mark.connect
def test_container_connect_redis_url(backup_tfvars):
    """Test Connect with container Redis."""
    # Given
    override_data = """
        flag_create_external_redis                      = false
        flag_use_container_redis                        = true
        flag_enable_data_studio                         = true
        flag_use_wave_lite                              = false
    """

    # When
    plan = prepare_plan(override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then
    # Connect Redis should use the same container service
    assert "redis:6379" in outputs["tower_connect_redis_url"]["value"]


@pytest.mark.local
@pytest.mark.redis
@pytest.mark.redis_container
@pytest.mark.container
@pytest.mark.wave_lite
def test_container_wave_lite_redis_url(backup_tfvars):
    """Test Redis URLs with container Redis mode."""
    # Given
    override_data = """
        flag_create_external_redis                      = false
        flag_use_container_redis                        = true
        flag_enable_data_studio                         = false
        flag_use_wave_lite                              = true
    """

    # When
    plan = prepare_plan(override_data)
    outputs = plan["planned_values"]["outputs"]

    # Then

    # Wave-Lite Redis should use dedicated container service with secure connection
    assert "rediss://wave-redis:6379" in outputs["wave_lite_redis_url"]["value"]

    # Ensure it's different from Tower's Redis container
    assert (
        outputs["wave_lite_redis_url"]["value"] != outputs["tower_redis_url"]["value"]
    )
