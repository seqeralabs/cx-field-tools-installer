from types import SimpleNamespace

from scripts.installer.data_external.generate_db_connection_string import (
    MYSQL8_CONNSTRING,
    V24PLUS_CONNSTRING,
    generate_connection_string,
)

# Not required - with testing we are faking things out. Testing in remote repo won't have access to
# a tfvars file.
# from installer.utils.extractors import get_tfvars_as_json
# data_dictionary = get_tfvars_as_json()
# data = SimpleNamespace(**data_dictionary)

BLANK_CONNSTRING = ""

KEYS = [
    "tower_container_version",
    "flag_use_container_db",
    "db_container_engine_version",
    "db_engine_version",
    "expected",
]

TEST_MATRIX = [
    # Container DB section
    ["v23.1.3", True, "5.7", "8.0", BLANK_CONNSTRING],
    ["v23.1.3", True, "8.0", "5.7", f"?{MYSQL8_CONNSTRING}"],
    ["v24.0.0", True, "8.0", "5.7", f"?{MYSQL8_CONNSTRING}&{V24PLUS_CONNSTRING}"],
    # RDS Section
    ["v23.1.3", False, "8.0", "5.7", BLANK_CONNSTRING],
    ["v23.1.3", False, "5.7", "8.0", f"?{MYSQL8_CONNSTRING}"],
    ["v24.0.0", False, "5.7", "8.0", f"?{MYSQL8_CONNSTRING}&{V24PLUS_CONNSTRING}"],
]


def test_db_connstrings():
    for values in TEST_MATRIX:
        data_dictionary = dict(zip(KEYS, values))
        data = SimpleNamespace(**data_dictionary)
        connstring = generate_connection_string(data)
        assert connstring == data.expected
