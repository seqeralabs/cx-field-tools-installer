import pytest

from conftest import prepare_plan


## ------------------------------------------------------------------------------------
## New Redis
## ------------------------------------------------------------------------------------
# NOTE: Mock DNS values here are hardcoded into the modules/connection_strings/v1.0.0/main.tf file.


@pytest.mark.local
@pytest.mark.redis
def test_external_redis_url(backup_tfvars):
    # Given
    new_redis_override_data = """
        flag_create_external_redis                      = true
        flag_use_container_redis                        = false
    """

    # When
    plan = prepare_plan(new_redis_override_data)
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
