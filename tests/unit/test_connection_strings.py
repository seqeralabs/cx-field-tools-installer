import pytest


def test_tower_db_url(tfplan_json):
    """
    Test that an installation that uses RDS does not have the container URL.
    """
    flag_create_external_db = tfplan_json["variables"]["flag_create_external_db"]["value"]
    flag_use_existing_external_db = tfplan_json["variables"]["flag_use_existing_external_db"]["value"]
    use_external_db = True if (flag_create_external_db or flag_use_existing_external_db) else False

    tower_db_url_var = tfplan_json["variables"]["tower_db_url"]["value"]
    tower_db_url_output = tfplan_json["planned_values"]["outputs"]["tower_db_url"].get("value", None)

    if use_external_db:
        assert tower_db_url_output != tower_db_url_var
    else:
        assert tower_db_url_output == tower_db_url_var


def test_tower_redis_url(tfplan_json):
    """
    Test that an installation that uses Redis does not have the container URL.
    """
    flag_create_external_redis = tfplan_json["variables"]["flag_create_external_redis"]["value"]
    use_external_redis = True if (flag_create_external_redis) else False

    tower_redis_url_var = "redis://redis:6379"
    tower_redis_url_output = tfplan_json["planned_values"]["outputs"]["tower_redis_url"].get("value", None)

    if use_external_redis:
        assert tower_redis_url_output != tower_redis_url_var
    else:
        assert tower_redis_url_output == tower_redis_url_var


if __name__ == "__main__":
    pytest.main()