import re
import subprocess
from pathlib import Path

from tests.utils.assertions.file_filters import filter_templates
from tests.utils.cache.cache import create_templatefile_cache_folder
from tests.utils.config import (
    TCValues,
    all_template_files,
)
from tests.utils.filehandling import FileHelper
from tests.utils.terraform.parser import extract_config_values

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


def _is_sql_file(key: str) -> bool:
    """
    Check if file needs special SQL handling (can't use terraform console).

    SQL files with postgres single-quotes break terraform console input parsing.
    """
    # TODO: Move this to all_template_files as a discrete flag
    sql_exception_files = ["wave_lite_rds"]
    return key in sql_exception_files


def generate_tc_files(plan, desired_files, testcase_name):
    """
    Create templatefiles relevant to the testcase.

    Delegates to specialized handlers based on file type:
        - Regular templates: terraform console rendering
        - SQL templates: Python script substitution

    Args:
        tc: Test case context object.

    Returns:
        Updated template_files dict with content and filepath added
    """
    TC: TCValues = extract_config_values(plan)

    TC.all_template_files = filter_templates(desired_files)  # Master dictionary relevant to this testcase
    TC.testcase_name = testcase_name

    for key in TC.all_template_files.keys():  # (e.g., "tower_env")
        extension = all_template_files[key]["extension"]
        read_type = all_template_files[key]["read_type"]

        cache_dir = create_templatefile_cache_folder(TC)
        cache_file_str = f"{cache_dir}/{key}{extension}"
        cache_file_path = Path(cache_file_str)

        if _is_sql_file(key):
            # _generate_sql_templatefile(key, tc.cache_dir, tc.template_files)
            pass
        else:
            if not cache_file_path.exists():
                # Cache miss. Create file
                payload = prepare_templatefile_payload(key, TC)
                write_populated_templatefile(cache_file_str, payload)
            cache_file_content = read_type(cache_file_path.as_posix())

            TC.all_template_files[key]["content"] = cache_file_content
            TC.all_template_files[key]["filepath"] = cache_file_str

    return TC.all_template_files
