from tests.utils.config import FP, TCValues
from tests.utils.filehandling import FileHelper


def extract_config_values(plan: dict) -> TCValues:
    """Build a TCValues bundle from a terraform plan JSON.

    Used by the legacy plan-based test path (`test_outputs.py`) that validates the
    contents of `terraform plan` output directly. The templatefile-rendering path no
    longer goes through this function — it uses the precomputed scenario cache
    populated by `tests/utils/terraform/precompute.py`.

    WARNING: Plan booleans are Python True/False, not terraform "true"/"false".
    """
    # Flatten nested "value" keys: {"key": {"value": "val"}} -> {"key": "val"}
    vars_extracted = {k: v.get("value", v) for k, v in plan["variables"].items()}
    outputs_extracted = {k: v.get("value", v) for k, v in plan["planned_values"]["outputs"].items()}

    tower_secrets = FileHelper.read_json(FP.TOWER_SECRETS)
    groundswell_secrets = FileHelper.read_json(FP.GROUNDSWELL_SECRETS)
    seqerakit_secrets = FileHelper.read_json(FP.SEQERAKIT_SECRETS)
    wave_lite_secrets = FileHelper.read_json(FP.WAVE_LITE_SECRETS)

    tc = TCValues()
    tc.vars = vars_extracted
    tc.outputs = outputs_extracted
    tc.tower_secrets = {k: v.get("value", v) for k, v in tower_secrets.items()}
    tc.groundswell_secrets = {k: v.get("value", v) for k, v in groundswell_secrets.items()}
    tc.seqerakit_secrets = {k: v.get("value", v) for k, v in seqerakit_secrets.items()}
    tc.wave_lite_secrets = {k: v.get("value", v) for k, v in wave_lite_secrets.items()}

    return tc
