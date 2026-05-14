"""Regression test: every local referenced from `009_define_file_templates.tf` must resolve via `terraform console`.

Companion to the #353 console-based templatefile rendering refactor. The fast path
(`stage_tfvars` + `generate_tc_files(None, …)`) pipes templatefile arg maps through
`terraform console`, which expects every `local.<name>` reference in those maps to
evaluate to a concrete value. A local whose definition mixes a tfvars-known branch
with a resource-attribute branch in a ternary will collapse to `(known after apply)`
under console-without-plan (HCL evaluates both ternary branches eagerly) — and the
rendered template would silently contain the literal text `(known after apply)`.

This test scans the raw source of `009_define_file_templates.tf` for every `local.<name>`
reference, evaluates each via `terraform console`, and fails on any result of
`(known after apply)`. Catches the silent-corruption failure mode at PR time.

If this test fails:
  1. Find the offending local's definition (likely in `000_main.tf`).
  2. Refactor it so no branch references a resource attribute, OR
  3. Wrap resource refs in `var.use_mocks ? null : try(<ref>, null)` (see #353 addendum).
"""

import re

import pytest
from tests.utils.config import FP
from tests.utils.filehandling import FileHelper
from tests.utils.terraform.executor import (
    TF_CONSOLE_UNKNOWN_MARKER,
    console_evaluate_local,
)


# Locals the test framework substitutes in Python *before* the templatefile payload reaches
# `terraform console`. They're not expected to be console-resolvable — the framework guarantees
# they never need to be. See `tests/utils/terraform/template_generator.py:replace_vars_in_templatefile`.
_LOCALS_SUBSTITUTED_BY_PYTHON = {
    "tower_secrets",
    "groundswell_secrets",
    "seqerakit_secrets",
    "wave_lite_secrets",
}

# Locals known to be resource-dependent (their definition is a ternary whose branches reference
# resources/data sources that don't exist under console-without-plan). Currently silent because
# every templatefile that references one of these carries a stub `{}` assertion block in
# `tests/datafiles/expected_results/expected_results.py` — the corrupt rendering isn't checked.
# Deferred for the defensive-refactor work tracked in
# `.github/issue-drafts/in-review/make_locals_more_defensive.md`. Remove from this set as each
# local gets the two-layer-defense pattern applied.
_LOCALS_DEFERRED_TO_DEFENSIVE_REFACTOR = {
    "vpc_id",
    "dns_instance_ip",
    "ssh_key_name",
    "sg_ec2_final",  # regex false positive: only referenced from a commented-out line in 009.tf
}

_ALLOWLISTED_LOCALS = _LOCALS_SUBSTITUTED_BY_PYTHON | _LOCALS_DEFERRED_TO_DEFENSIVE_REFACTOR


def _locals_to_check() -> set[str]:
    """Locals referenced in 009.tf, minus the documented allowlists."""
    raw = FileHelper.read_file(f"{FP.ROOT}/009_define_file_templates.tf")
    referenced = set(re.findall(r"\blocal\.(\w+)", raw))
    return referenced - _ALLOWLISTED_LOCALS


@pytest.mark.local
@pytest.mark.framework
@pytest.mark.parametrize("local_name", sorted(_locals_to_check()))
def test_local_resolves_via_console(session_setup, local_name):
    """Every non-allowlisted local referenced from 009 must evaluate to a concrete value under console-without-plan."""
    result = console_evaluate_local(local_name)
    assert result != TF_CONSOLE_UNKNOWN_MARKER, (
        f"local.{local_name} resolves to {TF_CONSOLE_UNKNOWN_MARKER!r} under `terraform console`.\n"
        f"This means any templatefile that references it via the fast path (#353) would silently\n"
        f"render the literal text {TF_CONSOLE_UNKNOWN_MARKER!r} into the generated config file.\n\n"
        f"Likely cause: local.{local_name}'s definition contains a ternary where at least one branch\n"
        f"references a resource or downstream module that doesn't exist without `terraform apply`.\n"
        f"Fix by refactoring the local so no branch touches a resource attribute, OR by wrapping the\n"
        f"resource ref in `var.use_mocks ? null : try(<ref>, null)` (the two-layer defense pattern\n"
        f'documented at 000_main.tf:module "connection_strings").\n\n'
        f"If this is a deliberate known-gap rather than a new violation, add `{local_name}` to the\n"
        f"appropriate allowlist set at the top of this test file with a comment explaining why."
    )
