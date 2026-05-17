"""OFF baseline + per-feature delta constants for the assertion retrofit.

`OFF_BASELINE` is a tfvars string that turns off every feature that
`tests/datafiles/generate_core_data.sh` enables by default via
`base-overrides.auto.tfvars`. Tests stage this directly to render the off-state,
or concatenate `OFF_BASELINE + "flag_X = true"` to activate one feature on top.

Per-feature delta constants (e.g. `STUDIOS_PATH_ROUTING_ON`) get added below as
tests migrate to the new pattern. Each is a nested dict keyed by template name —
`{template_name: {key_or_path: value}}` — consumable by the `present` parameter
of `assert_kv_delta` / `assert_yaml_delta` / `assert_text_delta`.

Co-located with `test_config_file_content.py` so the test file stays focused on
test logic and the constants stay focused on expected-state declarations.
"""

OFF_BASELINE = """
    flag_use_aws_ses_iam_integration    = false
    flag_use_existing_smtp              = true
    flag_enable_groundswell             = false
    flag_data_explorer_enabled          = false
    flag_enable_data_studio             = false
    flag_use_wave                       = false
    flag_use_wave_lite                  = false
    flag_allow_aws_instance_credentials = false
    tower_enable_openapi                = false
    tower_enable_pipeline_versioning    = false
    flag_tower_enable_participant_auto_create_user = false
    flag_tower_enable_member_auto_create_user      = false
    tower_workflow_cleanup_enabled                 = false
"""
