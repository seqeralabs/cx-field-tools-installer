"""Tests for `verify_studios_private_ca` in `check_configuration.py`.

`flag_run_studios_via_private_ca` doesn't work in installer 1.9.0 (issue #460), so `make verify` rejects it.
The prerequisite checks stay in the code for when the feature is turned back on; the last tests keep them covered.
No Terraform or AWS calls.
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


def _ca_data(**overrides) -> SimpleNamespace:
    """A site that meets every prerequisite for the feature, with the flag on."""
    values = {
        "flag_run_studios_via_private_ca": True,
        "flag_use_private_cacert": True,
        "tower_container_version": "v26.2.1",
        "data_studio_container_version": "0.14.0",
        "data_studio_options": {},
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_flag_true_fails_while_disabled(caplog):
    """In 1.9.0, setting the flag to true stops `make verify` with the #460 error."""
    with pytest.raises(SystemExit):
        cc.verify_studios_private_ca(_ca_data())
    assert "#460" in caplog.text


def test_flag_false_passes():
    """Setting the flag to false passes."""
    cc.verify_studios_private_ca(_ca_data(flag_run_studios_via_private_ca=False))


def test_flag_missing_passes():
    """The template comments the flag out, so tfvars may not contain it at all. That counts as false."""
    data = _ca_data()
    del data.flag_run_studios_via_private_ca
    cc.verify_studios_private_ca(data)


def test_prerequisites_pass_when_reenabled(monkeypatch):
    """With the feature turned back on, a site that meets every prerequisite passes."""
    monkeypatch.setattr(cc, "STUDIOS_PRIVATE_CA_DISABLED", False)
    cc.verify_studios_private_ca(_ca_data())


@pytest.mark.parametrize(
    "overrides",
    [
        {"flag_use_private_cacert": False},
        {"tower_container_version": "v26.1.3"},
        {"data_studio_container_version": "0.12.1"},
    ],
)
def test_prerequisites_still_enforced_when_reenabled(monkeypatch, overrides):
    """With the feature turned back on, each missing prerequisite still stops `make verify`."""
    monkeypatch.setattr(cc, "STUDIOS_PRIVATE_CA_DISABLED", False)
    with pytest.raises(SystemExit):
        cc.verify_studios_private_ca(_ca_data(**overrides))
