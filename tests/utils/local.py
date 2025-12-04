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

from tests.utils.assertions.file_handlers import (
    assert_kv_key_omitted,
    assert_kv_key_present,
    assert_yaml_key_omitted,
    assert_yaml_key_present,
)
from tests.utils.config import (
    FP,
    all_template_files,
    kitchen_sink,
    secrets_dir,
)
from tests.utils.filehandling import FileHelper

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
def generate_namespaced_dictionaries(plan: dict) -> tuple:
    """
    Converts JSONified terraform plan into easier-to-use SimpleNamespace.

    WARNING!!!!!!
      - Plan keys are in Python dictionary form, so JSON "true" becomes True.  AFFECTS: `outputs` and `vars`
      - Config file values are directly cracked from HCL so they are "true".
    """

    vars_dict = plan["variables"]
    outputs_dict = plan["planned_values"]["outputs"]

    with open(f"{secrets_dir}/ssm_sensitive_values_tower_testing.json", "r") as f:
        tower_secrets = json.load(f)

    with open(f"{secrets_dir}/ssm_sensitive_values_groundswell_testing.json", "r") as f:
        groundswell_secrets = json.load(f)

    with open(f"{secrets_dir}/ssm_sensitive_values_seqerakit_testing.json", "r") as f:
        seqerakit_secrets = json.load(f)

    with open(f"{secrets_dir}/ssm_sensitive_values_wave_lite_testing.json", "r") as f:
        wave_lite_secrets = json.load(f)

    # https://dev.to/taqkarim/extending-simplenamespace-for-nested-dictionaries-58e8
    # Avoids noisy dict notation ([""]) and constant repetition of `.value`.
    # Variables have only one key (values); outputs may have 3 keys (sensitive, type, value).
    # Example: `vars.tower_contact_email`
    vars_flattened = {k: v.get("value", v) for k, v in vars_dict.items()}
    outputs_flattened = {k: v.get("value", v) for k, v in outputs_dict.items()}

    tower_secrets_flattened = {k: v.get("value", v) for k, v in tower_secrets.items()}
    groundswell_secrets_flattened = {k: v.get("value", v) for k, v in groundswell_secrets.items()}
    seqerakit_secrets_flattened = {k: v.get("value", v) for k, v in seqerakit_secrets.items()}
    wave_lite_secrets_flattened = {k: v.get("value", v) for k, v in wave_lite_secrets.items()}

    """
    Only namespace the top level, preserve nested dictionaries as regular dicts
    Problem is that nested values like data_studios_options show up like:
    vscode-1-101-2-0-8-5=namespace(container='public.cr.seqera.io/platform/data-studio-vscode:1.101.2-0.8.5', icon='vscode', qualifier='VSCODE-1-101-2-0-8-5', status='recommended', tool='vscode')
    and this breaks the 'terraform console' template submission
    """
    # vars = json.loads(json.dumps(vars_flattened), object_hook=lambda item: SimpleNamespace(**item))
    # outputs = json.loads(json.dumps(outputs_flattened), object_hook=lambda item: SimpleNamespace(**item))
    vars = SimpleNamespace(**vars_flattened)
    outputs = SimpleNamespace(**outputs_flattened)

    tower_secrets_sn = SimpleNamespace(**tower_secrets_flattened)
    groundswell_secrets_sn = SimpleNamespace(**groundswell_secrets_flattened)
    seqerakit_secrets_sn = SimpleNamespace(**seqerakit_secrets_flattened)
    wave_lite_secrets_sn = SimpleNamespace(**wave_lite_secrets_flattened)

    # Group into two lists to make return disaggregation easier
    return (
        [vars, outputs, vars_dict, outputs_dict],
        [
            tower_secrets_sn,
            groundswell_secrets_sn,
            seqerakit_secrets_sn,
            wave_lite_secrets_sn,
        ],
    )


def replace_vars_in_templatefile(input_str, vars_obj, type) -> str:
    """
    This function uses the SimpleNamespace emitted by 'generate_namespaced_dictionaries' and used them to
    replace necessary values in the 'templatefile' command extracted from a JSONified 009 file.

    Critical replacements are outputs of 'module.connection_string' & secrets values.
    Do not need to replace 'var.' or 'local.' since these are known when 'terraform console' invoked.

    input_str : The value of a key extracted from JSONified 009_define_file_templates.tf
    vars_obj  : The SimpleNamespace object returned by generate_namespaced_dictionaries()
    type      : The prefix we are looking to replace.

    NOTE: This relies upon the emission of TF Locals values during testing via an extra outputs file definition
    (created by tests/datafiles/generate_core_data.sh)
    """

    # This part a bit magical, from Claude: Here's how it works:
    # 1. re.sub(pattern, replace_var, input_str) finds every occurrence of var.something
    # 2. For each match, it calls replace_var(match)
    # 3. replace_var extracts the variable name and returns the replacement value
    # 4. re.sub substitutes each match with the returned value
    # So for your input string, it will automatically find and replace var.app_name, var.flag_create_hosts_file_entry, and var.flag_do_not_use_https in a single call.

    def replace_var(match):
        try:
            var_name = match.group(1)
            if hasattr(vars_obj, var_name):
                value = getattr(vars_obj, var_name)
                if isinstance(value, str):
                    return f'"{value}"'
                elif isinstance(value, bool):
                    return str(value).lower()
                else:
                    return str(value)
        except IndexError:
            return match.group(0)  # Return original if var not found

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


def generate_interpolated_templatefile(key, extension, read_type, namespaces, cache_templatefile_hash):
    """
    namespaces                  : SimpleNamespaced outputs of 'terrform plan'.
    cache_templatefile_hash     : Relies on the hash of all the tfvars files used for the specific testcase.
    key                         : key from JSONified 009
    extension                   : Proper file output
    read_type                   : Which utility helper to use to load the resulting file.
    """

    # Hash templatefiles to speed up n+1 tests
    #   1) Generate hash of tfvars variables and do cache check to speed this up.
    #   2) If cache miss, emit generated files as <CACHE_VALUE>_<FILENAME> and stick in 'tests/.templatfile_cache'.
    outfile = Path(f"{cache_templatefile_hash}/{key}{extension}")
    if not outfile.exists():
        result = prepare_templatefile_payload(key, namespaces)
        write_populated_templatefile(outfile, result)

    content = read_type(outfile.as_posix())
    return content


def generate_interpolated_templatefiles(hash, namespaces, template_files, testcase_name):
    """
    Create all templatefiles based on terraform values relevant to the specific testcase.

    I don't seem able to put the file cache dir as a top-level key, so adding in to the dictionary for each individual file.
    """
    # Make cache folder if missing
    cache_templatefile_hash = f"{FP.CACHE_TEMPLATEFILE_DIR}/{testcase_name}__{hash}"
    folder_path = Path(cache_templatefile_hash)
    folder_path.mkdir(parents=True, exist_ok=True)

    # Can't include a timestamp in the name since this will mess up the caching check in `generate_interpolated_templatefile`.
    # Write timestamp in the folder instead -- add to filename for easy reference & inside file to make Path write mechanics happy.
    existing_timestamps = list(folder_path.glob(".timestamp*"))
    if not existing_timestamps:
        timestamp = datetime.now().strftime("%Y-%m-%d--%H:%M:%S")
        timestamp_file = folder_path / f".timestamp--{timestamp}"
        timestamp_file.write_text(timestamp)

    sql_exception_files = ["wave_lite_rds"]

    for k, v in template_files.items():
        if k in sql_exception_files:
            continue
        content = generate_interpolated_templatefile(
            k, v["extension"], v["read_type"], namespaces, cache_templatefile_hash
        )
        template_files[k]["content"] = content
        template_files[k]["filepath"] = f"{cache_templatefile_hash}/{k}{v['extension']}"

    # Edgecase: Wave-Lite SQL (not .tpl due to postgres single-quote needs).
    # Cant use `terraform template`. Use copy and conversion method instead.
    if any(k in template_files.keys() for k in sql_exception_files):
        source_dir = Path(f"{FP.ROOT}/assets/src/wave_lite_config/")
        script_path = f"{FP.ROOT}/scripts/installer/utils/sedalternative.py"

        for sql_file in source_dir.glob("*.sql"):
            shutil.copy(sql_file, cache_templatefile_hash)

        # Hardcoded -- not sure I love this.
        command = (
            f"python3 {script_path} wave_lite_test_limited wave_lite_test_limited_password {cache_templatefile_hash}"
        )
        subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=False,
        )

        template_files["wave_lite_rds"]["content"] = FileHelper.read_file(
            f"{cache_templatefile_hash}/wave-lite-rds.sql"
        )
        template_files["wave_lite_rds"]["filepath"] = f"{cache_templatefile_hash}/wave-lite-rds.sql"

    # Add hash to returned dict to make it easier to mount files directly rather than use tempfile
    # This messes up things re string indicies for reasons I dont understand.
    # template_files["cache_templatefile_hash"] = f"{cache_templatefile_hash}"

    return template_files


def generate_tc_files(plan, desired_files, testcase_name):
    """
    - Generates namespaced dictionaries.
    - Generates scenario hash.
    - Generates and returns necessary template files
    """
    # Handle various entities extracted from `terraform plan` JSON file.
    plan, secrets = generate_namespaced_dictionaries(plan)
    vars, outputs, vars_dict, _ = plan
    tower_secrets, groundswell_secrets, seqerakit_secrets, wave_lite_secrets = secrets
    namespaces = [
        vars,
        outputs,
        tower_secrets,
        groundswell_secrets,
        seqerakit_secrets,
        wave_lite_secrets,
    ]

    # Create hash of plan artefacts & secrets.
    content_to_hash = (
        f"{vars}\n{outputs}\n{tower_secrets}\n{groundswell_secrets}\n{seqerakit_secrets}\n{wave_lite_secrets}"
    )
    hash = hashlib.sha256(content_to_hash.encode("utf-8")).hexdigest()[:16]

    # If `kitchen_sink = True` or `desired_files = []` create every config file. If not, filter.
    if kitchen_sink:
        desired_files = []

    if desired_files:
        needed_template_files = {k: v for k, v in all_template_files.items() if k in desired_files}
    else:
        needed_template_files = all_template_files

    tc_files = generate_interpolated_templatefiles(hash, namespaces, needed_template_files, testcase_name)

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
