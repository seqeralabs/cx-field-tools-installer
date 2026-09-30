"""Tests for the numeric version comparisons in `check_configuration.py`.

String comparison sorted "0.14.0" before "0.8.2" and "v26.10.0" before "v26.2.0". These cases
pin the numeric behaviour of `_is_before`, and the path-routing check that the bug broke.
"""

from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
from tests.utils.config import FP


sys.path.insert(0, str(Path(FP.ROOT) / "scripts"))
sys.path.insert(0, str(Path(FP.ROOT) / "scripts/installer/validation"))
import check_configuration as cc


pytestmark = [pytest.mark.local, pytest.mark.quick]


@pytest.mark.parametrize(
    ("version", "minimum", "expected"),
    [
        # The string-comparison bugs this replaces.
        ("0.14.0", (0, 8, 2), False),
        ("0.9.0", (0, 10, 0), True),
        ("v26.10.0", (26, 2, 0), False),
        # Ordinary ordering.
        ("v26.1.3", (26, 2, 0), True),
        ("v26.2.0", (26, 2, 0), False),
        ("v25.3.3", (25, 3, 3), False),
        ("v25.3.2", (25, 3, 3), True),
        # A pre-release counts as its release.
        ("v26.2.0-RC16", (26, 2, 0), False),
        # A floating tag counts as the newest release of that line.
        ("0.12", (0, 12, 2), False),
        ("v26.1", (26, 1, 0), False),
        # Two-part minimums.
        ("v26.1.0", (26, 1), False),
        ("v25.2.9", (25, 3), True),
    ],
)
def test_is_before(version, minimum, expected):
    """`_is_before` compares each part as a number, not as text."""
    assert cc._is_before(version, minimum) is expected


def test_is_before_unreadable_version_exits():
    """An unreadable version stops validation with an error instead of a traceback."""
    with pytest.raises(SystemExit):
        cc._is_before("latest", (0, 8, 2))


def _studios_data(**overrides) -> SimpleNamespace:
    """Minimal namespace for the Studios path-routing and SSH checks."""
    values = {
        "flag_enable_data_studio": True,
        "flag_studio_enable_path_routing": True,
        "flag_use_private_cacert": False,
        "tower_container_version": "v26.2.0-RC16",
        "data_studio_container_version": "0.14.0",
        "data_studio_path_routing_url": "connect.example.com",
        "flag_enable_data_studio_ssh": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_path_routing_accepts_connect_0_14_0():
    """Regression: Connect 0.14.0 (the template default) passes the 0.8.2 path-routing floor."""
    cc.verify_data_studio(_studios_data(data_studio_container_version="0.14.0"))


def test_path_routing_rejects_connect_0_8_1():
    """Connect below 0.8.2 still fails the path-routing check."""
    with pytest.raises(SystemExit):
        cc.verify_data_studio(_studios_data(data_studio_container_version="0.8.1"))


def test_kms_key_rejected_before_v26_2():
    """The KMS key check still fails on v26.1 and passes on the v26.2 release candidate."""
    with pytest.raises(SystemExit):
        cc.verify_pipeline_secrets_kms_key(
            SimpleNamespace(tower_aws_secrets_kms_key_id="mrk-" + "0" * 32, tower_container_version="v26.1.3")
        )
    cc.verify_pipeline_secrets_kms_key(
        SimpleNamespace(tower_aws_secrets_kms_key_id="mrk-" + "0" * 32, tower_container_version="v26.2.0-RC16")
    )
