"""Regression tests for single-variable validation blocks migrated from check_configuration.py.

Each migration adds:
  1. A `validation` block on the variable in `variables.tf`
  2. A new bad-value line in `tf_modifiers` below
  3. A new entry in `expected_offenders`

Terraform aggregates all variable-validation failures from a single plan invocation,
so one test exercises every migrated validation. When a new validation is migrated,
extend `tf_modifiers` and `expected_offenders` together.

NOTE: assertions match against variable NAMES (not full error messages) so error-message
wording can be edited later without breaking the test.
"""

import pytest
from tests.utils.terraform.executor import prepare_plan


@pytest.mark.local
def test_single_variable_validations_reject_bad_values(session_setup):
    """Confirm each migrated single-variable validation block rejects its non-compliant value."""
    tf_modifiers = """
        tower_server_url                        = "http://example.com"
        tower_root_users                        = "REPLACE_ME"
        tower_db_url                            = "jdbc:mysql://example.com:3306/tower"
        tower_db_driver                         = "wrong.driver"
        tower_db_dialect                        = "wrong.dialect"
        db_engine_version                       = "5.7"
        db_container_engine_version             = "5.7"
        tower_container_version                 = "v24.0.0"
        data_studio_eligible_workspaces         = "abc"
        data_studio_ssh_eligible_workspaces     = "1,abc"
        pipeline_versioning_eligible_workspaces = "12 34"
    """

    with pytest.raises(RuntimeError) as excinfo:
        prepare_plan(tf_modifiers)

    error_text = str(excinfo.value)
    expected_offenders = [
        "tower_server_url",
        "tower_root_users",
        "tower_db_url",
        "tower_db_driver",
        "tower_db_dialect",
        "db_engine_version",
        "db_container_engine_version",
        "tower_container_version",
        "data_studio_eligible_workspaces",
        "data_studio_ssh_eligible_workspaces",
        "pipeline_versioning_eligible_workspaces",
    ]

    # For each variable passed with a non-compliant value, confirm Terraform's plan stderr
    # mentions the variable name (i.e., its validation block fired and reported it).
    for var_name in expected_offenders:
        assert var_name in error_text, (
            f"`{var_name}` does not have a compliant value, but Terraform did not report "
            f"it as a validation failure.\n\nFull stderr:\n{error_text}"
        )
