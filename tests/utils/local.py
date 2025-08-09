from pickle import FALSE
from numpy.core.fromnumeric import nonzero
import pytest

import os
from pathlib import Path
import shutil
import sys
import hashlib
from typing import Dict, Any
import re

import subprocess
import json
import yaml

from types import SimpleNamespace

from scripts.installer.utils.purge_folders import delete_pycache_folders


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
## Universal Configuration
## ------------------------------------------------------------------------------------
# Assumes this file lives at 3rd layer of project (i.e. PROJECT_ROOT/tests/utils/local.py)
root = str(Path(__file__).parent.parent.parent.resolve())

# Tfvars and override files filepaths
tfvars_path                         = f"{root}/terraform.tfvars"
tfvars_backup_path                  = f"{root}/terraform.tfvars.backup"

test_tfvars_source                  = f"{root}/tests/datafiles/terraform.tfvars"
test_tfvars_target                  = f"{root}/terraform.tfvars"
test_tfvars_override_source         = f"{root}/tests/datafiles/base-overrides.auto.tfvars"
test_tfvars_override_target         = f"{root}/base-overrides.auto.tfvars"

test_case_override_target           = f"{root}/override.auto.tfvars"
test_case_override_outputs_source   = f"{root}/tests/datafiles/012_testing_outputs.tf"
test_case_override_outputs_target   = f"{root}/012_testing_outputs.tf"
                

test_docker_compose_file  = f"/tmp/cx-testing-docker-compose.yml"

# SSM (testing) secrets
ssm_tower                           = f"{root}/tests/datafiles/ssm_sensitive_values_tower_testing.json"
ssm_groundswell                     = f"{root}/tests/datafiles/ssm_sensitive_values_groundswell_testing.json"
ssm_seqerakit                       = f"{root}/tests/datafiles/ssm_sensitive_values_seqerakit_testing.json"
ssm_wave_lite                       = f"{root}/tests/datafiles/ssm_sensitive_values_wave_lite_testing.json"

# Tfplan files and caching folder
plan_cache_dir                      = f"{root}/tests/.plan_cache"

test_case_tfplan_file               = f"{root}/tfplan"
test_case_tfplan_json_file          = f"{root}/tfplan.json"

templatefile_cache_dir            = f"{root}/tests/.templatefile_cache"


## ------------------------------------------------------------------------------------
## File Utility Functions
## ------------------------------------------------------------------------------------
def read_json(file_path: str) -> dict:
    """Read a JSON plan file."""
    with open(file_path, "r") as f:
        return json.load(f)


def read_yaml(file_path: str) -> Any:
    """Read a JSON plan file."""
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def read_file(file_path: str) -> str:
    """Read a file."""
    with open(file_path, "r") as f:
        return f.read()


def write_file(file_path: str, content: str | bytes) -> None:
    """Write content to a file."""
    if isinstance(content, bytes):
        content = content.decode("utf-8")
    with open(file_path, "w") as f:
        f.write(content)


def move_file(source: str, target: str) -> None:
    """Move a file."""
    try:
        shutil.move(source, target)
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        sys.exit(1)


def copy_file(source: str, target: str) -> None:
    """Move a file."""
    try:
        shutil.copy2(source, target)
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        sys.exit(1)


def parse_key_value_file(file_path: str) -> Dict[str, Any]:
    """Parse a file containing KEY=VALUE pairs. Function intended to be used with tfvars files.

    Args:
        file_path: Path to the file to parse

    Returns:
        Dictionary containing key-value pairs

    NOTE:
        Double-quotes / single-quottes as part of string messes up pytest string assertions. Remove these to normalize.
        Terraform always hasd double-quotes.
        Env files can be either double-quotes or single-quotes.
    """
    result = {}
    raw = read_file(file_path)

    for line in raw.splitlines():
        line = line.strip()
        if line and "=" in line:
            key, value = line.split("=", 1)
            value = value.strip()

            # Edgecase: Empty strings represented by "" or '' but this confuses python (e.g. '""')
            if (value == '""') or (value == "''"):
                value = ""
            elif value.startswith("'") and value.endswith("'"):
                value = value.strip("'")
            elif value.startswith('"') and value.endswith('"'):
                value = value.strip('"')

            result[key.strip()] = value.strip()

    return result


## ------------------------------------------------------------------------------------
## Cache Utility Functions
## ------------------------------------------------------------------------------------
def get_cache_key(override_data: str, qualifier: str = "") -> str:
    """Generate SHA-256 hash of override data and tfvars content for cache key."""
    override_data = override_data.strip()
    qualifier = qualifier.strip()

    tfvars_content = read_file(tfvars_path).strip()

    # Create combined cache key
    combined_content = f"{override_data}\n---TFVARS---\n{qualifier}\n---QUALIFIER---\n{tfvars_content}"
    return hashlib.sha256(combined_content.encode("utf-8")).hexdigest()[:16]


def strip_overide_whitespace(override_data: str) -> str:
    """
    Purges intermediate whitespace (extra space makes same keys hash to different values).
    Convert multiple spaces to single space (ASSUMPTION: Python tabs insert spaces!)
    NOTE: Need to keep `\n` to not break HCL formatting expectations.
    """
    return "\n".join(re.sub(r"\s+", " ", line) for line in override_data.splitlines())


## ------------------------------------------------------------------------------------
## Subprocess Utility Functions
## ------------------------------------------------------------------------------------
# NOTE: I need the PIPE to capture output for the plan to apply, but it's noisy in the console.
# Ended up using shell-type subprocess.run commands so I can use native Bash to dump output to files.
def execute_subprocess(command: str) -> bytes:
    """
    Execute a subprocess command.
    """
    result = subprocess.run(
        command,
        check=True,
        # stdout=subprocess.PIPE,
        stdout=subprocess.DEVNULL,  # > /dev/null
        stderr=subprocess.STDOUT,  # 2>&1
        shell=True,
    ).stdout

    return result


## ------------------------------------------------------------------------------------
## Terrafrom Comamnd Execution Helpers
## ------------------------------------------------------------------------------------
def run_terraform_plan(qualifier: str = "") -> None:
    """
    Plan based on core tfvars, core override, and testcase override.
    Uses shell-type Bash commands to simplify code.
    """
    for file in [test_case_tfplan_file, test_case_tfplan_json_file]:
        Path(file).unlink(missing_ok=True)

    command = f"terraform plan {qualifier} -out=tfplan -refresh=false && terraform show -json tfplan > tfplan.json"
    execute_subprocess(command)


def run_terraform_apply(qualifier: str = "", auto_approve: bool = True) -> None:
    """
    Normally should use tfplan from `run_terraform_plan`.
    Command override available for targeted apply just in case (will need to plan again).
    Uses shell-type Bash commands to simplify code.
    Results will generally be:
        - `terraform apply --auto-approve tfpan`
        - `terraform apply --auto-approve -target=null_resource.my_resource`
    """
    base_command = f"terraform apply {'--auto-approve' if auto_approve else ''}"
    command = f"{base_command} {qualifier if len(qualifier) > 0 else 'tfplan'}"
    execute_subprocess(command)


def run_terraform_destroy(qualifier: str = "", auto_approve: bool = True) -> None:
    """
    Override file generated by prepare_plan; core tfvars file generated by fixture.
    Results will generally be:
        - `terraform destroy --auto-approve`
        - `terraform destroy --auto-approve -target=null_resource.my_resource`
    """
    base_command = f"terraform destroy {'--auto-approve' if auto_approve else ''}"
    command = f"{base_command} {qualifier if len(qualifier) > 0 else ''}"
    execute_subprocess(command)


## ------------------------------------------------------------------------------------
## Helpers
## ------------------------------------------------------------------------------------
def prepare_plan(
    override_data: str,
    qualifier: str = "",
    use_cache: bool = True,
) -> dict:
    """Generate override.auto.tfvars and run terraform plan with caching.

    Args:
        override_data: Terraform variable overrides
        qualifier: Additional modifier to add to cache key (e.g '-target=null_resource.my_resource')
        use_cache: Whether to use cached results (default: True)

    Returns:
        Terraform plan JSON data
    """

    override_data = strip_overide_whitespace(override_data)

    cache_key = get_cache_key(override_data, qualifier)
    cached_plan_file = f"{plan_cache_dir}/plan_{cache_key}"
    cached_plan_json_file = f"{plan_cache_dir}/plan_{cache_key}.json"

    os.makedirs(plan_cache_dir, exist_ok=True)

    if use_cache and os.path.exists(cached_plan_json_file):
        print(f"Reusing cached plans for: {cache_key}")

        execute_subprocess(f"cp {cached_plan_file} {test_case_tfplan_file}")
        execute_subprocess(f"cp {cached_plan_json_file} {test_case_tfplan_json_file}")
        write_file(test_case_override_target, override_data)
    else:
        # Write override file in root and create plan files.
        print(f"Cache miss. Generating new plan for: {cache_key}")
        write_file(test_case_override_target, override_data)
        run_terraform_plan(qualifier)

        # Stash generated plan files in cachedir for future use.
        execute_subprocess(f"cp {test_case_tfplan_file} {cached_plan_file}")
        execute_subprocess(f"cp {test_case_tfplan_json_file} {cached_plan_json_file}")

    return read_json(test_case_tfplan_json_file)


def get_reconciled_tfvars() -> Dict[str, Any]:
    """
    Return single consolidated file comprising:
      - test_tfvars_target
      - (updated by) test_tfvars_override_target
      - (updated by) test_case_override_target
    """
    tfvars = parse_key_value_file(test_tfvars_target)
    base_overrides = parse_key_value_file(test_tfvars_override_target)
    try:
        # Test case override file may not exist.
        test_overrides = parse_key_value_file(test_case_override_target)
    except FileNotFoundError:
        test_overrides = {}

    tfvars.update({k: base_overrides[k] for k in base_overrides.keys()})
    tfvars.update({k: test_overrides[k] for k in test_overrides.keys()})

    return tfvars


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

    with open('tests/datafiles/ssm_sensitive_values_tower_testing.json', 'r') as f:
        tower_secrets = json.load(f)

    with open('tests/datafiles/ssm_sensitive_values_groundswell_testing.json', 'r') as f:
        groundswell_secrets = json.load(f)

    with open('tests/datafiles/ssm_sensitive_values_seqerakit_testing.json', 'r') as f:
        seqerakit_secrets = json.load(f)

    with open('tests/datafiles/ssm_sensitive_values_wave_lite_testing.json', 'r') as f:
        wave_lite_secrets = json.load(f)
    

    # https://dev.to/taqkarim/extending-simplenamespace-for-nested-dictionaries-58e8
    # Avoids noisy dict notation ([""]) and constant repetition of `.value`.
    # Variables have only one key (values); outputs may have 3 keys (sensitive, type, value).
    # Example: `vars.tower_contact_email`
    vars_flattened = {k: v.get("value", v) for k,v in vars_dict.items()}
    outputs_flattened = {k: v.get("value", v) for k,v in outputs_dict.items()}

    tower_secrets_flattened = {k: v.get("value", v) for k,v in tower_secrets.items()}
    groundswell_secrets_flattened = {k: v.get("value", v) for k,v in groundswell_secrets.items()}
    seqerakit_secrets_flattened = {k: v.get("value", v) for k,v in seqerakit_secrets.items()}
    wave_lite_secrets_flattened = {k: v.get("value", v) for k,v in wave_lite_secrets.items()}
    
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
    return ([vars, outputs, vars_dict, outputs_dict], 
            [tower_secrets_sn, groundswell_secrets_sn, seqerakit_secrets_sn, wave_lite_secrets_sn])


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

    # This part a big magical, from Claude: Here's how it works:
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
        pattern = r'module.connection_strings\.(\w+)'
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
        pattern = r'var\.(\w+)'
        return re.sub(pattern, replace_var, input_str)
    
    elif type == "local":
        pattern = r'local\.(\w+)'
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

    vars, outputs, tower_secrets, groundswell_secrets, seqerakit_secrets, wave_lite_secrets = namespaces

    # Had to re-enable this for tower.sql but it breaks tower.env (the data_studio_options). Why?
    # result = replace_vars_in_templatefile(input_str, vars, "tfvar")
    # result = replace_vars_in_templatefile(result, outputs, "local")
    result = replace_vars_in_templatefile(input_str, outputs, "module.connection_strings")
    result = replace_vars_in_templatefile(result, tower_secrets, "tower_secrets")
    result = replace_vars_in_templatefile(result, groundswell_secrets, "groundswell_secrets")
    result = replace_vars_in_templatefile(result, seqerakit_secrets, "seqerakit_secrets")
    result = replace_vars_in_templatefile(result, wave_lite_secrets, "wave_lite_secrets")
    result = result.replace("\n", "")   # MUST REMOVE NEW LINES OR CONSOLE CALL BREAKS.
    # TODO: Figure out secrets

    return result


def prepare_templatefile_payload(key, namespaces):
    """
    Execute the templatefile command from JSONified 009, then sub in necessary values for SimpleNamespaced
    terraform plan outputs.
    """
    templatefile_json = read_json("009_define_file_templates.json")
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
        check=True
    )
    output = payload.stdout

    # Strip '<<EOT' and 'EOT' appending to start and end of multi-line payload emitted by 'terraform console'.
    if output.startswith("<<EOT"):
        lines = output.splitlines()
        output = "\n".join(lines[1:-1])

    write_file(outfile, output)


def generate_interpolated_templatefile(key, extension, read_type, namespaces, templatefile_cache_dir_hash):
    """
    namespaces                  : SimpleNamespaced outputs of 'terrform plan'.
    templatefile_cache_dir_hash : Relies on the hash of all the tfvars files used for the specific testcase.
    key                         : key from JSONified 009
    extension                   : Proper file output
    read_type                   : Which utility helper to use to load the resulting file.
    """

    # Hash templatefiles to speed up n+1 tests
    #   1) Generate hash of tfvars variables and do cache check to speed this up.
    #   2) If cache miss, emit generated files as <CACHE_VALUE>_<FILENAME> and stick in 'tests/.templatfile_cache'.
    outfile = Path(f"{templatefile_cache_dir_hash}/{key}{extension}")
    if not outfile.exists():
        result = prepare_templatefile_payload(key, namespaces)
        write_populated_templatefile(outfile, result)
    
    content = read_type(outfile.as_posix())
    # print(content)
    return content


def generate_all_interpolated_templatefiles(hash, namespaces):
    """
    Create all templatefiles based on terraform values relevant to the specific testcase.
    """
    # Make cache folder if missing
    folder_path = Path(f"{templatefile_cache_dir}/{hash}")
    folder_path.mkdir(parents=True, exist_ok=True)

    templatefile_cache_dir_hash = f"{templatefile_cache_dir}/{hash}"

    template_files = {
        "tower_env": {
            "extension" : ".env", 
            "read_type" : parse_key_value_file,
            "content"   : ""
        },
        "tower_yml": {
            "extension" : ".yaml", 
            "read_type" : read_yaml,
            "content"   : ""
        },
        "tower_sql": {
            "extension" : ".sql", 
            "read_type" : read_file,
            "content"   : ""
        },
        "groundswell_sql": {
            "extension" : ".sql", 
            "read_type" : read_file,
            "content"   : ""
        },
        "groundswell_env": {
            "extension" : ".env", 
            "read_type" : parse_key_value_file,
            "content"   : ""
        },
        "data_studios_env": {
            "extension" : ".env", 
            "read_type" : parse_key_value_file,
            "content"   : ""
        },
        "wave_lite_yml": {
            "extension" : ".yaml", 
            "read_type" : read_yaml,
            "content"   : ""
        },
        "docker_compose": {
            "extension" : ".yaml", 
            "read_type" : read_yaml,
            "content"   : ""
        },
        "seqerakit_yml": {
            "extension" : ".yaml", 
            "read_type" : read_yaml,
            "content"   : ""
        },
        # TODO: aws_batch_manual
        # TODO: aws_batch_forge
        "cleanse_and_configure_host": {
            "extension" : ".sh", 
            "read_type" : read_file,
            "content"   : ""
        },
        "ansible_02_update_file_configurations": {
            "extension" : ".yaml", 
            "read_type" : read_yaml,
            "content"   : ""
        },
        "ansible_03_pull_containers_and_run_tower": {
            "extension" : ".yaml", 
            "read_type" : read_yaml,
            "content"   : ""
        },
        "ansible_05_patch_groundswell": {
            "extension" : ".yaml", 
            "read_type" : read_yaml,
            "content"   : ""
        },
        "ansible_06_run_seqerakit": {
            "extension" : ".yaml", 
            "read_type" : read_yaml,
            "content"   : ""
        },
        # TODO: codecommit_seqerakit
        # TODO: ssh_config
        "docker_logging": {
            "extension" : ".json", 
            "read_type" : read_json,
            "content"   : ""
        },
        "private_ca_conf": {
            "extension" : ".conf", 
            "read_type" : read_file,
            "content"   : ""
        },
    }

    for k,v in template_files.items():
        content = generate_interpolated_templatefile(k, v["extension"], v["read_type"], namespaces, templatefile_cache_dir_hash)
        template_files[k]["content"] = content

    return template_files


## ------------------------------------------------------------------------------------
## Helpers - Assertions
## ------------------------------------------------------------------------------------
def assert_key_value(entries: dict, file):
    """Confirm key-values in provided dict are present in file."""
    for k,v in entries.items():
        assert file[k] == str(v)


def assert_key_not_in_keys(entries: dict, file):
    """Confirm keys in provided dict are not present in file."""
    keys = file.keys()

    for k,v in entries.items():
        assert k not in keys


def assert_present_and_omitted(entries: dict, file):
    """Confirm key-values are present & keys are not present."""
    assert_key_value(entries["present"], file)
    assert_key_not_in_keys(entries["omitted"], file)
