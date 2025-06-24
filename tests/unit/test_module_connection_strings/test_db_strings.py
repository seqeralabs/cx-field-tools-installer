import pytest


## ------------------------------------------------------------------------------------
## New RDS
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.db
@pytest.mark.db_new
def test_new_tower_db_root(plan_new_db):
    """Test tower_db_root for new RDS scenario.
    In new RDS case:
    - tower_db_local should be empty
    - tower_db_remote_existing should be empty
    - tower_db_remote_new_reconciled should be mock value
    """
    assert plan_new_db.outputs["tower_db_root"] == "mock-new-tower-db.example.com"


@pytest.mark.local
@pytest.mark.db
@pytest.mark.db_new
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
@pytest.mark.db_new
def test_new_swell_db_url(plan_new_db):
    assert "mock-new-tower-db.example.com" in plan_new_db.outputs["swell_db_url"]


@pytest.mark.local
@pytest.mark.db
@pytest.mark.db_new
def test_new_wave_lite_db_url(plan_new_db):
    assert (
        "mock-new-wave-lite-db.example.com" in plan_new_db.outputs["wave_lite_db_url"]
    )


## ------------------------------------------------------------------------------------
## Existing RDS
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.db
@pytest.mark.db_existing
def test_existing_tower_db_root(plan_existing_db):
    """Test tower_db_root for existing RDS scenario.
    In existing RDS case:
    - tower_db_local should be empty
    - tower_db_remote_existing should be mock value
    - tower_db_remote_new_reconciled should be empty
    """
    print("================================================")
    print(f"Outputs: {plan_existing_db.outputs}")
    assert (
        plan_existing_db.outputs["tower_db_root"]
        == "mock-existing-tower-db.example.com"
    )


@pytest.mark.local
@pytest.mark.db
@pytest.mark.db_existing
def test_existing_tower_db_url(plan_existing_db):
    assert (
        "mock-existing-tower-db.example.com" in plan_existing_db.outputs["tower_db_url"]
    )


@pytest.mark.local
@pytest.mark.db
@pytest.mark.db_existing
def test_existing_swell_db_url(plan_existing_db):
    assert (
        "mock-existing-tower-db.example.com" in plan_existing_db.outputs["swell_db_url"]
    )


# GAP: Wave-Lite with pre-existing database.
