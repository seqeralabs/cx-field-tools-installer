import json
from pathlib import Path
import re
import shutil
import subprocess

from tests.utils.assertions.file_filters import filter_templates
from tests.utils.cache.cache import create_templatefile_cache_folder
from tests.utils.config import FP, TCValues, all_template_files
from tests.utils.filehandling import FileHelper
from tests.utils.terraform.parser import extract_config_values


## ------------------------------------------------------------------------------------
## Helpers - Templatefile
## ------------------------------------------------------------------------------------


def replace_vars_in_templatefile(input_str, vars_dict, pattern) -> str:
    """Replace terraform references with actual values in templatefile string.

    Critical replacements: module.connection_strings.* and secrets
    Do not need to replace 'var.' or 'local.' since terraform console knows these.

    Args:
        input_str: Templatefile string from JSONified 009.
        vars_dict: Dictionary of values to substitute.
        pattern: Which terraform reference type to replace (e.g. "module.connection_strings").

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
        "tls_connect_ssh_host_key": r"tls_private_key\.connect_ssh_host_key\.(\w+)",
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
            if isinstance(value, bool):
                return str(value).lower()  # Booleans need lowercase
            return str(value)  # Numbers stay as-is
        return match.group(0)  # Keep original if not found

    return re.sub(pattern, replace_match, input_str)


def prepare_templatefile_payload(key, tc: TCValues):
    r"""Extract the templatefile command from JSONified 009, then sub values as necessary.

    BACKGROUND:
    Returns a single `templatefile("path", {...})` HCL expression string for the given key.
    The caller (`generate_tc_files`) collects these into a map and feeds the whole map to
    `terraform console` via `render_templatefiles_batched` in one call per scenario (#361),
    rather than invoking the console once per template as the original implementation did
    (#353 introduced console, #361 batched it). The same evaluator `templatefile()` uses
    in production handles the rendering. The substitutions below cover the values console
    can't resolve on its own:
      - `module.connection_strings.*` outputs (resolved via plan-derived `tc.outputs`, or via
        a separate `terraform console` call when running on the #353 fast path).
      - `local.<...>_secrets[...]` — sourced from JSON fixtures since the secrets layer is
        never produced by terraform at test time.
      - `tls_private_key.*` attributes — mocked with deterministic dummy values.

    Variables and other locals are left intact for `terraform console` to resolve at render time.

    Note: '\n' is stripped from the payload because the trailing newline breaks the
    `terraform console` subprocess input parsing.
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
    # tls_private_key attributes are (known after apply) — substitute before console runs,
    # same reason module.connection_strings.* values are substituted.
    tls_ssh_host_key_values = {"public_key_fingerprint_sha256": "SHA256:mocksshfingerprintfortesting"}
    payload = replace_vars_in_templatefile(payload, tls_ssh_host_key_values, "tls_connect_ssh_host_key")
    return payload.replace("\n", "")  # MUST REMOVE NEW LINES OR CONSOLE CALL BREAKS.


def render_templatefiles_batched(payloads: dict[str, str]) -> dict[str, str]:
    r"""Render every requested templatefile in a single `terraform console` call.

    Builds `jsonencode({k1 = <payload1>, k2 = <payload2>, ...})` and feeds it to
    `terraform console`. The console emits the value of `jsonencode(...)` as a
    *quoted* JSON string (e.g. `"{\\"k1\\":\\"...\\"}"`). Decode the wrapping
    quote-string first, then parse the inner JSON object — same double-`json.loads`
    pattern as `executor.py:extract_module_outputs_via_console`.

    Args:
        payloads: {template_key: 'templatefile("path/to/file.tpl", {...})'} — the
            same payload strings `prepare_templatefile_payload` produces today,
            collected into one map instead of submitted serially.

    Returns:
        {template_key: rendered_content}.

    Tradeoff: a single failed payload fails the whole batch. `terraform console`'s
    error names the offending expression in stdout/stderr, but the pytest traceback
    points here rather than at the specific `desired_files` entry. To narrow blame,
    grep the error output for the template key; for unit-level rendering of one
    template, use `write_populated_templatefile` directly. A fail-then-retry-
    individually fallback is intentionally not implemented (see #361).
    """
    if not payloads:
        return {}

    # Single-line expression — terraform console treats stdin newlines as
    # submit-this-expression markers (see the warning in `prepare_templatefile_payload`,
    # and the single-line pattern in `executor.py:extract_module_outputs_via_console`).
    expr_body = ", ".join(f"{k} = {v}" for k, v in payloads.items())
    expr = f"jsonencode({{ {expr_body} }})"

    result = subprocess.run(
        ["terraform", "console"],  # noqa: S607  (relies on PATH; standard for test env)
        input=expr,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(json.loads(result.stdout.strip()))


def write_populated_templatefile(outfile, payload):
    """Executes 'terraform console', passing in the specific templatefile and substituted payload.

    Example :
        > terraform console <<< 'templatefile("assets/src/ansible/06_run_seqerakit.yml.tpl",
            { app_name = "abc", flag_create_hosts_file_entry = false, flag_do_not_use_https = true })'

    Note:
        - 'terraform console' command needs single quotes on outside and double-quotes within.
        - 'terraform console' emits '<<EOT' and 'EOT' at start/finish of multi-line payload. These must be stripped.
    """
    # print(payload)
    payload = subprocess.run(
        ["terraform", "console"],  # noqa: S607  (relies on PATH; standard for test env)
        input=str(payload),
        capture_output=True,
        text=True,
        check=True,
    )
    output = payload.stdout

    if output.startswith("<<EOT"):
        lines = output.splitlines()
        output = "\n".join(lines[1:-1])

    FileHelper.write_file(outfile, output)


def _is_wave_lite_rds(key: str) -> bool:
    """Check if file needs special SQL handling (can't use terraform console).

    SQL files with postgres single-quotes break terraform console input parsing.
    """
    sql_exception_files = ["wave_lite_rds"]
    return key in sql_exception_files


def generate_tc_files(plan, desired_files, testcase_name):
    """Create templatefiles relevant to the testcase.

    Args:
        plan: Terraform plan JSON used to extract config values. Pass `None` to take the
            console-based fast path (no `terraform plan` invoked; module outputs resolved
            via a single `terraform console` call). The caller must have staged tfvars
            (e.g. via `stage_tfvars`) before invoking this function. See #353 addendum.
        desired_files: List of template file keys to generate (empty list = all).
        testcase_name: Name of the testcase, used as a sub-folder for cache output.

    Returns:
        Updated template_files dict with content and filepath added.

    Implementation notes:
        Two-pass loop. Pass 1 partitions every requested template into one of three
        buckets: (a) wave-lite-rds SQL files (use sedalternative.py path), (b) cache
        hits (read existing cache file), (c) cache misses (collect payload for batch).
        Pass 2 issues a single `terraform console` call via `render_templatefiles_batched`
        for all cache-miss payloads, then writes each result to its per-key cache file.
        See #361 for the optimisation rationale.
    """
    tc: TCValues = extract_config_values(plan)

    tc.all_template_files = filter_templates(desired_files)  # Master dictionary relevant to this testcase
    tc.testcase_name = testcase_name

    cache_dir = create_templatefile_cache_folder(tc)

    # Pass 1: partition into wave-lite-rds (SQL), cache hits, and cache misses.
    batch_payloads: dict[str, str] = {}  # key -> templatefile(...) HCL expression
    cache_miss_paths: dict[str, str] = {}  # key -> on-disk cache file path

    for key in tc.all_template_files:  # (e.g., "tower_env")
        extension = all_template_files[key]["extension"]
        read_type = all_template_files[key]["read_type"]

        cache_file_str = f"{cache_dir}/{key}{extension}"
        cache_file_path = Path(cache_file_str)

        if _is_wave_lite_rds(key):
            # (Postgres) SQL files can't use 'terraform console' because single-quotes break input parsing.
            # Generate SQL template using Python script substitution.

            # Copy src file to cache_dir
            # WARNING!! THIS whole section is brittle and stupid.
            #   - Python 'sedalternative' script is dumb and very finicky about dirs and hyphens.
            #   - The all_template_files key for this uses underscores but file itself needs to be hyphens.
            #   TODO: Find some way to get this harmonized.
            #         Simplest way would be to change hyphens to underscores in source file.
            file_name = "wave-lite-rds.sql"
            source_path = f"{FP.ROOT}/assets/src/wave_lite_config/{file_name}"
            target_path = f"{cache_dir}/{file_name}"
            script_path = f"{FP.ROOT}/scripts/installer/utils/sedalternative.py"
            shutil.copy(source_path, target_path)

            # Run substitution script
            # TODO: Make credentials configurable instead of hardcoded
            command = f"python3 {script_path} wave_lite_test_limited wave_lite_test_limited_password {cache_dir}"
            subprocess.run(command, shell=True, text=True, capture_output=False, check=True)  # noqa: S602  (intentional shell features; inputs are hardcoded test paths)

            # Store content
            tc.all_template_files[key]["content"] = read_type(target_path)
            tc.all_template_files[key]["filepath"] = target_path  # DONT USE THIS: cache_file_str

        elif cache_file_path.exists():
            # Cache hit: read existing rendered file directly.
            tc.all_template_files[key]["content"] = read_type(cache_file_path.as_posix())
            tc.all_template_files[key]["filepath"] = cache_file_str

        else:
            # Cache miss: collect payload for the batched render pass.
            batch_payloads[key] = prepare_templatefile_payload(key, tc)
            cache_miss_paths[key] = cache_file_str

    # Pass 2: single batched `terraform console` call renders every cache-miss
    # template. The jsonencode/json.loads round-trip in render_templatefiles_batched
    # returns rendered strings with newlines already decoded — no `<<EOT` stripping
    # needed (that was a quirk of the per-template path's raw heredoc output).
    if batch_payloads:
        rendered = render_templatefiles_batched(batch_payloads)
        for key, content in rendered.items():
            target_path = cache_miss_paths[key]
            FileHelper.write_file(target_path, content)

            read_type = all_template_files[key]["read_type"]
            tc.all_template_files[key]["content"] = read_type(target_path)
            tc.all_template_files[key]["filepath"] = target_path

    return tc.all_template_files
