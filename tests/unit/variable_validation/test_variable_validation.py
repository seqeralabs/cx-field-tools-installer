"""Regression tests for single-variable validation blocks migrated from check_configuration.py.

Structure: rounds.
  - Round N contains each variable's Nth bad value (where it has one).
  - Variables with K criteria appear in rounds 1..K.
  - Each round runs ONE `terraform plan` and asserts every variable in that round's
    bad-value dict is reported in stderr.

Adding a new criterion → add an entry to the appropriate round dict (or add a new round
if you've introduced a variable with more criteria than any existing one).

Trade-offs vs. one-criterion-per-parametrize:
  - Fewer pytest cases (3 vs 20+) → much faster CI run (~3-6s vs ~20-40s)
  - Each case asserts multiple validations in a single plan invocation
  - Failure message reports the round + specific variable + criterion, so per-criterion
    diagnostics are preserved when something breaks
"""

import pytest
from tests.utils.terraform.executor import prepare_plan


# Each round: {variable_name: (bad_value, criterion_description)}
SCENARIOS: dict[str, dict[str, tuple[str, str]]] = {
    "round_1": {
        "tower_server_url": ("http://example.com", "http prefix"),
        "tower_root_users": ("REPLACE_ME", "placeholder value"),
        "tower_db_url": ("jdbc:mysql://example.com:3306/tower", "jdbc: prefix"),
        "tower_db_driver": ("wrong.driver", "non-matching driver"),
        "tower_db_dialect": ("wrong.dialect", "non-matching dialect"),
        "db_engine_version": ("5.7", "major version below 8"),
        "db_container_engine_version": ("5.7", "major version below 8"),
        "tower_container_version": ("25.3.0", "missing 'v' prefix"),
        "data_studio_eligible_workspaces": ("abc", "non-numeric value"),
        "data_studio_ssh_eligible_workspaces": ("abc", "non-numeric value"),
        "pipeline_versioning_eligible_workspaces": ("abc", "non-numeric value"),
        "private_cacert_bucket_prefix": ("my-bucket", "missing s3:// prefix"),
    },
    "round_2": {
        "tower_server_url": ("https://example.com", "https prefix"),
        "tower_root_users": ("", "empty string"),
        "tower_db_url": ("mysql://example.com:3306/tower", "mysql: prefix"),
        "db_engine_version": ("7.4", "major version below 8 (boundary)"),
        "tower_container_version": ("v24.0.0", "major version below 25"),
        "data_studio_eligible_workspaces": ("1,abc", "mixed numeric/non-numeric"),
        "data_studio_ssh_eligible_workspaces": ("1,,2", "double comma"),
        "pipeline_versioning_eligible_workspaces": ("12 34", "space breaks the CSV"),
    },
    "round_3": {
        "tower_container_version": ("vfoo", "non-numeric after 'v'"),
        "data_studio_eligible_workspaces": ("12 34", "space breaks the CSV"),
    },
}


@pytest.mark.local
@pytest.mark.variable_validation
@pytest.mark.parametrize("scenario_name", list(SCENARIOS.keys()))
def test_validation_rejects_bad_values(session_setup, scenario_name):
    """For each round, fire one plan with all that round's bad values and assert every entry is rejected.

    `session_setup` is referenced to enforce AWS preflight ordering; the var is unused inside the body.
    """
    scenario = SCENARIOS[scenario_name]
    tf_modifiers = "\n".join(f'{name} = "{value}"' for name, (value, _) in scenario.items())

    with pytest.raises(RuntimeError) as excinfo:
        prepare_plan(tf_modifiers)

    error_text = str(excinfo.value)
    for var_name, (bad_value, criterion) in scenario.items():
        assert var_name in error_text, (
            f"In {scenario_name!r}: `{var_name}` set to {bad_value!r} (criterion: {criterion}) "
            f"did not trigger validation.\n\nFull stderr:\n{error_text}"
        )
