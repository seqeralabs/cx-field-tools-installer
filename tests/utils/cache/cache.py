import hashlib
import re
from datetime import datetime
from pathlib import Path

from tests.utils.config import FP, TCValues
from tests.utils.filehandling import FileHelper


## ------------------------------------------------------------------------------------
## Cache Utility Functions
## ------------------------------------------------------------------------------------
def hash_cache_key(tf_modifiers: str, qualifier: str = "") -> str:
    """Generate SHA-256 hash of override data and tfvars content for cache key."""

    tfvars_base = FileHelper.read_file(FP.TFVARS_BASE).strip()
    tfvars_override = FileHelper.read_file(FP.TFVARS_BASE_OVERRIDE_DST).strip()
    tf_modifiers = tf_modifiers.strip()
    qualifier = qualifier.strip()

    # Create combined cache key: All 3 tfvars layers + qualifier
    combined_content = tfvars_base + tfvars_override + tf_modifiers + qualifier
    return hashlib.sha256(combined_content.encode("utf-8")).hexdigest()[:16]


def normalize_whitespace(tf_modifiers: str) -> str:
    """
    Purges intermediate whitespace (extra space makes same keys hash to different values).
    Convert multiple spaces to single space (ASSUMPTION: Python tabs insert spaces!)
    NOTE: Need to keep `\n` to not break HCL formatting expectations.
    """
    return "\n".join(re.sub(r"\s+", " ", line) for line in tf_modifiers.splitlines())


def hash_tc_values(tc: TCValues) -> str:
    """Generate hash from TC values. Single responsibility."""
    content = (
        str(tc.vars)
        + str(tc.outputs)
        + str(tc.tower_secrets)
        + str(tc.groundswell_secrets)
        + str(tc.seqerakit_secrets)
        + str(tc.wave_lite_secrets)
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def create_templatefile_cache_folder(tc: TCValues, testcase_name: str) -> str:
    """
    Create a folder to store generated templatefiles for reuse.
    """
    hashed_tc = hash_tc_values(tc)

    # Make cache folder if missing
    cache_dir = f"{FP.CACHE_TEMPLATEFILE_DIR}/{testcase_name}__{hashed_tc}"
    folder_path = Path(cache_dir)
    folder_path.mkdir(parents=True, exist_ok=True)

    # Timestamp cant be in name -- will affect cache check in `generate_templatefile`. Write timestamp in the folder instead.
    existing_timestamps = list(folder_path.glob(".timestamp*"))
    if not existing_timestamps:
        timestamp = datetime.now().strftime("%Y-%m-%d--%H:%M:%S")
        timestamp_file = folder_path / f".timestamp--{timestamp}"
        timestamp_file.write_text(timestamp)

    return cache_dir
