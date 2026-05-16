from typing import Any

from tests.utils.config import (
    FP,
    TCValues,
)
from tests.utils.filehandling import FileHelper
from tests.utils.terraform.executor import extract_module_outputs_via_console


def get_reconciled_tfvars() -> dict[str, Any]:
    """Return single consolidated tfvars by merging overrides into base.

    - FP.TFVARS_BASE
    - FP.TFVARS_BASE_OVERRIDE_DST
    - FP.TFVARS_AUTO_OVERRIDE_DST
    """
    tfvars = FileHelper.parse_kv(FP.TFVARS_BASE)
    base_overrides = FileHelper.parse_kv(FP.TFVARS_BASE_OVERRIDE_DST)
    test_overrides = FileHelper.parse_kv(FP.TFVARS_AUTO_OVERRIDE_DST)

    tfvars.update({k: base_overrides[k] for k in base_overrides})
    tfvars.update({k: test_overrides[k] for k in test_overrides})

    return tfvars


def extract_config_values(plan: dict | None = None) -> TCValues:
    """Build a TCValues bundle for templatefile substitutions.

    Two modes:
      - `plan` is a dict: derive `vars` and `outputs` from the plan JSON (legacy path,
        required for tests that also validate plan-derived state).
      - `plan` is None: derive `vars` from the reconciled on-disk tfvars and `outputs`
        from a single `terraform console` call (fast path; saves ~30s on cold caches —
        see #353 addendum). The caller is responsible for having staged the tfvars
        (e.g. via `stage_tfvars`) before invoking this function.

    The TCValues shape is identical in both modes; downstream substitution code is unchanged.

    WARNING: Plan booleans are Python True/False, not terraform "true"/"false".
    """
    if plan is not None:
        # Flatten nested "value" keys: {"key": {"value": "val"}} -> {"key": "val"}
        vars_extracted = {k: v.get("value", v) for k, v in plan["variables"].items()}
        outputs_extracted = {k: v.get("value", v) for k, v in plan["planned_values"]["outputs"].items()}
    else:
        vars_extracted = get_reconciled_tfvars()
        outputs_extracted = extract_module_outputs_via_console()

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
