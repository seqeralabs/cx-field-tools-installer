"""Regression test: every local referenced from `009_define_file_templates.tf` must resolve via `terraform console`.

Companion to the #353 console-based templatefile rendering refactor. The fast path
(`stage_tfvars` + `generate_tc_files(None, …)`) pipes templatefile arg maps through
`terraform console`, which expects every `local.<name>` reference in those maps to
evaluate to a concrete value. A local whose definition mixes a tfvars-known branch
with a resource-attribute branch in a ternary will collapse to `(known after apply)`
under console-without-plan (HCL evaluates both ternary branches eagerly) — and the
rendered template would silently contain the literal text `(known after apply)`.

This test scans the raw source of `009_define_file_templates.tf` for every `local.<name>`
reference and verifies — using the resolved values written to each scenario's
`tests/.scenario_cache/{hash}/locals.json` by the parallel precompute (see
`tests/utils/terraform/precompute.py`) — that the local resolved to a non-null value
in EVERY collected scenario. Because the precompute wraps each lookup in
`try(local.X, null)`, a `null` in `locals.json` is exactly the silent-corruption case
the check guards against.

Checking every scenario rather than just one catches the case where a local resolves
fine under tfvars combo A but fails under combo B. Disk reads are ~ms scale, so the
extra coverage is essentially free relative to the prior implementation (which paid
one ~1.5 s `terraform console` startup per parametrized case).

If this test fails:
  1. Find the offending local's definition (likely in `000_main.tf`).
  2. Refactor it so no branch references a resource attribute, OR
  3. Wrap resource refs in `var.use_mocks ? null : try(<ref>, null)` (see #353 addendum).
"""

import json
from pathlib import Path
import re

import pytest
from tests.utils.config import FP
from tests.utils.filehandling import FileHelper


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
    """Every non-allowlisted local from 009 must resolve to a non-null value in every scenario's `locals.json`."""
    cache_root = Path(FP.CACHE_SCENARIO_DIR)
    scenario_dirs = sorted(d for d in cache_root.iterdir() if d.is_dir())
    assert scenario_dirs, (
        f"No scenario cache folders found under {cache_root}. Precompute may not have run — check session_setup output."
    )

    failures: list[str] = []
    for scenario_dir in scenario_dirs:
        locals_path = scenario_dir / "locals.json"
        if not locals_path.exists():
            failures.append(f"  - {scenario_dir.name}: locals.json missing")
            continue
        locals_map = json.loads(locals_path.read_text())
        if local_name not in locals_map:
            failures.append(f"  - {scenario_dir.name}: key absent (precompute didn't request it?)")
            continue
        if locals_map[local_name] is None:
            failures.append(f"  - {scenario_dir.name}: value is null (precompute's try() fallback fired)")

    assert not failures, (
        f"local.{local_name} failed to resolve in {len(failures)} of {len(scenario_dirs)} scenarios:\n"
        f"{chr(10).join(failures[:5])}\n"
        f"{'  ... (more)' if len(failures) > 5 else ''}\n\n"
        f"A null value means the precompute's `try(local.{local_name}, null)` fell back — the local's\n"
        f"definition contains a ternary where at least one branch references a resource or downstream\n"
        f"module that doesn't exist without `terraform apply`. Fix by refactoring the local so no branch\n"
        f"touches a resource attribute, OR by wrapping the resource ref in `var.use_mocks ? null : try(<ref>, null)`\n"
        f'(the two-layer defense pattern documented at 000_main.tf:module "connection_strings" and locals.tf).\n\n'
        f"If this is a deliberate known-gap rather than a new violation, add `{local_name}` to the\n"
        f"appropriate allowlist set at the top of this test file with a comment explaining why."
    )
