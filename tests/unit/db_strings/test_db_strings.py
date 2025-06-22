import pytest


## ------------------------------------------------------------------------------------
## New RDS
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.db
def test_new_tower_db_url(plan_new_db):
    # assert plan_new_db.outputs['tower_db_url'] == 'mock-db.example.com'
    # mod = plan_new_db.modules['module.connection_strings']
    # print(mod)
    # res ['tower_db_url'] == 'mock-db.example.com'
    # print(plan_new_db.modules)
    # mod = plan_new_db.modules['module.connection_strings']
    # print(mod)
    # print(plan_new_db.outputs)
    # This value comes from mock value in module.connection_strings.main.tf

    assert "mock-new-tower-db.example.com" in plan_new_db.outputs["tower_db_url"]


@pytest.mark.local
@pytest.mark.db
def test_new_swell_db_url(plan_new_db):
    assert "mock-new-tower-db.example.com" in plan_new_db.outputs["swell_db_url"]


@pytest.mark.local
@pytest.mark.db
def test_new_wave_lite_db_url(plan_new_db):
    assert (
        "mock-new-wave-lite-db.example.com" in plan_new_db.outputs["wave_lite_db_url"]
    )


## ------------------------------------------------------------------------------------
## Existing RDS
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.db
@ pytest.mark.db_existing
def test_existing_tower_db_url(plan_existing_db):
    assert (
        "mock-existing-tower-db.example.com" in plan_existing_db.outputs["tower_db_url"]
    )


@pytest.mark.local
@pytest.mark.db
@ pytest.mark.db_existing
def test_existing_swell_db_url(plan_existing_db):
    assert (
        "mock-existing-tower-db.example.com" in plan_existing_db.outputs["swell_db_url"]
    )


# GAP: Wave-Lite with pre-existing database.
