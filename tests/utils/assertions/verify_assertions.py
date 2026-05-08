import os
import sys
import tempfile
from types import SimpleNamespace

import pytest
import yaml

# https://gist.github.com/lsloan/dedd22cb319594f232155c37e280ebd7
from yamlpath import Processor, YAMLPath
from yamlpath.common import Parsers
from yamlpath.exceptions import UnmatchedYAMLPathException
from yamlpath.wrappers import ConsolePrinter, NodeCoords


logging_args = SimpleNamespace(quiet=True, verbose=False, debug=False)
logger = ConsolePrinter(logging_args)
yaml_parser = Parsers.get_yaml_editor()


## ------------------------------------------------------------------------------------
## Assertion Helpers - Handles Different Filetypes
## ------------------------------------------------------------------------------------
def assert_kv_key_present(entries: dict, file):
    """Confirm key-values in provided dict are present in file."""
    for k, v in entries.items():
        try:
            assert file[k] == str(v), f"Key {k} sought but not found."
        except AssertionError as e:
            pytest.fail(f"Assertion failed for {k}: {e!s}")


def assert_kv_key_omitted(entries: dict, file):
    """Confirm keys in provided dict are not present in file."""
    keys = file.keys()

    for k in entries:
        assert k not in keys, f"Key {k} should not be present but was found."


def assert_yaml_key_present(entries: dict, file):
    """Confirm key-values in provided dict are present in YAML file.

    WARNING -- this is ugly. Uses a 3rd party library; acceptable since testing
    is only essential to Seqera staff.
    Reference: https://gist.github.com/lsloan/dedd22cb319594f232155c37e280ebd7
    """
    # file content is passes as a dictionary, I need to write out yaml
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as tmp:
        yaml.dump(file, tmp)
        tmp_path = tmp.name

    try:
        # https://gist.github.com/lsloan/dedd22cb319594f232155c37e280ebd7
        (yaml_data, document_loaded) = Parsers.get_yaml_data(yaml_parser, logger, tmp_path)
        if not document_loaded:
            sys.exit(1)
        processor = Processor(logger, yaml_data)

        for k, v in entries.items():
            try:
                # https://gist.github.com/lsloan/dedd22cb319594f232155c37e280ebd7
                data_yaml_path = YAMLPath(k)
                for node_coordinate in processor.get_nodes(data_yaml_path, mustexist=True):
                    node_data = NodeCoords.unwrap_node_coords(node_coordinate)
                    print(f"yaml_key{k}")
                    print(f"nodeData={node_data!s}")
                    assert str(node_data) == str(v), f"Key {k} does not match Value {v}."
            except AssertionError as e:
                pytest.fail(f"Assertion failed for {k}: {e!s}")
    finally:
        os.unlink(tmp_path)


def assert_yaml_key_omitted(entries: dict, file):
    """Confirm keys in provided dict are not present in YAML file.

    Assumes you'll pass <PATH>.keys() as v. Uses a 3rd party library; acceptable
    since testing is only essential to Seqera staff.
    Reference: https://gist.github.com/lsloan/dedd22cb319594f232155c37e280ebd7
    """
    # file content is passes as a dictionary, I need to write out yaml
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as tmp:
        yaml.dump(file, tmp)
        tmp_path = tmp.name

    try:
        # https://gist.github.com/lsloan/dedd22cb319594f232155c37e280ebd7
        (yaml_data, document_loaded) = Parsers.get_yaml_data(yaml_parser, logger, tmp_path)
        if not document_loaded:
            sys.exit(1)
        processor = Processor(logger, yaml_data)

        # This one is a bit odd because of how the library works. I WANT to have Exceptions raised
        # when trying to find the YAMLPath (i.e. path doesnt exist). The most concise code block
        # avoids try/except but doesn't identify an key that actually does exist. Using slightly more
        # convoluted code.
        for k in entries:
            data_yaml_path = YAMLPath(k)
            with pytest.raises(UnmatchedYAMLPathException):
                list(processor.get_nodes(data_yaml_path, mustexist=True))
    finally:
        os.unlink(tmp_path)


## ------------------------------------------------------------------------------------
## Helpers - Meta-level
## ------------------------------------------------------------------------------------


def verify_all_assertions(tc_files, tc_assertions):
    """Cycle through all in-scope template files and run related assertions."""
    for k, v in tc_files.items():
        print(f"Testing {sys._getframe().f_code.co_name}.{k}.")

        content = v["content"]
        validation_type = v["validation_type"]
        assertions = tc_assertions[k]

        # assert_present_and_omitted(assertions, content, validation_type)
        match validation_type:
            case "yml":
                assert_yaml_key_present(assertions["present"], content)
                assert_yaml_key_omitted(assertions["omitted"], content)
            case "kv":
                assert_kv_key_present(assertions["present"], content)
                assert_kv_key_omitted(assertions["omitted"], content)
            case "sql":
                # DO NOT USE THIS LOGIC BRANCH - SQL IS NOW VALIDATED ANOTHER WAY.
                pass
            case _:
                # raise ValueError(f"Expected type to be in 'yml', 'sql', or 'kv'], got '{type}'")
                pass
