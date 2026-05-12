from pathlib import Path
from types import SimpleNamespace

from installer.utils.extractors import get_tfvars_as_json
import pytest


TEMPLATE_TFVARS = str(Path(__file__).resolve().parents[2] / "templates" / "TEMPLATE_terraform.tfvars")


@pytest.fixture(scope="module")
def data():
    """Load tfvars from the TEMPLATE file. Lazy so import-time pytest collection doesn't fire Docker."""
    return SimpleNamespace(**get_tfvars_as_json(TEMPLATE_TFVARS))


def test_tfvars_app_name(data):
    assert data.app_name == "tower-template"
