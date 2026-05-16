import json
import os
from pathlib import Path
import shutil
import subprocess

from tests.utils.cache.cache import hash_cache_key, normalize_whitespace
from tests.utils.config import FP
from tests.utils.filehandling import FileHelper


# Sentinel for `terraform console` placeholder when a value can't be resolved without `terraform apply`
# (e.g. a ternary whose unselected branch references a resource attribute — see #353 addendum).
TF_CONSOLE_UNKNOWN_MARKER = "(known after apply)"


## ------------------------------------------------------------------------------------
## Subprocess Utility Functions
## ------------------------------------------------------------------------------------
# stdout/stderr are captured (not echoed) to keep the test console clean during success.
# On failure, both streams are surfaced inside the raised RuntimeError so pytest tracebacks
# include the actual terraform error rather than a bare "exit status 1".
def execute_subprocess(command: str) -> str:
    """Execute a subprocess command. Surfaces stdout+stderr on failure."""
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            shell=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Subprocess failed (exit {e.returncode}): {command}\n"
            f"--- STDOUT ---\n{e.stdout}\n"
            f"--- STDERR ---\n{e.stderr}"
        ) from e
    return result.stdout


## ------------------------------------------------------------------------------------
## Utility Class
## ------------------------------------------------------------------------------------
# Keep all file method helpers in a single class to simplify imports.
class TF:
    """Terraform command execution helpers.
    - Plan based on core tfvars, core override, and testcase override.
    - Targeted apply/destroy available if necessary. eg.
      - `terraform apply   --auto-approve tfpan`
      - `terraform apply   --auto-approve -target=null_resource.my_resource`
      - `terraform destroy --auto-approve`
      - `terraform destroy --auto-approve -target=null_resource.my_resource`
    """

    @staticmethod
    def plan(qualifier: str = "") -> None:
        """Run terraform plan with caching support."""
        files_to_purge = [FP.TFPLAN_FILE_LOCATION, FP.TFPLAN_JSON_LOCATION]

        for file in files_to_purge:
            Path(file).unlink(missing_ok=True)

        command = f"terraform plan {qualifier} -out=tfplan -refresh=false && terraform show -json tfplan > tfplan.json"
        execute_subprocess(command)

    @staticmethod
    def apply(qualifier: str = "") -> None:
        """Run terraform apply (defaults to using tfplan)."""
        qualifier = qualifier if len(qualifier) > 0 else "tfplan"
        command = f"terraform apply --auto-approve {qualifier}"
        execute_subprocess(command)

    @staticmethod
    def destroy(qualifier: str = "") -> None:
        """Run terraform destroy."""
        qualifier = qualifier if len(qualifier) > 0 else ""
        command = f"terraform destroy --auto-approve {qualifier}"
        execute_subprocess(command)


## ------------------------------------------------------------------------------------
## Plan Generation
## ------------------------------------------------------------------------------------
# Find a cached Terraform plan, or generate new one with fresh set of tfvars files.
def prepare_plan(tf_modifiers: str, qualifier: str = "") -> dict:
    """Generate override.auto.tfvars and run terraform plan with caching.

    Args:
        tf_modifiers: Terraform variable overrides
        qualifier: Additional modifier to add to cache key (e.g '-target=null_resource.my_resource')

    Returns:
        Terraform plan JSON data
    """
    # Cache key affected by whitespace. Standardize before hashing.
    tf_modifiers = normalize_whitespace(tf_modifiers)
    cache_key = hash_cache_key(tf_modifiers, qualifier)

    # Always try to use cached results (for speed and performance)
    cached_plan = f"{FP.CACHE_PLAN_DIR}/plan_{cache_key}"
    cached_json = f"{FP.CACHE_PLAN_DIR}/plan_{cache_key}.json"

    # Write normalized tf_modifiers to the 'override.auto.tfvars' file.
    FileHelper.write_file(FP.TFVARS_AUTO_OVERRIDE_DST, tf_modifiers)

    if os.path.exists(cached_json):
        print(f"Cache hit! {cache_key}")
        shutil.copy(cached_plan, FP.TFPLAN_FILE_LOCATION)
        shutil.copy(cached_json, FP.TFPLAN_JSON_LOCATION)
        return FileHelper.read_json(FP.TFPLAN_JSON_LOCATION)

    # Cache miss. Create plan files and cache for future use.
    print(f"Cache miss. {cache_key}")
    TF.plan(qualifier)

    shutil.copy(FP.TFPLAN_FILE_LOCATION, cached_plan)
    shutil.copy(FP.TFPLAN_JSON_LOCATION, cached_json)

    return FileHelper.read_json(FP.TFPLAN_JSON_LOCATION)


## ------------------------------------------------------------------------------------
## Console-only path (no plan required)
## ------------------------------------------------------------------------------------
def stage_tfvars(tf_modifiers: str) -> None:
    """Write `tf_modifiers` to override.auto.tfvars without running `terraform plan`.

    Faster counterpart to `prepare_plan` for tests that don't need plan-derived values
    (i.e. anything in the templatefile path after the #353 console-based refactor).

    Same whitespace normalisation as `prepare_plan` so the override file is byte-identical
    regardless of which helper produced it.
    """
    tf_modifiers = normalize_whitespace(tf_modifiers)
    FileHelper.write_file(FP.TFVARS_AUTO_OVERRIDE_DST, tf_modifiers)


def _console_outputs_cache_path() -> Path:
    """Disk path for the cached console outputs of the currently-staged scenario.

    Cache key is the hash of `override.auto.tfvars`'s content. Matches `prepare_plan`'s
    cache-keying convention so the two paths invalidate together on tfvars changes.
    """
    try:
        override_content = FileHelper.read_file(FP.TFVARS_AUTO_OVERRIDE_DST)
    except (FileNotFoundError, OSError):
        override_content = ""
    cache_key = hash_cache_key(override_content, "")
    return Path(FP.CACHE_CONSOLE_DIR) / f"console_outputs_{cache_key}.json"


def extract_module_outputs_via_console() -> dict[str, object]:
    """Return the full `module.connection_strings.*` output map via a single `terraform console` call.

    Replaces the plan-derived `tc.outputs` for tests that only need module outputs (which
    after the v2.0.0 refactor of the `connection_strings` module is a pure-function map of
    its inputs). Does NOT require `terraform plan`; requires `terraform init`.

    Works because the module's call site at `000_main.tf` wraps every resource-attribute
    input in the `var.use_mocks ? null : try(<ref>, null)` two-layer defense, which keeps
    all the module's inputs evaluatable under console-without-state. See the #353 addendum
    for the full reasoning.

    Results are cached to disk in `tests/.console_cache/` keyed on the override.auto.tfvars
    hash — a single `terraform console` invocation costs ~1.8s, so reusing across test
    sessions (or across multiple tests staging the same scenario) preserves the warm-cache
    speed the legacy plan-based path provided. Invalidate via `make purge_cache`.
    """
    cache_path = _console_outputs_cache_path()
    if cache_path.exists():
        return FileHelper.read_json(str(cache_path))

    result = subprocess.run(
        ["terraform", "console"],  # noqa: S607  (relies on PATH; standard for test env)
        input="jsonencode(module.connection_strings)",
        capture_output=True,
        text=True,
        check=True,
    )
    # `terraform console` emits the value of `jsonencode(...)` as a *quoted* JSON string
    # (e.g. `"{\"tower_db_url\":\"...\"}"\n`). Decode the wrapping quote-string first, then
    # parse the inner JSON object.
    outputs = json.loads(json.loads(result.stdout.strip()))

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(outputs))
    return outputs


def console_evaluate_local(local_name: str) -> str:
    """Return the raw stdout from `terraform console` for the expression `local.<local_name>`.

    Used by the regression linter that ensures every local referenced from a templatefile
    arg map is resolvable under console-without-plan. The caller is responsible for
    interpreting the result (in particular, comparing against `TF_CONSOLE_UNKNOWN_MARKER`).
    """
    result = subprocess.run(
        ["terraform", "console"],  # noqa: S607  (relies on PATH; standard for test env)
        input=f"local.{local_name}",
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()
