"""Parallel precompute of resolved locals + rendered templatefiles per scenario.

Each unique tfvars scenario gets one parallel `terraform console` worker that:
  1. Builds payloads for every templatefile (Python-side substitution of secrets + tls stubs).
  2. Submits a single `jsonencode({locals = {...}, templates = {...}})` to console.
  3. Parses the result; writes `locals.json` + every rendered template into
     `tests/.scenario_cache/{cache_key}/`.

The cache key is `hash_templatefile_cache_key(tf_modifiers)` — disk-only, no console
needed. Tests read from this cache directly at runtime; no further console invocations
occur.

`wave_lite_rds.sql` is rendered separately via `sedalternative.py` because its postgres
single-quote literals break `terraform console`'s stdin input parsing.
"""

import ast
from collections import defaultdict
import concurrent.futures
from datetime import UTC, datetime
import inspect
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import textwrap
import time

from tests.utils.cache.cache import hash_scenario, hash_templatefile_cache_key, normalize_whitespace
from tests.utils.config import FP, all_template_files
from tests.utils.filehandling import FileHelper


JSON_009_PATH = "009_define_file_templates.json"
JSON_012_PATH = "012_outputs.json"

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

_TLS_KEY_STUBS = {"public_key_fingerprint_sha256": "SHA256:mocksshfingerprintfortesting"}

# `all_template_files` key uses underscores; the actual on-disk filename uses hyphens.
_WAVE_LITE_RDS_KEY = "wave_lite_rds"
_WAVE_LITE_RDS_FILENAME = "wave-lite-rds.sql"


## ------------------------------------------------------------------------------------
## Reference substitution (Python-side; for refs console can't resolve in test mode)
## ------------------------------------------------------------------------------------
def _replace_refs(input_str: str, vars_dict: dict, pattern: str) -> str:
    """Substitute terraform references that console can't resolve in test mode.

    Handles `local.<X>_secrets[...]["value"]` and `tls_private_key.connect_ssh_host_key.*`.
    Module outputs, vars, and other locals are left intact — console resolves them
    natively when evaluating the surrounding `templatefile()` expression.
    """
    patterns = {
        "tower_secrets": r'local\.tower_secrets\["([^"]+)"\]\["[^"]+"\]',
        "groundswell_secrets": r'local\.groundswell_secrets\["([^"]+)"\]\["[^"]+"\]',
        "seqerakit_secrets": r'local\.seqerakit_secrets\["([^"]+)"\]\["[^"]+"\]',
        "wave_lite_secrets": r'local\.wave_lite_secrets\["([^"]+)"\]\["[^"]+"\]',
        "tls_connect_ssh_host_key": r"tls_private_key\.connect_ssh_host_key\.(\w+)",
    }
    pat = patterns.get(pattern)
    if not pat:
        return input_str

    def replace_match(match: re.Match) -> str:
        var_name = match.group(1)
        if var_name in vars_dict:
            value = vars_dict[var_name]
            if isinstance(value, str):
                return f'"{value}"'
            if isinstance(value, bool):
                return str(value).lower()
            return str(value)
        return match.group(0)

    return re.sub(pat, replace_match, input_str)


## ------------------------------------------------------------------------------------
## Discovery
## ------------------------------------------------------------------------------------
def discover_referenced_locals() -> set[str]:
    """Console-resolvable locals referenced from 009.json (minus the allowlisted skips)."""
    path = Path(FP.ROOT) / JSON_009_PATH
    if not path.exists():
        return set()
    content = path.read_text()
    return set(re.findall(r"local\.(\w+)", content)) - _LOCALS_TO_SKIP


def discover_output_expressions() -> dict[str, str]:
    """Map every output declared in 012_outputs.tf to its HCL value expression.

    Reads `012_outputs.json` (JSONified at session_setup via the same `hcl_to_json`
    pipeline used for 009). hcl2json wraps each value with `${...}` — strip that so the
    expression embeds cleanly back into a downstream `terraform console` call.

    Outputs whose `value` references unguarded resources (caller_identity, EC2 IPs, etc.)
    have been refactored in `012_outputs.tf` to be passthroughs of `local.<name>` defined
    with the two-layer-defense pattern in `locals.tf`. Console can evaluate every value
    expression that this function returns.
    """
    path = Path(FP.ROOT) / JSON_012_PATH
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    expressions: dict[str, str] = {}
    for name, blocks in data.get("output", {}).items():
        raw = blocks[0]["value"]
        # Strip the hcl2json `${...}` interpolation wrapper.
        expressions[name] = raw[2:-1] if raw.startswith("${") and raw.endswith("}") else raw
    return expressions


def collect_scenarios_from_items(items) -> dict[str, str]:
    """Build `{scenario_hash: tf_modifiers}` from collected pytest items.

    Reads each item's `@pytest.mark.tfvars(...)` marker; falls back to `#NONE` for tests
    without one (matching the `generated_test_files` fixture's default).
    """
    scenarios: dict[str, str] = {}
    for item in items:
        marker = item.get_closest_marker("tfvars")
        tf_modifiers = marker.args[0] if marker else "#NONE"
        scenarios[hash_scenario(tf_modifiers)] = tf_modifiers
    return scenarios


def read_scenario_outputs(tf_modifiers: str) -> dict:
    """Read the resolved `module.connection_strings` outputs for one scenario from disk.

    Consumed by the `scenario_outputs` fixture in `tests/conftest.py`. The values were
    written by `_precompute_scenario` during `session_setup` via a single
    `terraform console` call per scenario.
    """
    cache_key = hash_templatefile_cache_key(tf_modifiers)
    outputs_path = Path(FP.CACHE_SCENARIO_DIR) / cache_key / "outputs.json"
    return json.loads(outputs_path.read_text())


## ------------------------------------------------------------------------------------
## Worker helpers
## ------------------------------------------------------------------------------------
def _expected_filenames() -> set[str]:
    """The full set of filenames a complete scenario cache directory should contain."""
    names = {"locals.json", "outputs.json"}
    for key, meta in all_template_files.items():
        names.add(_WAVE_LITE_RDS_FILENAME if key == _WAVE_LITE_RDS_KEY else f"{key}{meta['extension']}")
    return names


def _scenario_cache_complete(cache_dir: Path) -> bool:
    """True if every expected file is present in the cache dir."""
    if not cache_dir.exists():
        return False
    present = {p.name for p in cache_dir.iterdir()}
    return _expected_filenames().issubset(present)


def _load_secrets() -> dict[str, dict]:
    """Load and normalize the four secret JSON fixtures into `{category: {key: value}}`."""
    raw = {
        "tower": FP.TOWER_SECRETS,
        "groundswell": FP.GROUNDSWELL_SECRETS,
        "seqerakit": FP.SEQERAKIT_SECRETS,
        "wave_lite": FP.WAVE_LITE_SECRETS,
    }
    return {
        category: {k: v.get("value", v) for k, v in FileHelper.read_json(path).items()}
        for category, path in raw.items()
    }


def _build_template_payload(raw_expression: str, secrets: dict) -> str:
    """Strip the `${...}` wrapper from a 009.json entry and substitute secrets + tls stubs."""
    payload = raw_expression[2:-1]
    payload = _replace_refs(payload, secrets["tower"], "tower_secrets")
    payload = _replace_refs(payload, secrets["groundswell"], "groundswell_secrets")
    payload = _replace_refs(payload, secrets["seqerakit"], "seqerakit_secrets")
    payload = _replace_refs(payload, secrets["wave_lite"], "wave_lite_secrets")
    payload = _replace_refs(payload, _TLS_KEY_STUBS, "tls_connect_ssh_host_key")
    # `terraform console` treats stdin newlines as submit-this-expression markers.
    return payload.replace("\n", "")


def _render_wave_lite_rds(cache_dir: Path) -> None:
    """Render the SQL file via sedalternative.py — single-quotes break console input parsing."""
    source_path = Path(FP.ROOT) / "assets/src/wave_lite_config" / _WAVE_LITE_RDS_FILENAME
    shutil.copy(source_path, cache_dir / _WAVE_LITE_RDS_FILENAME)
    script_path = Path(FP.ROOT) / "scripts/installer/utils/sedalternative.py"
    cmd = ["python3", str(script_path), "wave_lite_test_limited", "wave_lite_test_limited_password", str(cache_dir)]
    subprocess.run(cmd, check=True, capture_output=True)  # noqa: S603  (args are hardcoded test fixtures)


## ------------------------------------------------------------------------------------
## Worker
## ------------------------------------------------------------------------------------
def _precompute_scenario(scenario_hash: str, tf_modifiers: str) -> tuple[str, float, str]:
    """Resolve locals + render all templatefiles for one scenario. Write to disk cache.

    Returns (scenario_hash, elapsed_seconds, status). Status:
      - `"hit"`: cache dir already complete
      - `"miss-ok"`: rendered successfully
      - `"miss-err: <message>"`: terraform console or parse failure
    """
    cache_key = hash_templatefile_cache_key(tf_modifiers)
    cache_dir = Path(FP.CACHE_SCENARIO_DIR) / cache_key
    start = time.time()

    if _scenario_cache_complete(cache_dir):
        return scenario_hash, time.time() - start, "hit"

    cache_dir.mkdir(parents=True, exist_ok=True)

    # Load 009 templatefile expressions + secret fixtures.
    templatefile_json = json.loads((Path(FP.ROOT) / JSON_009_PATH).read_text())
    raw_locals = templatefile_json["locals"][0]
    secrets = _load_secrets()

    # Build per-template payloads (skip wave_lite_rds — rendered separately).
    template_payloads = {
        key: _build_template_payload(raw_locals[key], secrets)
        for key in all_template_files
        if key != _WAVE_LITE_RDS_KEY and key in raw_locals
    }

    # Mega-expression: locals + every output from 012_outputs.tf + every templatefile,
    # all in one jsonencode round trip. Each output's value expression is enumerated from
    # 012_outputs.json and embedded directly — `test_outputs.py` reads the resulting map
    # from `outputs.json` to validate per-scenario output behaviour.
    locals_to_resolve = discover_referenced_locals()
    output_expressions = discover_output_expressions()
    locals_body = ", ".join(f"{n} = try(local.{n}, null)" for n in sorted(locals_to_resolve))
    outputs_body = ", ".join(f"{name} = {value_expr}" for name, value_expr in sorted(output_expressions.items()))
    templates_body = ", ".join(f"{k} = {p}" for k, p in template_payloads.items())
    expr = (
        f"jsonencode({{ "
        f"locals = {{ {locals_body} }}, "
        f"outputs = {{ {outputs_body} }}, "
        f"templates = {{ {templates_body} }} "
        f"}})"
    )

    # Per-worker tfvars + state paths so parallel processes don't fight over the default state lock.
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".tfvars",
        prefix=f"precompute-{scenario_hash}-",
        delete=False,
    ) as tf:
        # Canonicalise (whitespace-normalize + dedup): terraform rejects duplicate variable
        # assignments within a single tfvars file. Dedup is "last wins", which gives the
        # BASELINE + scenario_modifier precedence semantics.
        tf.write(normalize_whitespace(tf_modifiers))
        tfvars_path = Path(tf.name)
    state_path = Path(tempfile.gettempdir()) / f"precompute-{scenario_hash}.tfstate"

    try:
        cmd = ["terraform", "console", f"-var-file={tfvars_path}", f"-state={state_path}"]
        try:
            result = subprocess.run(  # noqa: S603  (tfvars/state paths are tempfile-generated, not user input)
                cmd,
                cwd=FP.ROOT,
                input=expr,
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            stderr_clean = re.sub(r"\x1b\[[0-9;]*m", "", e.stderr or "")
            return scenario_hash, time.time() - start, f"miss-err: rc={e.returncode}; stderr={stderr_clean[:800]}"

        try:
            parsed = json.loads(json.loads(result.stdout.strip()))
        except (json.JSONDecodeError, ValueError) as e:
            stderr_clean = re.sub(r"\x1b\[[0-9;]*m", "", result.stderr or "")
            return (
                scenario_hash,
                time.time() - start,
                (f"miss-err: json-parse {e}; stdout={result.stdout[:200]!r}; stderr={stderr_clean[:400]}"),
            )

        # Persist resolved locals (useful for debugging; not consumed by tests today).
        (cache_dir / "locals.json").write_text(json.dumps(parsed["locals"], indent=2))

        # Persist resolved `module.connection_strings` outputs — consumed by `test_outputs.py`.
        (cache_dir / "outputs.json").write_text(json.dumps(parsed["outputs"], indent=2))

        # Persist rendered templates.
        for key, content in parsed["templates"].items():
            ext = all_template_files[key]["extension"]
            (cache_dir / f"{key}{ext}").write_text(content)

        # Wave-lite-rds SQL via the sedalternative.py path.
        _render_wave_lite_rds(cache_dir)

        return scenario_hash, time.time() - start, "miss-ok"
    finally:
        tfvars_path.unlink(missing_ok=True)
        state_path.unlink(missing_ok=True)


def precompute_in_parallel(scenarios: dict[str, str], max_workers: int = 8) -> dict[str, str]:
    """Run `_precompute_scenario` over all unique scenarios in parallel. Return status map."""
    if not scenarios:
        return {}

    Path(FP.CACHE_SCENARIO_DIR).mkdir(parents=True, exist_ok=True)

    # Clear override.auto.tfvars so each worker's -var-file is the authoritative tfvars source.
    Path(FP.TFVARS_AUTO_OVERRIDE_DST).unlink(missing_ok=True)

    statuses: dict[str, str] = {}
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_precompute_scenario, h, tfvars): h for h, tfvars in scenarios.items()}
        for future in concurrent.futures.as_completed(futures):
            h = futures[future]
            try:
                _, _elapsed, status = future.result()
            except Exception as e:
                status = f"miss-err: worker-crash {e}"
            statuses[h] = status

    return statuses


## ------------------------------------------------------------------------------------
## INDEX.md generation
## ------------------------------------------------------------------------------------
_BASELINE_CONST_NAMES = {"BASELINE_ASSERTIONS"}


def _parse_function_ast(func) -> ast.Module | None:
    """Return the parsed AST of `func`'s source, or `None` if it can't be obtained."""
    try:
        source = textwrap.dedent(inspect.getsource(func))
    except (OSError, TypeError):
        return None
    try:
        return ast.parse(source)
    except SyntaxError:
        return None


def _called_name(call: ast.Call) -> str | None:
    """Return the simple/attribute callee name of a `Call` node, or `None`."""
    func_node = call.func
    if isinstance(func_node, ast.Attribute):
        return func_node.attr
    if isinstance(func_node, ast.Name):
        return func_node.id
    return None


def _collect_delta_constant_names(tree: ast.AST) -> set[str]:
    """Names of constants passed to `merge_deltas(...)`, excluding the OFF baseline."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or _called_name(node) != "merge_deltas":
            continue
        for arg in node.args:
            if isinstance(arg, ast.Name) and arg.id not in _BASELINE_CONST_NAMES:
                names.add(arg.id)
    return names


def _templates_from_delta_constant(const: object) -> set[str]:
    """Template keys with non-empty present/omitted in a single delta-constant dict."""
    if not isinstance(const, dict):
        return set()
    templates: set[str] = set()
    for template, parts in const.items():
        if not isinstance(parts, dict):
            continue
        if (parts.get("present") or {}) or (parts.get("omitted") or set()):
            templates.add(template)
    return templates


def _compute_required_templates(item) -> list[str]:
    """Static analysis: derive the minimum file set a test asserts on.

    Walks the test function's AST for `merge_deltas(...)` calls, collects the `Name` args
    that aren't `BASELINE_ASSERTIONS`, resolves each name against the test module's
    globals, and unions the template keys of every resolved delta dict.

    Returns sorted template names, or `[]` if the test doesn't follow the merge_deltas
    pattern (legacy or non-delta tests).
    """
    func = getattr(item, "function", None)
    if func is None:
        return []
    tree = _parse_function_ast(func)
    if tree is None:
        return []
    constant_names = _collect_delta_constant_names(tree)
    if not constant_names:
        return []
    globals_ = getattr(func, "__globals__", {})
    templates: set[str] = set()
    for name in constant_names:
        templates |= _templates_from_delta_constant(globals_.get(name))
    return sorted(templates)


def write_scenario_index(items) -> Path:
    """Write `tests/.scenario_cache/INDEX.md` mapping each collected test to its cache folder.

    Per-test rows are grouped by source file. Each row links the cache hash to its folder
    via a relative markdown link (`./<hash>/`). Tests whose precompute failed get a
    `⚠️ precompute failed` suffix so the broken link is visually obvious.
    """
    by_file: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for item in items:
        marker = item.get_closest_marker("tfvars")
        tf_modifiers = marker.args[0] if marker else "#NONE"
        h = hash_templatefile_cache_key(tf_modifiers)
        rel_file = str(Path(str(item.fspath)).relative_to(FP.ROOT))
        by_file[rel_file].append((item.name, h))

    cache_root = Path(FP.CACHE_SCENARIO_DIR)
    cache_root.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Scenario Cache Index",
        "",
        f"_Generated: {datetime.now(tz=UTC).strftime('%Y-%m-%d %H:%M UTC')}. Regenerated every test session._",
        "",
    ]

    for fpath in sorted(by_file):
        lines.append(f"## {fpath}")
        lines.append("")
        lines.append("| Test | Cache Folder |")
        lines.append("|------|--------------|")
        for test_name, h in sorted(by_file[fpath]):
            folder_exists = (cache_root / h).exists()
            suffix = "" if folder_exists else " ⚠️ precompute failed"
            lines.append(f"| `{test_name}` | [`{h}`](./{h}/){suffix} |")
        lines.append("")

    # Minimum file set per test — derived from each test's `merge_deltas(...)` arg names,
    # excluding `BASELINE_ASSERTIONS`. Tests not following the delta pattern (legacy
    # `generate_assertions_all_*` flow, or tests with no delta assertions at all) are
    # omitted from this section.
    by_file_min: dict[str, list[tuple[str, list[str]]]] = defaultdict(list)
    for item in items:
        required = _compute_required_templates(item)
        if not required:
            continue
        rel_file = str(Path(str(item.fspath)).relative_to(FP.ROOT))
        by_file_min[rel_file].append((item.name, required))

    if by_file_min:
        lines.append("---")
        lines.append("")
        lines.append("## Minimum file set per test")
        lines.append("")
        lines.append(
            "_Files each test explicitly asserts on, derived from `merge_deltas(...)` call sites "
            "(excluding `BASELINE_ASSERTIONS`). Tests using the legacy "
            "`generate_assertions_all_*` pattern are not listed here._",
        )
        lines.append("")
        for fpath in sorted(by_file_min):
            lines.append(f"### {fpath}")
            lines.append("")
            lines.append("| Test | Required Templates |")
            lines.append("|------|--------------------|")
            for test_name, templates in sorted(by_file_min[fpath]):
                joined = ", ".join(f"`{t}`" for t in templates)
                lines.append(f"| `{test_name}` | {joined} |")
            lines.append("")

    index_path = cache_root / "INDEX.md"
    index_path.write_text("\n".join(lines))
    return index_path
