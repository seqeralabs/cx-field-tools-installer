import sys
from types import SimpleNamespace

# https://gist.github.com/lsloan/dedd22cb319594f232155c37e280ebd7
from yamlpath import Processor, YAMLPath
from yamlpath.common import Parsers
from yamlpath.exceptions import UnmatchedYAMLPathException
from yamlpath.wrappers import ConsolePrinter, NodeCoords

from tests.utils.assertions.file_filters import filter_templates
from tests.utils.assertions.file_handlers import (
    assert_kv_key_omitted,
    assert_kv_key_present,
    assert_yaml_key_omitted,
    assert_yaml_key_present,
)

loggingArgs = SimpleNamespace(quiet=True, verbose=False, debug=False)
logger = ConsolePrinter(loggingArgs)
yamlParser = Parsers.get_yaml_editor()


"""
EXPLANATION
=======================================
Originally tried using [tftest](https://pypi.org/project/tftest/). Too complicated and abstract IMO. Now using simpler methodology:

1. Test in the project directory.
2. Take a backup of the existing `terraform.tfvars` file.
3. Create a new testing artifacts:
    - Core (via `tests/datafiles/generate_core_data.sh`):
        - `terraform.tfvars` generate from `templates/TEMPLATE_terraform.tfvars.
        - `base-overrides.auto.tfvars` to generate REPLACE_ME substitutions and set some values for faster baseline testing.
    - Testcase:
        - Generate a new `override.auto.tfvars` file in the project root based on necessary overrides for each test.
        - Terraform lexical hierarchy means this file trumps same settings in core files.
4. Run tests:
    1. For each test case, run `terraform plan` using test tfvars and override files. 
    2. Run assertions.
    NOTE: Results cached when possible (i.e. local) to speed up n+1 test runs. Not always feasible with apply-type tests.

5. When tests are complete:
    - Purge tfvars and override files.
    - Restore the original `terraform.tfvars` to project root.
"""


## ------------------------------------------------------------------------------------
## Helpers - Assertions
## ------------------------------------------------------------------------------------


def assert_present_and_omitted(entries: dict, file, type=None):
    """
    Confirm present & omitted key.
    Must account for differences
    """

    if type == "yml":
        assert_yaml_key_present(entries["present"], file)
        assert_yaml_key_omitted(entries["omitted"], file)
    elif type == "sql":
        # DO NOT USE THIS LOGIC BRANCH - SQL IS NOW VALIDATED ANOTHER WAY.
        # assert_sql_key_present(entries["present"], file)
        # assert_sql_key_omitted(entries["omitted"], file)
        pass
    elif type == "kv":
        assert_kv_key_present(entries["present"], file)
        assert_kv_key_omitted(entries["omitted"], file)
    else:
        # raise ValueError(f"Expected type to be in 'yml', 'sql', or 'kv'], got '{type}'")
        pass


def verify_all_assertions(tc_files, tc_assertions):
    """Use the keyset of the testcase files to control which asserttions are used (for limited & kitchen sink)."""
    for k, v in tc_files.items():
        print(f"Testing {sys._getframe().f_code.co_name}.{k}.")
        content = v["content"]
        validation_type = v["validation_type"]
        assertions = tc_assertions[k]
        assert_present_and_omitted(assertions, content, validation_type)
