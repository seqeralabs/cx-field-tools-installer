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
    r"""Purge intermediate whitespace (extra space makes same keys hash to different values).

    Convert multiple spaces to single space (ASSUMPTION: Python tabs insert spaces!)
    NOTE: Need to keep `\n` to not break HCL formatting expectations.
    """
    return "\n".join(re.sub(r"\s+", " ", line) for line in tf_modifiers.splitlines())


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
