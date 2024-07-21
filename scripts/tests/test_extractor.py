import sys
from types import SimpleNamespace

sys.dont_write_bytecode = True

from installer.utils.extractors import get_tfvars_as_json

data_dictionary = get_tfvars_as_json()
data = SimpleNamespace(**data_dictionary)


def test_tfvars_app_name():
    assert data.app_name == "tower-dev"
