"""Tests for the MySQL 8.4 upgrade checks (Design Decision 25).

Covers `verify_database_version` in `check_configuration.py` and the plan parsing in
`check_db_replacement.py`. No Terraform or AWS calls.
"""

from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
from tests.utils.config import FP


sys.path.insert(0, str(Path(FP.ROOT) / "scripts"))
sys.path.insert(0, str(Path(FP.ROOT) / "scripts/installer/validation"))
import check_configuration as cc
import check_db_replacement as cdr


pytestmark = [pytest.mark.local, pytest.mark.quick]


def _db_data(**overrides) -> SimpleNamespace:
    """Template defaults for the database checks: container MySQL 8.4, TLS on, Platform v26.2."""
    values = {
        "flag_create_external_db": False,
        "flag_use_container_db": True,
        "db_engine_version": "8.4",
        "db_param_group": "mysql8.4",
        "db_container_engine_version": "8.4",
        "db_enforce_tls": True,
        "db_allow_major_version_upgrade": False,
        "flag_enable_groundswell": False,
        "tower_container_version": "v26.2.0-RC16",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_defaults_pass(caplog):
    """Template defaults produce no error and no warning."""
    cc.verify_database_version(_db_data())
    assert not caplog.records


def test_param_group_must_match_version():
    """New RDS with an 8.4 engine and an 8.0 parameter group fails."""
    with pytest.raises(SystemExit):
        cc.verify_database_version(
            _db_data(flag_create_external_db=True, flag_use_container_db=False, db_param_group="mysql8.0")
        )


def test_param_group_match_with_patch_version():
    """A patch version such as 8.4.11 still matches mysql8.4."""
    cc.verify_database_version(
        _db_data(flag_create_external_db=True, flag_use_container_db=False, db_engine_version="8.4.11")
    )


def test_mysql_8_0_warns_on_platform_26(caplog):
    """MySQL 8.0 on Platform v26.1+ warns that the combination is unsupported."""
    cc.verify_database_version(_db_data(db_container_engine_version="8.0"))
    assert "isn't supported by Platform v26.1+" in caplog.text


def test_groundswell_with_tls_warns(caplog):
    """TLS enforced on 8.4 with Groundswell on warns about the unconfirmed Groundswell driver."""
    cc.verify_database_version(_db_data(flag_enable_groundswell=True))
    assert "Groundswell" in caplog.text


def test_groundswell_on_8_0_no_tls_warning(caplog):
    """On MySQL 8.0, TLS isn't active, so there's no Groundswell TLS warning."""
    cc.verify_database_version(_db_data(flag_enable_groundswell=True, db_container_engine_version="8.0"))
    assert "Groundswell" not in caplog.text


def test_upgrade_switch_reminder(caplog):
    """db_allow_major_version_upgrade = true prints the set-it-back reminder."""
    cc.verify_database_version(_db_data(db_allow_major_version_upgrade=True))
    assert "back to false" in caplog.text


def _plan(*actions_per_instance: list[str]) -> dict:
    """A minimal `terraform show -json` plan with one `aws_db_instance` per actions list."""
    changes = [
        {
            "address": f"module.rds[0].module.db_instance.aws_db_instance.this[{i}]",
            "type": "aws_db_instance",
            "change": {"actions": actions},
        }
        for i, actions in enumerate(actions_per_instance)
    ]
    changes.append(
        {"address": "aws_db_parameter_group.x", "type": "aws_db_parameter_group", "change": {"actions": ["delete"]}}
    )
    return {"resource_changes": changes}


def test_plan_update_in_place_found():
    """An in-place update is reported and contains no delete."""
    assert cdr.find_db_instance_changes(_plan(["update"])) == [
        ("module.rds[0].module.db_instance.aws_db_instance.this[0]", ["update"])
    ]


def test_plan_replacement_detected():
    """A replacement (delete + create) is reported with its delete action."""
    changes = cdr.find_db_instance_changes(_plan(["delete", "create"]))
    assert any("delete" in actions for _, actions in changes)


def test_plan_ignores_other_resource_types():
    """Only aws_db_instance changes count; a parameter-group replacement is ignored."""
    assert cdr.find_db_instance_changes(_plan()) == []
