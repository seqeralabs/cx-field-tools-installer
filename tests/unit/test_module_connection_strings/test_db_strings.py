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
    print(f"plan_new_db outputs are: {plan_new_db['planned_values']['outputs']}")
    print(f"plan_new_db outputs are: {plan_new_db['planned_values']['outputs'].keys()}")
    outputs = plan_new_db['planned_values']['outputs']

    assert (
        outputs["tower_db_root"]["value"] == "mock-new-tower-db.example.com"
    )


@pytest.mark.local
@pytest.mark.db
@pytest.mark.db_new
def test_new_tower_db_url(plan_new_db):
    outputs = plan_new_db['planned_values']['outputs']
    assert "mock-new-tower-db.example.com" in outputs["tower_db_url"]["value"]


@pytest.mark.local
@pytest.mark.db
@pytest.mark.db_new
def test_new_swell_db_url(plan_new_db):
    outputs = plan_new_db['planned_values']['outputs']
    assert "mock-new-tower-db.example.com" in outputs["swell_db_url"]["value"]


@pytest.mark.local
@pytest.mark.db
@pytest.mark.db_new
def test_new_wave_lite_db_url(plan_new_db):
    outputs = plan_new_db['planned_values']['outputs']
    assert (
        "mock-new-wave-lite-db.example.com" in outputs["wave_lite_db_url"]["value"]
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
    outputs = plan_existing_db['planned_values']['outputs']
    assert (
        outputs['tower_db_root']['value'] == "mock-existing-tower-db.example.com"
    )


@pytest.mark.local
@pytest.mark.db
@pytest.mark.db_existing
def test_existing_tower_db_url(plan_existing_db):
    outputs = plan_existing_db['planned_values']['outputs']
    assert (
        "mock-existing-tower-db.example.com" in outputs['tower_db_url']['value']
    )


@pytest.mark.local
@pytest.mark.db
@pytest.mark.db_existing
def test_existing_swell_db_url(plan_existing_db):
    outputs = plan_existing_db['planned_values']['outputs']
    assert (
        "mock-existing-tower-db.example.com" in outputs['swell_db_url']['value']
    )


# GAP: Wave-Lite with pre-existing database.
