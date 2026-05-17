import functools
import hashlib
from pathlib import Path
import re

from tests.utils.config import FP
from tests.utils.filehandling import FileHelper


## ------------------------------------------------------------------------------------
## Cache Utility Functions
## ------------------------------------------------------------------------------------
def hash_cache_key(tf_modifiers: str, qualifier: str = "") -> str:
    """Generate SHA-256 hash of override data and tfvars content for cache key.

    Used by the legacy plan-based path (`prepare_plan`) for the per-scenario plan cache
    under `tests/.plan_cache/`. The templatefile-rendering path uses
    `hash_templatefile_cache_key` instead.
    """
    tfvars_base = FileHelper.read_file(FP.TFVARS_BASE).strip()
    tfvars_override = FileHelper.read_file(FP.TFVARS_BASE_OVERRIDE_DST).strip()
    tf_modifiers = tf_modifiers.strip()
    qualifier = qualifier.strip()

    # Create combined cache key: All 3 tfvars layers + qualifier
    combined_content = tfvars_base + tfvars_override + tf_modifiers + qualifier
    return hashlib.sha256(combined_content.encode("utf-8")).hexdigest()[:16]


def normalize_whitespace(tf_modifiers: str) -> str:
    r"""Canonicalise tfvars so logically-identical inputs produce the same hash.

    Also ensures the result is safe to write to a single tfvars file (terraform forbids
    duplicate variable assignments within one file).

    Two passes:

    1. **Whitespace normalize** — per line, collapse runs of internal whitespace to a
       single space and `.strip()` leading/trailing whitespace.

    2. **Dedup** — for any `key = value` assignment that appears more than once in the
       input, keep only the LAST occurrence. Non-assignment lines (comments, blanks,
       heredoc starters, complex syntax) are preserved in order.

    The "last wins" rule is what enables the `BASELINE + scenario_modifier` pattern:
    if `scenario_modifier` re-declares a key from `BASELINE`, the scenario's value
    wins (matches the user's stated precedence rule).

    Newlines are preserved. `#` comments and blank lines are NOT stripped — they're
    content; collapsing them would surprise anyone who documented a scenario deliberately.

    Safe because terraform's HCL parser is whitespace-insensitive for simple assignments
    and none of the project's `@pytest.mark.tfvars(...)` markers use heredocs or
    multi-line strings where indentation would be load-bearing.
    """
    # Pass 1: per-line whitespace normalize.
    lines = [re.sub(r"\s+", " ", line).strip() for line in tf_modifiers.splitlines()]

    # Pass 2: dedup — find last occurrence of each `key = …` line.
    assignment_pattern = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=")
    last_index: dict[str, int] = {}
    for i, line in enumerate(lines):
        m = assignment_pattern.match(line)
        if m:
            last_index[m.group(1)] = i

    keep_indices = set(last_index.values())
    result: list[str] = []
    for i, line in enumerate(lines):
        if assignment_pattern.match(line) and i not in keep_indices:
            continue  # earlier duplicate, drop
        result.append(line)
    return "\n".join(result)


def hash_scenario(tf_modifiers: str) -> str:
    """SHA-256 of a single scenario's whitespace-normalized tf_modifiers string.

    Used to dedupe identical tfvars across tests at collection time. Independent from
    `hash_templatefile_cache_key` which also folds in static disk state — that one is
    the actual cache-directory key; this one is just for in-memory dedup.
    """
    normalized = normalize_whitespace(tf_modifiers).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


@functools.lru_cache(maxsize=1)
def _compute_static_hash_part() -> str:
    """Hash of disk-resident inputs that affect rendered templatefile content.

    Folds in:
      - Project tfvars files (terraform.tfvars + base-overrides.auto.tfvars)
      - The four secret JSON fixtures (tower / groundswell / seqerakit / wave_lite)
      - Locals source (`000_main.tf`) and template source (`009_define_file_templates.tf`)
      - Every `.tpl` file under `assets/src/`

    Changing any of these invalidates every templatefile cache entry. Cached per-process
    via lru_cache — these inputs are stable across a pytest session. Workers (separate
    processes) compute this once each on first call.
    """
    parts = [
        FileHelper.read_file(FP.TFVARS_BASE),
        FileHelper.read_file(FP.TFVARS_BASE_OVERRIDE_DST),
        FileHelper.read_file(FP.TOWER_SECRETS),
        FileHelper.read_file(FP.GROUNDSWELL_SECRETS),
        FileHelper.read_file(FP.SEQERAKIT_SECRETS),
        FileHelper.read_file(FP.WAVE_LITE_SECRETS),
        FileHelper.read_file(f"{FP.ROOT}/000_main.tf"),
        FileHelper.read_file(f"{FP.ROOT}/009_define_file_templates.tf"),
    ]
    parts.extend(tpl.read_text() for tpl in sorted(Path(f"{FP.ROOT}/assets/src").rglob("*.tpl")))
    return hashlib.sha256("".join(parts).encode("utf-8")).hexdigest()


def hash_templatefile_cache_key(tf_modifiers: str) -> str:
    """Disk-only cache key for rendered templatefiles. No terraform console required.

    Combines the static-disk-state hash with the per-test tfvars modifiers. Both
    precompute workers and runtime `generate_tc_files` compute this the same way →
    same cache directory under `tests/.scenario_cache/` → cross-test reuse works
    whenever two tests' tfvars match byte-for-byte.
    """
    normalized = normalize_whitespace(tf_modifiers).strip()
    return hashlib.sha256((_compute_static_hash_part() + normalized).encode("utf-8")).hexdigest()[:16]
