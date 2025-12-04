import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
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


def replace_vars_in_templatefile(input_str, vars_dict, type) -> str:
    """
    Replace terraform references with actual values in templatefile string.

    Critical replacements: module.connection_strings.* and secrets
    Do not need to replace 'var.' or 'local.' since terraform console knows these.

    Args:
        input_str: Templatefile string from JSONified 009
        vars_dict: Dictionary of values to substitute
        type: Prefix pattern to match (e.g. "module.connection_strings")
    """

    def replace_var(match):
        var_name = match.group(1)
        if var_name in vars_dict:
            value = vars_dict[var_name]
            if isinstance(value, str):
                return f'"{value}"'
            elif isinstance(value, bool):
                return str(value).lower()
            else:
                return str(value)
        return match.group(0)  # Return original if not found

    # The regex re.sub() function handles the "looping" automatically. Finds all matches of the defined pattern in the string
    # and calls the replace_var function for each.
    if type == "module.connection_strings":
        pattern = r"module.connection_strings\.(\w+)"
        return re.sub(pattern, replace_var, input_str)

    elif type == "tower_secrets":
        pattern = r'local\.tower_secrets\["([^"]+)"\]\["[^"]+"\]'
        return re.sub(pattern, replace_var, input_str)

    elif type == "groundswell_secrets":
        pattern = r'local\.groundswell_secrets\["([^"]+)"\]\["[^"]+"\]'
        return re.sub(pattern, replace_var, input_str)

    elif type == "seqerakit_secrets":
        pattern = r'local\.seqerakit_secrets\["([^"]+)"\]\["[^"]+"\]'
        return re.sub(pattern, replace_var, input_str)

    elif type == "wave_lite_secrets":
        pattern = r'local\.wave_lite_secrets\["([^"]+)"\]\["[^"]+"\]'
        return re.sub(pattern, replace_var, input_str)

    # Keeping these in just-in-case they are ever needed in future
    elif type == "tfvar":
        pattern = r"var\.(\w+)"
        return re.sub(pattern, replace_var, input_str)

    elif type == "local":
        pattern = r"local\.(\w+)"
        return re.sub(pattern, replace_var, input_str)
    else:
        return "Error"


def sub_templatefile_inputs(input_str, namespaces):
    """
    Helper function that does the actual subsituation of the values in the JSONified 009 templatefile payload.
    """

    # BACKGROUND:
    # I'm sourcing the templatefile string directly from 009. A normal plan/apply would have all the input values availabe at execution.
    # This is slow, however, so I'm trying to use the much faster 'terraform console' approach. Console appears to have access to 'tfvars'
    # and necessary 'locals', but not to the outputs of called modules (emitted file is "known after apply").
    #
    # To make this work, I need to run a 'terraform plan' (full) to generate all outputs (inclusive of module outputs), which can then
    # be used for substitution in the templatefile string passed by 'terraform console'. This feels like a Rube Goldberg, but it gets
    # test execution down from 30+ seconds (everytime) to ~4 seconds (first time, cacheable).
    #
    # TBD what happens with secrets
    #
    # '\n' must be replace in  the extracted 009 payload so it can be passed to 'terraform console' via subprocess call.

    (
        vars,
        outputs,
        tower_secrets,
        groundswell_secrets,
        seqerakit_secrets,
        wave_lite_secrets,
    ) = namespaces

    # Had to re-enable this for tower.sql but it breaks tower.env (the data_studio_options). Why?
    # result = replace_vars_in_templatefile(input_str, vars, "tfvar")
    # result = replace_vars_in_templatefile(result, outputs, "local")
    result = replace_vars_in_templatefile(input_str, outputs, "module.connection_strings")
    result = replace_vars_in_templatefile(result, tower_secrets, "tower_secrets")
    result = replace_vars_in_templatefile(result, groundswell_secrets, "groundswell_secrets")
    result = replace_vars_in_templatefile(result, seqerakit_secrets, "seqerakit_secrets")
    result = replace_vars_in_templatefile(result, wave_lite_secrets, "wave_lite_secrets")
    result = result.replace("\n", "")  # MUST REMOVE NEW LINES OR CONSOLE CALL BREAKS.
    # TODO: Figure out secrets

    return result


def prepare_templatefile_payload(key, namespaces):
    """
    Execute the templatefile command from JSONified 009, then sub in necessary values for SimpleNamespaced
    terraform plan outputs.
    """
    templatefile_json = FileHelper.read_json("009_define_file_templates.json")
    # The hcl2json conversion of 009 to JSON wraps the 'templatefile(...)' string we need with '${..}'.
    # The wrapper needs to be removed or else it breaks 'terraform console'.
    payload = templatefile_json["locals"][0][key]
    payload = payload[2:-1]
    payload = sub_templatefile_inputs(payload, namespaces)
    return payload


def write_populated_templatefile(outfile, payload):
    """
    Example of how this calls 'terraform console':
        > terraform console <<< 'templatefile("assets/src/ansible/06_run_seqerakit.yml.tpl", { app_name = "abc", flag_create_hosts_file_entry = false, flag_do_not_use_https = true })'

    'terraform console' command needs single quotes on outside and double-quotes within.
    """
    print(payload)
    payload = subprocess.run(
        ["terraform", "console"],
        input=str(payload),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    output = payload.stdout

    # Strip '<<EOT' and 'EOT' appending to start and end of multi-line payload emitted by 'terraform console'.
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


def generate_templatefiles(tc, template_files, testcase_name):
    """
    Create templatefiles relevant to the testcase.
    NOTE:
        - Some files like 'wave_lite_rds' file cant be processed as a '.tpl' due to single-quotes in the content.
        - Must use alternative approach to handle.
    """
    templatefile_cache_dir = create_templatefile_cache_folder(tc, testcase_name)

    # TODO: Put this over onto all_template_files as discrete flag.
    sql_exception_files = ["wave_lite_rds"]

    # Step 1 -- Generate any file that can be done so normally (i.e. not SQL files)
    for k, v in template_files.items():
        if k in sql_exception_files:
            continue

        # Retrieve cached file / generate new file (and cache). Add payload and filepath to 'template_files'.
        content = generate_templatefile(k, tc, templatefile_cache_dir)
        template_files[k]["content"] = content
        template_files[k]["filepath"] = f"{templatefile_cache_dir}/{k}{v['extension']}"

    # Step 2 -- Generate edgecases that could be generated normally.
    if any(k in template_files.keys() for k in sql_exception_files):
        source_dir = Path(f"{FP.ROOT}/assets/src/wave_lite_config/")
        script_path = f"{FP.ROOT}/scripts/installer/utils/sedalternative.py"

        for sql_file in source_dir.glob("*.sql"):
            shutil.copy(sql_file, templatefile_cache_dir)

        # Hardcoded -- not sure I love this.
        command = (
            f"python3 {script_path} wave_lite_test_limited wave_lite_test_limited_password {templatefile_cache_dir}"
        )
        subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=False,
        )

        template_files["wave_lite_rds"]["content"] = FileHelper.read_file(f"{templatefile_cache_dir}/wave-lite-rds.sql")
        template_files["wave_lite_rds"]["filepath"] = f"{templatefile_cache_dir}/wave-lite-rds.sql"

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
