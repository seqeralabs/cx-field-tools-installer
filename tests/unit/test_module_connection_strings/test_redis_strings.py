import pytest


## ------------------------------------------------------------------------------------
## New Redis
## NOTE: Could combine this with new DB to save testing cycles (if cant optimize)
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.redis
def test_new_tower_redis_url(plan_new_redis):
    outputs = plan_new_redis["planned_values"]["outputs"]
    assert (
        "redis://mock-new-tower-redis.example.com"
        in outputs["tower_redis_url"]["value"]
    )


pytest.mark.local


@pytest.mark.redis
def test_new_wave_lite_redis_url(plan_new_redis):
    outputs = plan_new_redis["planned_values"]["outputs"]
    assert (
        "rediss://mock-new-wave-lite-redis.example.com"
        in outputs["wave_lite_redis_url"]["value"]
    )


pytest.mark.local


@pytest.mark.redis
def test_new_connect_redis_url(plan_new_redis):
    # Current as of June 2025, prefix still auto-appended by Connect app itself. Dont include.
    outputs = plan_new_redis["planned_values"]["outputs"]
    assert (
        "mock-new-connect-redis.example.com"
        in outputs['tower_connect_redis_url']["value"]
    )
