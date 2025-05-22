from types import SimpleNamespace

from installer.utils.extractors import tf_vars_json_payload

data_dictionary = tf_vars_json_payload
data = SimpleNamespace(**data_dictionary)


def test_tfvars_app_name():
    assert data.app_name == "tower-dev"
