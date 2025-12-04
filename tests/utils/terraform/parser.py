from typing import Any, Dict

from tests.utils.config import (
    FP,
    TCValues,
)
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


def extract_config_values(plan: dict) -> TCValues:
    """
    Extract and flatten JSON entities from various input sources. Used to generate templatefiles.

      1. 'terraform plan' variables & outputs.
      2. testing secrets

    WARNING: Plan booleans are Python True/False, not terraform "true"/"false".
    """
    vars_dict = plan["variables"]
    outputs_dict = plan["planned_values"]["outputs"]
    tower_secrets = FileHelper.read_json(FP.TOWER_SECRETS)
    groundswell_secrets = FileHelper.read_json(FP.GROUNDSWELL_SECRETS)
    seqerakit_secrets = FileHelper.read_json(FP.SEQERAKIT_SECRETS)
    wave_lite_secrets = FileHelper.read_json(FP.WAVE_LITE_SECRETS)

    # Flatten nested "value" keys: {"key": {"value": "val"}} -> {"key": "val"}
    TC = TCValues()
    TC.vars = {k: v.get("value", v) for k, v in vars_dict.items()}
    TC.outputs = {k: v.get("value", v) for k, v in outputs_dict.items()}
    TC.tower_secrets = {k: v.get("value", v) for k, v in tower_secrets.items()}
    TC.groundswell_secrets = {k: v.get("value", v) for k, v in groundswell_secrets.items()}
    TC.seqerakit_secrets = {k: v.get("value", v) for k, v in seqerakit_secrets.items()}
    TC.wave_lite_secrets = {k: v.get("value", v) for k, v in wave_lite_secrets.items()}

    return TC
