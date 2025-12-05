import sys
from types import SimpleNamespace

import pytest
import yaml

# https://gist.github.com/lsloan/dedd22cb319594f232155c37e280ebd7
from yamlpath import Processor, YAMLPath
from yamlpath.common import Parsers
from yamlpath.exceptions import UnmatchedYAMLPathException
from yamlpath.wrappers import ConsolePrinter, NodeCoords

loggingArgs = SimpleNamespace(quiet=True, verbose=False, debug=False)
logger = ConsolePrinter(loggingArgs)
yamlParser = Parsers.get_yaml_editor()


## ------------------------------------------------------------------------------------
## Assertion Helpers - Handles Different Filetypes
## ------------------------------------------------------------------------------------
def assert_kv_key_present(entries: dict, file):
    """Confirm key-values in provided dict are present in file."""
    for k, v in entries.items():
        try:
            assert file[k] == str(v), f"Key {k} sought but not found."
        except AssertionError as e:
            pytest.fail(f"Assertion failed for {k}: {str(e)}")


def assert_kv_key_omitted(entries: dict, file):
    """Confirm keys in provided dict are not present in file."""
    keys = file.keys()

    for k in entries.keys():
        assert k not in keys, f"Key {k} should not be present but was found."


def assert_yaml_key_present(entries: dict, file):
    """
    Confirm key-values in provided dict are present in file. WARNING -- THIS IS UGLY.
    Uses 3rd party library. Acceptable since testing is only essential to Seqera staff.
    Found necessary code implementation at: https://gist.github.com/lsloan/dedd22cb319594f232155c37e280ebd7
    """

    # file content is passes as a dictionary, I need to write out yaml
    with open("/tmp/cx-testing-yml", "w") as f:
        yaml.dump(file, f)

    # https://gist.github.com/lsloan/dedd22cb319594f232155c37e280ebd7
    (yamlData, documentLoaded) = Parsers.get_yaml_data(yamlParser, logger, "/tmp/cx-testing-yml")
    if not documentLoaded:
        exit(1)
    processor = Processor(logger, yamlData)

    for k, v in entries.items():
        try:
            # https://gist.github.com/lsloan/dedd22cb319594f232155c37e280ebd7
            dataYamlPath = YAMLPath(k)
            for nodeCoordinate in processor.get_nodes(dataYamlPath, mustexist=True):
                nodeData = NodeCoords.unwrap_node_coords(nodeCoordinate)
                print(f"yaml_key{k}")
                print(f"nodeData={str(nodeData)}")
                assert str(nodeData) == str(v), f"Key {k} does not match Value {v}."
        except AssertionError as e:
            pytest.fail(f"Assertion failed for {k}: {str(e)}")


def assert_yaml_key_omitted(entries: dict, file):
    """
    Confirm keys in provided are not present in YAML file. Assumes you'll base <PATH>.keys() as v.
    Uses 3rd party library. Acceptable since testing is only essential to Seqera staff.
    Found necessary code implementation at: https://gist.github.com/lsloan/dedd22cb319594f232155c37e280ebd7"""

    # file content is passes as a dictionary, I need to write out yaml
    with open("/tmp/cx-testing-yml", "w") as f:
        yaml.dump(file, f)

    # https://gist.github.com/lsloan/dedd22cb319594f232155c37e280ebd7
    (yamlData, documentLoaded) = Parsers.get_yaml_data(yamlParser, logger, "/tmp/cx-testing-yml")
    if not documentLoaded:
        exit(1)
    processor = Processor(logger, yamlData)

    # This one is a bit odd because of how the library works. I WANT to have Exceptions raised when trying to find the YAMLPath
    # (i.e. path doesnt exist). The most concise code block avoids try/except but doesn't identify an key that actually does exist.
    # Using slightly more convoluted code.
    for k, v in entries.items():
        dataYamlPath = YAMLPath(k)
        with pytest.raises(UnmatchedYAMLPathException):
            list(processor.get_nodes(dataYamlPath, mustexist=True))


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
