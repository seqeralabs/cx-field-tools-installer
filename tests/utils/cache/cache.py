import hashlib
import re

from tests.utils.config import FP
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
