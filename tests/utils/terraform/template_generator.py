"""Runtime cache-reader for pre-rendered templatefiles.

Tests no longer invoke `terraform console` at runtime. Every templatefile is rendered
upfront by `tests/utils/terraform/precompute.py` during `session_setup`, in parallel per
scenario. This module just reads the per-scenario cache directory and returns the result
in the shape consumers expect.

If `generate_tc_files` is called for a scenario whose precompute failed, the missing-file
read raises `FileNotFoundError` — diagnosed via `tests/.scenario_cache/INDEX.md`, which
flags failed scenarios with `⚠️ precompute failed`.
"""

from pathlib import Path

from tests.utils.cache.cache import hash_templatefile_cache_key
from tests.utils.config import FP, all_template_files


# `all_template_files` key uses underscores; the actual on-disk filename uses hyphens.
_WAVE_LITE_RDS_KEY = "wave_lite_rds"
_WAVE_LITE_RDS_FILENAME = "wave-lite-rds.sql"


def _cache_filename(key: str, extension: str) -> str:
    """Map a template key to its on-disk filename inside the scenario cache directory."""
    if key == _WAVE_LITE_RDS_KEY:
        return _WAVE_LITE_RDS_FILENAME
    return f"{key}{extension}"


def generate_tc_files(plan, testcase_name, tf_modifiers):
    """Read every pre-rendered templatefile from this scenario's cache directory.

    Args:
        plan: Unused. Kept in the signature for back-compat with callers that haven't
            migrated. Will be dropped with the TCValues refactor.
        testcase_name: Unused. Kept in the signature for back-compat. Same disposition.
        tf_modifiers: The per-test tfvars block (from `@pytest.mark.tfvars(...)`). Used
            to compute the cache directory.

    Returns:
        `{template_key: {extension, read_type, content, filepath, validation_type}}` —
        the shape `verify_all_assertions` and the testcontainer tests expect.

    Raises:
        FileNotFoundError: a cache file is missing. Means precompute failed for this
            scenario — check `tests/.scenario_cache/INDEX.md`.
    """
    cache_key = hash_templatefile_cache_key(tf_modifiers)
    cache_dir = Path(FP.CACHE_SCENARIO_DIR) / cache_key

    result: dict[str, dict] = {}
    for key, meta in all_template_files.items():
        filename = _cache_filename(key, meta["extension"])
        filepath = cache_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(
                f"Expected pre-rendered template at {filepath}. "
                f"Precompute may have failed for this scenario — check tests/.scenario_cache/INDEX.md."
            )
        read_type = meta["read_type"]
        result[key] = {
            "extension": meta["extension"],
            "read_type": read_type,
            "content": read_type(str(filepath)),
            "filepath": str(filepath),
            "validation_type": meta["validation_type"],
        }
    return result
