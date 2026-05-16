"""Parallel precompute of resolved `local.*` values for every collected test scenario.

Hooks into `pytest_collection_modifyitems` (collect tfvars per test via the `tfvars` marker)
and `session_setup` (kick off parallel `terraform console` calls). Each unique scenario gets
one console invocation that emits `jsonencode({try(local.X, null)})` for every local
referenced from `009_define_file_templates.json`; the resolved map is cached on disk keyed
by the scenario hash.

Tests do not yet consume the cache — phase 1 is mechanism + timing baseline. The per-template
hashing layer that will consume these values is tracked in `optimize-test-file-generation`.

`try(..., null)` defends against the still-unguarded locals (`local.vpc_id`,
`local.dns_instance_ip`, etc.) that lack the two-layer `var.use_mocks ? null : try(...)`
pattern. Those resolve to `null` here and stay broken for downstream consumers until
`make_locals_more_defensive` lands.
"""

import concurrent.futures
import json
from pathlib import Path
import re
import subprocess
import tempfile
import time

from tests.utils.cache.cache import hash_scenario
from tests.utils.config import FP


JSON_009_PATH = "009_define_file_templates.json"

# Locals we can't or shouldn't ask `terraform console` to resolve. Source of truth is
# `tests/unit/framework/test_console_locals_resolvability.py`; keep in sync.
# - `*_secrets` are substituted in Python from JSON fixtures before payloads reach console.
# - The rest reference resource attributes inside unguarded ternaries and resolve to
#   `(known after apply)` under console-without-plan. Any `(known after apply)` entry
#   inside a `jsonencode({...})` collapses the entire batch to unknown — so they have to
#   be excluded until the `make_locals_more_defensive` work lands.
_LOCALS_TO_SKIP = {
    "tower_secrets",
    "groundswell_secrets",
    "seqerakit_secrets",
    "wave_lite_secrets",
    "vpc_id",
    "dns_instance_ip",
    "ssh_key_name",
    "sg_ec2_final",
}


def discover_referenced_locals() -> set[str]:
    """Return every console-resolvable `local.<NAME>` referenced from JSONified 009.

    Walks the JSON-as-text since `replace_vars_in_templatefile` already uses regex against
    the same source. Excludes `_LOCALS_TO_SKIP` — locals that either don't need terraform
    resolution (Python-substituted secrets) or can't be resolved without a plan.
    """
    path = Path(FP.ROOT) / JSON_009_PATH
    if not path.exists():
        return set()
    content = path.read_text()
    return set(re.findall(r"local\.(\w+)", content)) - _LOCALS_TO_SKIP


def collect_scenarios_from_items(items) -> dict[str, str]:
    """Build `{scenario_hash: tf_modifiers}` from collected pytest items.

    Reads each item's `@pytest.mark.tfvars(...)` marker; falls back to `#NONE` for tests
    without one (matching the `staged_scenario` fixture's default).
    """
    scenarios: dict[str, str] = {}
    for item in items:
        marker = item.get_closest_marker("tfvars")
        tf_modifiers = marker.args[0] if marker else "#NONE"
        scenarios[hash_scenario(tf_modifiers)] = tf_modifiers
    return scenarios


def _build_resolution_expression(locals_to_resolve: set[str]) -> str:
    r"""Build the `jsonencode({...})` HCL expression that resolves every requested local.

    Each entry is `name = try(local.name, null)`. The `try()` wrapper is load-bearing —
    it keeps the whole batch evaluable even when a specific local has unguarded resource
    refs that would otherwise return `(known after apply)` and corrupt the entire `jsonencode`.

    Single line — `terraform console` treats stdin newlines as submit-this-expression markers.
    """
    sorted_names = sorted(locals_to_resolve)
    body = ", ".join(f"{name} = try(local.{name}, null)" for name in sorted_names)
    return f"jsonencode({{ {body} }})"


def _precompute_scenario(scenario_hash: str, tf_modifiers: str, expr: str) -> tuple[str, float, str]:
    """Resolve all locals for one scenario via `terraform console`. Write JSON to cache.

    Returns (scenario_hash, elapsed_seconds, status). `status` is `"hit"` if the cache file
    already existed, `"miss-ok"` on successful render, `"miss-err: <msg>"` on failure.

    `terraform console`'s `-var-file=` flag is layered ON TOP of the project's auto-loaded
    tfvars (`terraform.tfvars`, `base-overrides.auto.tfvars`). The caller is responsible for
    ensuring `override.auto.tfvars` is absent during the precompute window so it can't taint
    the resolution.
    """
    cache_path = Path(FP.CACHE_SCENARIO_DIR) / f"{scenario_hash}.json"
    start = time.time()
    if cache_path.exists():
        return scenario_hash, time.time() - start, "hit"

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".tfvars",
        prefix=f"precompute-{scenario_hash}-",
        delete=False,
    ) as tf:
        tf.write(tf_modifiers)
        tfvars_path = Path(tf.name)

    # Per-worker state-file path. Parallel console processes share the project's `.terraform/`
    # but acquire a state lock on the default state file path; pointing each worker at a unique
    # (empty) state path side-steps the contention. Console reads state but doesn't mutate it.
    state_path = Path(tempfile.gettempdir()) / f"precompute-{scenario_hash}.tfstate"

    try:
        try:
            cmd = ["terraform", "console", f"-var-file={tfvars_path}", f"-state={state_path}"]
            result = subprocess.run(  # noqa: S603  (tfvars/state paths are tempfile-generated, not user input)
                cmd,
                cwd=FP.ROOT,
                input=expr,
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            # Strip ANSI escape sequences from terraform's pretty-printed error output.
            stderr_clean = re.sub(r"\x1b\[[0-9;]*m", "", e.stderr or "")
            return scenario_hash, time.time() - start, f"miss-err: rc={e.returncode}; stderr={stderr_clean[:800]}"

        # `jsonencode(...)` output: a quoted JSON string. Decode twice (matches `extract_module_outputs_via_console`).
        try:
            resolved = json.loads(json.loads(result.stdout.strip()))
        except (json.JSONDecodeError, ValueError) as e:
            stderr_clean = re.sub(r"\x1b\[[0-9;]*m", "", result.stderr or "")
            return (
                scenario_hash,
                time.time() - start,
                (f"miss-err: json-parse {e}; stdout={result.stdout[:200]!r}; stderr={stderr_clean[:400]}"),
            )

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(resolved))
        return scenario_hash, time.time() - start, "miss-ok"
    finally:
        tfvars_path.unlink(missing_ok=True)


def precompute_in_parallel(scenarios: dict[str, str], max_workers: int = 8) -> dict[str, str]:
    """Run `_precompute_scenario` over all unique scenarios in parallel. Return status map.

    Status values per scenario: "hit", "miss-ok", or "miss-err: <message>".
    Failures don't abort the batch — tests can still run; the missing cache file is just
    a downstream cache miss when this work is consumed.
    """
    if not scenarios:
        return {}

    Path(FP.CACHE_SCENARIO_DIR).mkdir(parents=True, exist_ok=True)

    locals_to_resolve = discover_referenced_locals()
    if not locals_to_resolve:
        # 009.json not yet generated, or no locals referenced. Nothing to do.
        return dict.fromkeys(scenarios, "skip-no-locals")

    expr = _build_resolution_expression(locals_to_resolve)
    statuses: dict[str, str] = {}

    # Clear override.auto.tfvars so each parallel console call only sees the per-scenario
    # tfvars passed via -var-file (plus the project's base auto-loaded tfvars). Restored
    # by whichever test runs first via `stage_tfvars`.
    override_path = Path(FP.TFVARS_AUTO_OVERRIDE_DST)
    override_path.unlink(missing_ok=True)

    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_precompute_scenario, h, tfvars, expr): h for h, tfvars in scenarios.items()}
        for future in concurrent.futures.as_completed(futures):
            h = futures[future]
            try:
                _, _elapsed, status = future.result()
            except Exception as e:
                status = f"miss-err: worker-crash {e}"
            statuses[h] = status

    return statuses
