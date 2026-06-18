import pytest
from tests.unit.config_files.expected_deltas import (
    AWS_SES_ACTIVE,
    AWS_SES_ACTIVE_ASSERTIONS,
    BASELINE,
    BASELINE_ASSERTIONS,
    DATA_EXPLORER_ACTIVE,
    DATA_EXPLORER_ACTIVE_ASSERTIONS,
    DATA_LINEAGE_ACTIVE,
    DATA_LINEAGE_ACTIVE_ASSERTIONS,
    DATA_LINEAGE_WORKSPACE_RESTRICTION_ACTIVE,
    DATA_LINEAGE_WORKSPACE_RESTRICTION_ACTIVE_ASSERTIONS,
    DB_EXTERNAL_EXISTING_ACTIVE,
    DB_EXTERNAL_EXISTING_ACTIVE_ASSERTIONS,
    DB_EXTERNAL_EXISTING_X_GROUNDSWELL_DELTA,
    DB_EXTERNAL_EXISTING_X_WAVE_LITE_DELTA,
    DB_EXTERNAL_NEW_ACTIVE,
    DB_EXTERNAL_NEW_ACTIVE_ASSERTIONS,
    DB_EXTERNAL_NEW_X_GROUNDSWELL_DELTA,
    DB_EXTERNAL_NEW_X_WAVE_LITE_DELTA,
    GROUNDSWELL_ACTIVE,
    GROUNDSWELL_ACTIVE_ASSERTIONS,
    HOSTS_FILE_ENTRY_ACTIVE,
    HOSTS_FILE_ENTRY_ACTIVE_ASSERTIONS,
    INSECURE_HTTP_ACTIVE,
    INSECURE_HTTP_ACTIVE_ASSERTIONS,
    PRIVATE_CA_REVERSE_PROXY_ACTIVE,
    PRIVATE_CA_REVERSE_PROXY_ACTIVE_ASSERTIONS,
    REDIS_EXTERNAL_ACTIVE,
    REDIS_EXTERNAL_ACTIVE_ASSERTIONS,
    REDIS_EXTERNAL_X_STUDIOS_DELTA,
    REDIS_EXTERNAL_X_WAVE_LITE_DELTA,
    STUDIOS_ACTIVE,
    STUDIOS_ACTIVE_ASSERTIONS,
    STUDIOS_PATH_ROUTING_ACTIVE,
    STUDIOS_PATH_ROUTING_ACTIVE_ASSERTIONS,
    STUDIOS_SSH_ACTIVE,
    STUDIOS_SSH_ACTIVE_ASSERTIONS,
    STUDIOS_SSH_WORKSPACE_RESTRICTION_ACTIVE,
    STUDIOS_SSH_WORKSPACE_RESTRICTION_ACTIVE_ASSERTIONS,
    STUDIOS_WAVE_ACTIVE_ASSERTIONS,
    TOWER_OPT_IN_FLAGS_ACTIVE,
    TOWER_OPT_IN_FLAGS_ACTIVE_ASSERTIONS,
    WAVE_LITE_ACTIVE,
    WAVE_LITE_ACTIVE_ASSERTIONS,
    WAVE_SEQERA_HOSTED_ACTIVE,
    WAVE_SEQERA_HOSTED_ACTIVE_ASSERTIONS,
)
from tests.utils.assertions.delta import assert_all_deltas, merge_deltas
from tests.utils.config import expected_sql_dir
from tests.utils.filehandling.filehandling import FileHelper


## ------------------------------------------------------------------------------------
## MARK: Baseline
## ------------------------------------------------------------------------------------
## Confirms `BASELINE_ASSERTIONS` accurately describes the rendered output when only
## `BASELINE` tfvars are applied — every other delta test in this file stacks features
## on top of `BASELINE_ASSERTIONS` via `merge_deltas`, so drift here would cascade.


@pytest.mark.local
@pytest.mark.tfvars(BASELINE)
def test_confirm_baseline(generated_test_files):
    """Confirm BASELINE_ASSERTIONS matches the rendered state under BASELINE tfvars (no feature deltas)."""
    assert_all_deltas(generated_test_files, BASELINE_ASSERTIONS)


## ------------------------------------------------------------------------------------
## MARK: Tower Flags
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.tower
@pytest.mark.tfvars(BASELINE + TOWER_OPT_IN_FLAGS_ACTIVE)
def test_tower_opt_in_flags_active(generated_test_files):
    """Six Tower-level config flags all on: instance creds, OpenAPI, pipeline versioning, auto-create users, cleanup.

    Grouped as a single test for compactness — these are independent knobs with no
    cross-feature interactions. If any one grows complex (e.g. pipeline versioning gets
    workspace-restriction logic), break it out into its own `_active` test.
    """
    expected = merge_deltas(BASELINE_ASSERTIONS, TOWER_OPT_IN_FLAGS_ACTIVE_ASSERTIONS)
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: Private CA Reverse Proxy: Active
## ------------------------------------------------------------------------------------
# TODO: Add tests that cover URLs when ALB not active.


@pytest.mark.local
@pytest.mark.private_ca
@pytest.mark.tfvars(BASELINE + PRIVATE_CA_REVERSE_PROXY_ACTIVE)
def test_private_ca_reverse_proxy_active(generated_test_files):
    """Private CA reverse-proxy active: ALB skipped, reverseproxy container terminates TLS with the self-signed cert."""
    expected = merge_deltas(
        BASELINE_ASSERTIONS,
        PRIVATE_CA_REVERSE_PROXY_ACTIVE_ASSERTIONS,
    )
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: Studios
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.studios
@pytest.mark.tfvars(BASELINE + STUDIOS_ACTIVE)
def test_studios_active(generated_test_files):
    """Studios: Confirm TOWER_DATA_STUDIO_CONNECT_URL and CONNECT_PROXY_URL."""
    expected = merge_deltas(
        BASELINE_ASSERTIONS,
        STUDIOS_ACTIVE_ASSERTIONS,
    )
    assert_all_deltas(generated_test_files, expected)


@pytest.mark.local
@pytest.mark.studios
@pytest.mark.tfvars(BASELINE + STUDIOS_ACTIVE + STUDIOS_PATH_ROUTING_ACTIVE)
def test_studios_path_routing_active(generated_test_files):
    """Studios + path routing on: TOWER_DATA_STUDIO_CONNECT_URL and CONNECT_PROXY_URL use the custom URL."""
    expected = merge_deltas(
        BASELINE_ASSERTIONS,
        STUDIOS_ACTIVE_ASSERTIONS,
        STUDIOS_PATH_ROUTING_ACTIVE_ASSERTIONS,
    )
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: Studios SSH
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.studios
@pytest.mark.tfvars(BASELINE + STUDIOS_ACTIVE + STUDIOS_SSH_ACTIVE)
def test_studios_ssh_active(generated_test_files):
    """Studios + SSH on: 5 SSH-related keys appear in tower_env, 3 in data_studios_env."""
    expected = merge_deltas(
        BASELINE_ASSERTIONS,
        STUDIOS_ACTIVE_ASSERTIONS,
        STUDIOS_SSH_ACTIVE_ASSERTIONS,
    )
    assert_all_deltas(generated_test_files, expected)


@pytest.mark.local
@pytest.mark.studios
@pytest.mark.tfvars(BASELINE + STUDIOS_ACTIVE + STUDIOS_SSH_ACTIVE + STUDIOS_SSH_WORKSPACE_RESTRICTION_ACTIVE)
def test_studios_ssh_workspace_restriction_active(generated_test_files):
    """Studios + SSH + workspace restriction: TOWER_DATA_STUDIO_SSH_ALLOWED_WORKSPACES flips to the configured CSV."""
    expected = merge_deltas(
        BASELINE_ASSERTIONS,
        STUDIOS_ACTIVE_ASSERTIONS,
        STUDIOS_SSH_ACTIVE_ASSERTIONS,
        STUDIOS_SSH_WORKSPACE_RESTRICTION_ACTIVE_ASSERTIONS,
    )
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: Studios + Wave integration
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.studios
@pytest.mark.tfvars(BASELINE + STUDIOS_ACTIVE + WAVE_SEQERA_HOSTED_ACTIVE)
def test_studios_wave_active(generated_test_files):
    """Studios + Wave: DATA STUDIO - WAVE INTEGRATION block renders with default Wave vars."""
    expected = merge_deltas(
        BASELINE_ASSERTIONS,
        STUDIOS_ACTIVE_ASSERTIONS,
        WAVE_SEQERA_HOSTED_ACTIVE_ASSERTIONS,
        STUDIOS_WAVE_ACTIVE_ASSERTIONS,
    )
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: Data Explorer: Active
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.data_explorer
@pytest.mark.tfvars(BASELINE + DATA_EXPLORER_ACTIVE)
def test_data_explorer_active(generated_test_files):
    """Data Explorer on: TOWER_DATA_EXPLORER_ENABLED flips true, CLOUD_DISABLED_WORKSPACES surfaces empty."""
    expected = merge_deltas(BASELINE_ASSERTIONS, DATA_EXPLORER_ACTIVE_ASSERTIONS)
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: Data Lineage: Active
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.data_lineage
@pytest.mark.tfvars(BASELINE + DATA_LINEAGE_ACTIVE)
def test_data_lineage_active(generated_test_files):
    """Data Lineage on, no workspace restriction: TOWER_LINEAGE_ALLOWED_WORKSPACES surfaces empty (= all workspaces)."""
    expected = merge_deltas(BASELINE_ASSERTIONS, DATA_LINEAGE_ACTIVE_ASSERTIONS)
    assert_all_deltas(generated_test_files, expected)


@pytest.mark.local
@pytest.mark.data_lineage
@pytest.mark.tfvars(BASELINE + DATA_LINEAGE_ACTIVE + DATA_LINEAGE_WORKSPACE_RESTRICTION_ACTIVE)
def test_data_lineage_workspace_restriction_active(generated_test_files):
    """Data Lineage + workspace restriction: TOWER_LINEAGE_ALLOWED_WORKSPACES flips from "" to the configured CSV."""
    expected = merge_deltas(
        BASELINE_ASSERTIONS,
        DATA_LINEAGE_ACTIVE_ASSERTIONS,
        DATA_LINEAGE_WORKSPACE_RESTRICTION_ACTIVE_ASSERTIONS,
    )
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: AWS SES: Active
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.tower
@pytest.mark.tfvars(BASELINE + AWS_SES_ACTIVE)
def test_aws_ses_active(generated_test_files):
    """AWS SES (IAM) on: TOWER_ENABLE_AWS_SES flips true, container SMTP host/port keys disappear."""
    expected = merge_deltas(BASELINE_ASSERTIONS, AWS_SES_ACTIVE_ASSERTIONS)
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: Groundswell: Active
## NOTE: Interactions with DB settings are tested in cross-features section.
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.groundswell
@pytest.mark.tfvars(BASELINE + GROUNDSWELL_ACTIVE)
def test_groundswell_active(generated_test_files):
    """Groundswell on (BASELINE container DB).

    Asserts: tower_env Groundswell keys flip, groundswell_env populates, and the
    container-DB patching script renders in ansible_05.
    """
    expected = merge_deltas(BASELINE_ASSERTIONS, GROUNDSWELL_ACTIVE_ASSERTIONS)
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: DB (New)
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.db_new
@pytest.mark.tfvars(BASELINE + DB_EXTERNAL_NEW_ACTIVE)
def test_db_new_active(generated_test_files):
    """New external DB on top of OFF baseline: TOWER_DB_URL points to the new RDS endpoint."""
    expected = merge_deltas(BASELINE_ASSERTIONS, DB_EXTERNAL_NEW_ACTIVE_ASSERTIONS)
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: DB (Existing)
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.db_existing
@pytest.mark.tfvars(BASELINE + DB_EXTERNAL_EXISTING_ACTIVE)
def test_db_existing_active(generated_test_files):
    """Existing external DB on top of OFF baseline: TOWER_DB_URL points to the existing endpoint."""
    expected = merge_deltas(BASELINE_ASSERTIONS, DB_EXTERNAL_EXISTING_ACTIVE_ASSERTIONS)
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: Redis (New)
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.redis_external
@pytest.mark.tfvars(BASELINE + REDIS_EXTERNAL_ACTIVE)
def test_redis_external_active(generated_test_files):
    """External Redis on top of OFF baseline: TOWER_REDIS_URL points to the external endpoint."""
    expected = merge_deltas(BASELINE_ASSERTIONS, REDIS_EXTERNAL_ACTIVE_ASSERTIONS)
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: Wave
##  NOTE: Interactions with DB/Redis settings are tested in cross-features section.
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.wave
@pytest.mark.tfvars(BASELINE + WAVE_SEQERA_HOSTED_ACTIVE)
def test_seqera_hosted_wave_active(generated_test_files):
    """Activating Seqera-hosted Wave from OFF baseline: assert every generated file vs OFF + Wave delta."""
    expected = merge_deltas(BASELINE_ASSERTIONS, WAVE_SEQERA_HOSTED_ACTIVE_ASSERTIONS)
    assert_all_deltas(generated_test_files, expected)


@pytest.mark.local
@pytest.mark.wave
@pytest.mark.tfvars(BASELINE + WAVE_LITE_ACTIVE)
def test_wave_lite_active(generated_test_files):
    """Wave-Lite on top of OFF baseline with container DB and container Redis (defaults).

    Exercises the standalone Wave-Lite stack: wave_lite_yml URLs populate, the four
    Wave-Lite containers (wave-lite, wave-lite-reverse-proxy, wave-db, wave-redis)
    appear in docker_compose, and Tower's WAVE_SERVER_URL points at the local Wave-Lite
    endpoint. Cross-feature variants (external DB / external Redis) live in the
    Multi-Service Interactions section.
    """
    expected = merge_deltas(BASELINE_ASSERTIONS, WAVE_LITE_ACTIVE_ASSERTIONS)
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: Cross Features
##
## Cross-feature tests: scenarios where two features stacked together produce extra
## effects beyond what each feature delivers in isolation. Each test merges:
##   BASELINE_ASSERTIONS + <FEATURE_A>_ON_ASSERTIONS + <FEATURE_B>_ON_ASSERTIONS
##                       + <FEATURE_A>_X_<FEATURE_B>_DELTA   (the cross-feature piece)
##
## Cross-feature delta constants are only valid when both component features are stacked. Use the existing
## `_X_` constants where they exist; declare new ones there (not inline) when a new
## interaction emerges.
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.db_new
@pytest.mark.groundswell
@pytest.mark.tfvars(BASELINE + GROUNDSWELL_ACTIVE + DB_EXTERNAL_NEW_ACTIVE)
def test_db_new_with_groundswell(generated_test_files):
    """New external DB + Groundswell on: Groundswell's TOWER_DB_URL and SWELL_DB_URL flip to the new RDS endpoint."""
    expected = merge_deltas(
        BASELINE_ASSERTIONS,
        GROUNDSWELL_ACTIVE_ASSERTIONS,
        DB_EXTERNAL_NEW_ACTIVE_ASSERTIONS,
        DB_EXTERNAL_NEW_X_GROUNDSWELL_DELTA,
    )
    assert_all_deltas(generated_test_files, expected)


@pytest.mark.local
@pytest.mark.db_new
@pytest.mark.wave
@pytest.mark.tfvars(BASELINE + WAVE_LITE_ACTIVE + DB_EXTERNAL_NEW_ACTIVE)
def test_db_new_with_wave_lite(generated_test_files):
    """New external DB + Wave-Lite on: Wave-Lite uses the new RDS for its wave-db; container wave-db is removed.

    Mirror inverse of `test_db_existing_with_wave_lite` (which asserts the
    non-interaction). Unlike existing-DB, new-DB IS a real cross-feature interaction
    for Wave-Lite — Terraform provisions a wave-db RDS that Wave-Lite uses in place
    of the container.
    """
    expected = merge_deltas(
        BASELINE_ASSERTIONS,
        WAVE_LITE_ACTIVE_ASSERTIONS,
        DB_EXTERNAL_NEW_ACTIVE_ASSERTIONS,
        DB_EXTERNAL_NEW_X_WAVE_LITE_DELTA,
    )
    assert_all_deltas(generated_test_files, expected)


@pytest.mark.local
@pytest.mark.db_existing
@pytest.mark.groundswell
@pytest.mark.tfvars(BASELINE + GROUNDSWELL_ACTIVE + DB_EXTERNAL_EXISTING_ACTIVE)
def test_db_existing_with_groundswell(generated_test_files):
    """Existing external DB + Groundswell on: Groundswell's TOWER_DB_URL also flips to the existing endpoint."""
    expected = merge_deltas(
        BASELINE_ASSERTIONS,
        GROUNDSWELL_ACTIVE_ASSERTIONS,
        DB_EXTERNAL_EXISTING_ACTIVE_ASSERTIONS,
        DB_EXTERNAL_EXISTING_X_GROUNDSWELL_DELTA,
    )
    assert_all_deltas(generated_test_files, expected)


@pytest.mark.local
@pytest.mark.db_existing
@pytest.mark.wave
@pytest.mark.tfvars(BASELINE + WAVE_LITE_ACTIVE + DB_EXTERNAL_EXISTING_ACTIVE)
def test_db_existing_with_wave_lite(generated_test_files):
    """Existing external DB + Wave-Lite on: Wave-Lite ignores existing-DB for its own DB.

    Documented limitation as of Aug 2025: Wave-Lite always uses its container DB
    regardless of the existing-DB flag — `wave_lite_yml.wave.db.uri` stays at the
    container DB value, asserted via WAVE_LITE_ACTIVE_ASSERTIONS. The cross-feature delta
    captures the only real interaction: ansible_02's Wave-Lite Postgres population
    block renders because `populate_external_db` is true. If Wave-Lite ever grows
    existing-DB support, `wave.db.uri` will flip and break this assertion, forcing
    a constants update.
    """
    expected = merge_deltas(
        BASELINE_ASSERTIONS,
        WAVE_LITE_ACTIVE_ASSERTIONS,
        DB_EXTERNAL_EXISTING_ACTIVE_ASSERTIONS,
        DB_EXTERNAL_EXISTING_X_WAVE_LITE_DELTA,
    )
    assert_all_deltas(generated_test_files, expected)


@pytest.mark.local
@pytest.mark.redis_external
@pytest.mark.studios
@pytest.mark.tfvars(BASELINE + STUDIOS_ACTIVE + REDIS_EXTERNAL_ACTIVE)
def test_redis_external_with_studios(generated_test_files):
    """External Redis + Studios on: Studios's CONNECT_REDIS_ADDRESS flips to the external endpoint."""
    expected = merge_deltas(
        BASELINE_ASSERTIONS,
        REDIS_EXTERNAL_ACTIVE_ASSERTIONS,
        STUDIOS_ACTIVE_ASSERTIONS,
        REDIS_EXTERNAL_X_STUDIOS_DELTA,
    )
    assert_all_deltas(generated_test_files, expected)


@pytest.mark.local
@pytest.mark.redis_external
@pytest.mark.wave
@pytest.mark.tfvars(BASELINE + WAVE_LITE_ACTIVE + REDIS_EXTERNAL_ACTIVE)
def test_redis_external_with_wave_lite(generated_test_files):
    """External Redis + Wave-Lite on: Wave-Lite's redis endpoint flips and the container wave-redis is removed."""
    expected = merge_deltas(
        BASELINE_ASSERTIONS,
        REDIS_EXTERNAL_ACTIVE_ASSERTIONS,
        WAVE_LITE_ACTIVE_ASSERTIONS,
        REDIS_EXTERNAL_X_WAVE_LITE_DELTA,
    )
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: Seqerakit (ansible_06)
##
## `ansible_06_run_seqerakit` picks one of three mutually-exclusive substrings based on
## two flags. The truststore branch is the BASELINE default; flipping either
## `flag_create_hosts_file_entry` or `flag_do_not_use_https` on swaps it out for the
## corresponding alternative. The combined test is included for documentation — both
## flags independently knock out the truststore default, so there's no cross-feature
## delta to declare.
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.ansible
@pytest.mark.tfvars(BASELINE + HOSTS_FILE_ENTRY_ACTIVE)
def test_hosts_file_entry_active(generated_test_files):
    """`flag_create_hosts_file_entry` on: ansible_06 swaps the truststore branch for the hosts-file branch."""
    expected = merge_deltas(BASELINE_ASSERTIONS, HOSTS_FILE_ENTRY_ACTIVE_ASSERTIONS)
    assert_all_deltas(generated_test_files, expected)


@pytest.mark.local
@pytest.mark.ansible
@pytest.mark.tfvars(BASELINE + INSECURE_HTTP_ACTIVE)
def test_insecure_http_active(generated_test_files):
    """`flag_do_not_use_https` on: ansible_06 swaps the truststore branch for the insecure-HTTP branch."""
    expected = merge_deltas(BASELINE_ASSERTIONS, INSECURE_HTTP_ACTIVE_ASSERTIONS)
    assert_all_deltas(generated_test_files, expected)


@pytest.mark.local
@pytest.mark.ansible
@pytest.mark.tfvars(BASELINE + HOSTS_FILE_ENTRY_ACTIVE + INSECURE_HTTP_ACTIVE)
def test_hosts_file_entry_with_insecure_http(generated_test_files):
    """Both flags on simultaneously: hosts-file and insecure substrings both render; truststore stays out.

    Documentation-only — there's no cross-feature delta because each flag independently
    knocks out the truststore default. `merge_deltas` handles the union of both
    `_ON_ASSERTIONS` constants correctly.
    """
    expected = merge_deltas(
        BASELINE_ASSERTIONS,
        HOSTS_FILE_ENTRY_ACTIVE_ASSERTIONS,
        INSECURE_HTTP_ACTIVE_ASSERTIONS,
    )
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: TODO: Wave-Lite SQL
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.wave
def test_wave_sql_file_content(generated_test_files):
    """Test scenario.

    - Use the SQL files generated by the baseline testcase.
    - Compare against pre-generated result files in `tests/datafiles/expected_results/expected_sql`.
    """
    ## COMPARISON
    ## ========================================================================================
    wave_lite_rds = FileHelper.read_file(f"{generated_test_files['wave_lite_rds']['filepath']}")
    ref_wave_lite_rds = FileHelper.read_file(f"{expected_sql_dir}/wave-lite-rds.sql")

    assert ref_wave_lite_rds == wave_lite_rds
