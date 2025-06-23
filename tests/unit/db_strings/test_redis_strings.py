import pytest


## ------------------------------------------------------------------------------------
## New Redis
## NOTE: Could combine this with new DB to save testing cycles (if cant optimize)
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.redis
def test_new_tower_redis_url(plan_new_redis):
    assert (
        "redis://mock-new-tower-redis.example.com"
        in plan_new_redis.outputs["tower_redis_url"]
    )


pytest.mark.local


@pytest.mark.redis
def test_new_wave_lite_redis_url(plan_new_redis):
    assert (
        "rediss://mock-new-wave-lite-redis.example.com"
        in plan_new_redis.outputs["wave_lite_redis_url"]
    )


pytest.mark.local


@pytest.mark.redis
def test_new_connect_redis_url(plan_new_redis):
    # Current as of June 2025, prefix still auto-appended by Connect app itself. Dont include.
    print("================================================")
    print(f"Outputs: {plan_new_redis.outputs}")
    assert (
        "mock-new-connect-redis.example.com"
        in plan_new_redis.outputs["tower_connect_redis_url"]
    )
