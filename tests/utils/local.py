import re
import shutil
import subprocess
import sys
from pathlib import Path
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
from tests.utils.cache.cache import (
    create_templatefile_cache_folder,
    hash_tc_values,
)
from tests.utils.config import (
    FP,
    TCValues,
    all_template_files,
    kitchen_sink,
)
from tests.utils.filehandling import FileHelper
from tests.utils.terraform.parser import extract_config_values

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
## Helpers - Templatefile
## ------------------------------------------------------------------------------------


def replace_vars_in_templatefile(input_str, vars_dict, pattern) -> str:
    """
    Replace terraform references with actual values in templatefile string.

    Critical replacements: module.connection_strings.* and secrets
    Do not need to replace 'var.' or 'local.' since terraform console knows these.

    Args:
        input_str: Templatefile string from JSONified 009
        vars_dict: Dictionary of values to substitute
        type: Which terraform reference type to replace (e.g. "module.connection_strings")

    Example:
        Input:  "module.connection_strings.tower_db_url"
        Output: "jdbc:mysql://db:3306/tower"

    Note on regex capture groups:
        - Parentheses () in patterns create "capture groups" that extract specific parts
        - match.group(0) = entire match (e.g., "module.connection_strings.tower_db_url")
        - match.group(1) = first capture group (e.g., "tower_db_url")
    """
    patterns = {
        "module.connection_strings": r"module.connection_strings\.(\w+)",
        "tower_secrets": r'local\.tower_secrets\["([^"]+)"\]\["[^"]+"\]',
        "groundswell_secrets": r'local\.groundswell_secrets\["([^"]+)"\]\["[^"]+"\]',
        "seqerakit_secrets": r'local\.seqerakit_secrets\["([^"]+)"\]\["[^"]+"\]',
        "wave_lite_secrets": r'local\.wave_lite_secrets\["([^"]+)"\]\["[^"]+"\]',
        # Keeping these for future use if needed
        "tfvar": r"var\.(\w+)",
        "local": r"local\.(\w+)",
    }

    pattern = patterns.get(pattern)
    if not pattern:
        return "Error"

    def replace_match(match):
        """Convert Terraform primitives to Python equivalent (string / bool / number)."""
        var_name = match.group(1)  # Extract the variable name from the match
        if var_name in vars_dict:
            value = vars_dict[var_name]
            # Format the value correctly for terraform
            if isinstance(value, str):
                return f'"{value}"'  # Strings need quotes
            elif isinstance(value, bool):
                return str(value).lower()  # Booleans need lowercase
            else:
                return str(value)  # Numbers stay as-is
        return match.group(0)  # Keep original if not found

    return re.sub(pattern, replace_match, input_str)


def prepare_templatefile_payload(key, tc: TCValues):
    """
    Extract the templatefile command from JSONified 009, then sub values as necessary.

    BACKGROUND:
    A normal terraform plan/apply would have all the input values availabe at execution (this is SLOW).

    Instead, using the much faster 'terraform console' approach.
        - Console appears to have access to tfvars & locals, but not module outputs (emitted file is "known after apply").
        - As a result:
            - 1) Must run 'terraform plan' (full) once to generate all outputs (including of module outputs),
            - 2) Substitution in the templatefile string passed to 'terraform console'.
            - 3) Must add '\n' at end to not break the 'terraform console' subprocess call.
        - This feels Rube Goldberg-ish, but it gets test down from minutes to only seconds after first time cahcing.
    """
    templatefile_json = FileHelper.read_json("009_define_file_templates.json")
    # The hcl2json JSON conversion wraps the 'templatefile(...)' string we need with '${..}'.
    # Must remove wrapper or else it breaks 'terraform console'.
    payload = templatefile_json["locals"][0][key]
    payload = payload[2:-1]

    # Substitute values
    # Had to re-enable this for tower.sql but it breaks tower.env (the data_studio_options). Why?
    # result = replace_vars_in_templatefile(input_str, vars, "tfvar")
    # result = replace_vars_in_templatefile(result, outputs, "local")
    payload = replace_vars_in_templatefile(payload, tc.outputs, "module.connection_strings")
    payload = replace_vars_in_templatefile(payload, tc.tower_secrets, "tower_secrets")
    payload = replace_vars_in_templatefile(payload, tc.groundswell_secrets, "groundswell_secrets")
    payload = replace_vars_in_templatefile(payload, tc.seqerakit_secrets, "seqerakit_secrets")
    payload = replace_vars_in_templatefile(payload, tc.wave_lite_secrets, "wave_lite_secrets")
    payload = payload.replace("\n", "")  # MUST REMOVE NEW LINES OR CONSOLE CALL BREAKS.
    return payload


def write_populated_templatefile(outfile, payload):
    """
    Executes 'terraform console', passing in the specific templatefile and substituted payload.

    Example :
        > terraform console <<< 'templatefile("assets/src/ansible/06_run_seqerakit.yml.tpl",
            { app_name = "abc", flag_create_hosts_file_entry = false, flag_do_not_use_https = true })'

    NOTE:
        - 'terraform console' command needs single quotes on outside and double-quotes within.
        - 'terraform console' emits '<<EOT' and 'EOT' at start/finish of multi-line payload. These must be stripped.
    """
    # print(payload)
    payload = subprocess.run(
        ["terraform", "console"],
        input=str(payload),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    output = payload.stdout

    if output.startswith("<<EOT"):
        lines = output.splitlines()
        output = "\n".join(lines[1:-1])

    FileHelper.write_file(outfile, output)


def generate_templatefile(key, tc: TCValues, templatefile_cache_dir):
    """
    namespaces                  : SimpleNamespaced outputs of 'terrform plan'.
    templatefile_cache_dir     : Relies on the hash of all the tfvars files used for the specific testcase.
    key                         : key from JSONified 009
    """

    # Hash templatefiles to speed up n+1 tests
    #   - If cache miss, emit generated files as <CACHE_VALUE>_<FILENAME> and stick in 'tests/.templatfile_cache'.
    extension = all_template_files[key]["extension"]
    read_type = all_template_files[key]["read_type"]

    # Check cache location. If check miss, generate file and place in cache. Read and return (now) cached file.
    outfile = Path(f"{templatefile_cache_dir}/{key}{extension}")
    if not outfile.exists():
        result = prepare_templatefile_payload(key, tc)
        write_populated_templatefile(outfile, result)

    return read_type(outfile.as_posix())


def _is_sql_file(key: str) -> bool:
    """
    Check if file needs special SQL handling (can't use terraform console).

    SQL files with postgres single-quotes break terraform console input parsing.
    """
    # TODO: Move this to all_template_files as a discrete flag
    sql_exception_files = ["wave_lite_rds"]
    return key in sql_exception_files


def _generate_regular_templatefile(
    key: str, config: dict, tc: TCValues, cache_dir: str, template_files: dict
) -> None:
    """
    Generate template using terraform console.

    Args:
        key: Template identifier (e.g., "tower_env")
        config: Template configuration from all_template_files
        tc: Test case values (vars, outputs, secrets)
        cache_dir: Directory for cached template files
        template_files: Dictionary to update with generated content (modified in-place)
    """
    content = generate_templatefile(key, tc, cache_dir)
    template_files[key]["content"] = content
    template_files[key]["filepath"] = f"{cache_dir}/{key}{config['extension']}"


def _generate_sql_templatefile(key: str, cache_dir: str, template_files: dict) -> None:
    """
    Generate SQL template using Python script substitution.

    SQL files can't use terraform console because postgres uses single-quotes
    which break the console input parsing.

    Args:
        key: Template identifier (e.g., "wave_lite_rds")
        cache_dir: Directory for cached template files
        template_files: Dictionary to update with generated content (modified in-place)
    """
    source_dir = Path(f"{FP.ROOT}/assets/src/wave_lite_config/")
    script_path = f"{FP.ROOT}/scripts/installer/utils/sedalternative.py"

    # Copy SQL source files to cache
    for sql_file in source_dir.glob("*.sql"):
        shutil.copy(sql_file, cache_dir)

    # Run substitution script
    # TODO: Make credentials configurable instead of hardcoded
    command = (
        f"python3 {script_path} "
        f"wave_lite_test_limited "
        f"wave_lite_test_limited_password "
        f"{cache_dir}"
    )
    subprocess.run(command, shell=True, text=True, capture_output=False, check=True)

    # Read generated file
    template_files[key]["content"] = FileHelper.read_file(f"{cache_dir}/wave-lite-rds.sql")
    template_files[key]["filepath"] = f"{cache_dir}/wave-lite-rds.sql"


def generate_templatefiles(tc: TCValues, template_files: dict, testcase_name: str) -> dict:
    """
    Create templatefiles relevant to the testcase.

    Delegates to specialized handlers based on file type:
        - Regular templates: terraform console rendering
        - SQL templates: Python script substitution

    Args:
        tc: Test case values (vars, outputs, secrets)
        template_files: Templates to generate (from filter_templates)
        testcase_name: Name of test case for cache directory

    Returns:
        Updated template_files dict with content and filepath added
    """
    cache_dir = create_templatefile_cache_folder(tc, testcase_name)

    for key, config in template_files.items():
        if _is_sql_file(key):
            _generate_sql_templatefile(key, cache_dir, template_files)
        else:
            _generate_regular_templatefile(key, config, tc, cache_dir, template_files)

    return template_files


def generate_tc_files(plan, desired_files, testcase_name):
    """
    - Generates namespaced dictionaries.
    - Generates scenario hash.
    - Generates and returns necessary template files
    """
    TC: TCValues = extract_config_values(plan)
    needed_template_files: dict = filter_templates(desired_files)
    tc_files = generate_templatefiles(TC, needed_template_files, testcase_name)

    return tc_files


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
