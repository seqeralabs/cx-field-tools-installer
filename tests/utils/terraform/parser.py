from typing import Any, Dict

from tests.utils.config import FP
from tests.utils.filehandling import FileHelper


def get_reconciled_tfvars() -> Dict[str, Any]:
    """
    Return single consolidated tfvars (merge overrides into base):
    - FP.TFVARS_BASE
    - FP.TFVARS_BASE_OVERRIDE_DST
    - FP.TFVARS_AUTO_OVERRIDE_DST
    """
    tfvars = FileHelper.parse_kv(FP.TFVARS_BASE)
    base_overrides = FileHelper.parse_kv(FP.TFVARS_BASE_OVERRIDE_DST)
    test_overrides = FileHelper.parse_kv(FP.TFVARS_AUTO_OVERRIDE_DST)

    tfvars.update({k: base_overrides[k] for k in base_overrides.keys()})
    tfvars.update({k: test_overrides[k] for k in test_overrides.keys()})

    return tfvars
