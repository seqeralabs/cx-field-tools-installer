from pathlib import Path
import platform
from types import SimpleNamespace

from installer.utils.extractors import (
    HCL2JSON_BIN,
    _can_use_binary,
    _is_supported_extraction_platform,
    get_tfvars_as_json,
)
import pytest


TEMPLATE_TFVARS = str(Path(__file__).resolve().parents[2] / "templates" / "TEMPLATE_terraform.tfvars")


@pytest.fixture(scope="module")
def data():
    """Load tfvars from the TEMPLATE file. Lazy so import-time pytest collection doesn't fire Docker."""
    return SimpleNamespace(**get_tfvars_as_json(TEMPLATE_TFVARS))


def test_tfvars_app_name(data):
    assert data.app_name == "tower-template"


## ------------------------------------------------------------------------------------
## Phase 1 of #352: smoke tests for the extracted-binary dispatch path.
## ------------------------------------------------------------------------------------
def test_supported_platform_predicate_returns_bool():
    """`_is_supported_extraction_platform()` must always answer True/False — never raise."""
    assert isinstance(_is_supported_extraction_platform(), bool)


@pytest.mark.skipif(
    not (platform.system() == "Linux" and platform.machine() == "x86_64"),
    reason="Phase 1 of #352 only covers linux/amd64; other hosts use the docker fallback.",
)
def test_extracted_binary_is_used_on_supported_platform():
    """On linux/amd64 after `make extract_hcl2json` has run, the binary path should be active.

    Encodes the contract from #352: every `make run_tests_*` recipe pulls `extract_hcl2json`
    in first, so by the time pytest is collecting these tests the binary should exist at
    `HCL2JSON_BIN`. A failure here means either (a) the recipe didn't run (e.g. pytest was
    invoked directly, without `make`), or (b) extraction itself broke.
    """
    assert Path(HCL2JSON_BIN).is_file(), (
        f"Expected extracted hcl2json binary at {HCL2JSON_BIN}. "
        "Run `make extract_hcl2json` (or any `make run_tests_*` / `make verify`) first."
    )
    assert _can_use_binary() is True
