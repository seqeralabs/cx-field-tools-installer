from types import SimpleNamespace

from installer.utils.extractors import get_tfvars_as_json

data_dictionary = get_tfvars_as_json()
data = SimpleNamespace(**data_dictionary)


def test_tfvars_app_name():
    assert data.app_name == "tower-dev"
