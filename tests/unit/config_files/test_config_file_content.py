import pytest
from tests.unit.config_files.expected_deltas import (
    AWS_SES_ON,
    AWS_SES_ON_ASSERTIONS,
    BASELINE,
    BASELINE_ASSERTIONS,
    DATA_EXPLORER_ON,
    DATA_EXPLORER_ON_ASSERTIONS,
    DB_EXTERNAL_EXISTING_ON,
    DB_EXTERNAL_EXISTING_ON_ASSERTIONS,
    DB_EXTERNAL_NEW_ON,
    DB_EXTERNAL_NEW_ON_ASSERTIONS,
    GROUNDSWELL_ON,
    GROUNDSWELL_ON_ASSERTIONS,
    PRIVATE_CA_REVERSE_PROXY_ON,
    PRIVATE_CA_REVERSE_PROXY_ON_ASSERTIONS,
    REDIS_EXTERNAL_ON,
    REDIS_EXTERNAL_ON_ASSERTIONS,
    STUDIOS_ON,
    STUDIOS_ON_ASSERTIONS,
    STUDIOS_PATH_ROUTING_ON,
    STUDIOS_PATH_ROUTING_ON_ASSERTIONS,
    STUDIOS_SSH_ON,
    STUDIOS_SSH_ON_ASSERTIONS,
    STUDIOS_SSH_WORKSPACE_RESTRICTION_ON,
    STUDIOS_SSH_WORKSPACE_RESTRICTION_ON_ASSERTIONS,
    TOWER_OPT_IN_FLAGS_ON,
    TOWER_OPT_IN_FLAGS_ON_ASSERTIONS,
    WAVE_LITE_ON,
    WAVE_LITE_ON_ASSERTIONS,
    WAVE_SEQERA_HOSTED_ON,
    WAVE_SEQERA_HOSTED_ON_ASSERTIONS,
)
from tests.utils.assertions.delta import assert_all_deltas, merge_deltas
from tests.utils.config import expected_sql_dir
from tests.utils.filehandling import FileHelper


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
@pytest.mark.tfvars(BASELINE + TOWER_OPT_IN_FLAGS_ON)
def test_tower_opt_in_flags_active(generated_test_files):
    """Six Tower-level config flags all on: instance creds, OpenAPI, pipeline versioning, auto-create users, cleanup.

    Grouped as a single test for compactness — these are independent knobs with no
    cross-feature interactions. If any one grows complex (e.g. pipeline versioning gets
    workspace-restriction logic), break it out into its own `_active` test.
    """
    expected = merge_deltas(BASELINE_ASSERTIONS, TOWER_OPT_IN_FLAGS_ON_ASSERTIONS)
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: Private CA Reverse Proxy: Active
## ------------------------------------------------------------------------------------
# TODO: Add tests that cover URLs when ALB not active.

@pytest.mark.local
@pytest.mark.private_ca
@pytest.mark.tfvars(BASELINE + PRIVATE_CA_REVERSE_PROXY_ON)
def test_private_ca_reverse_proxy_active(generated_test_files):
    """Private CA reverse-proxy active: ALB skipped, reverseproxy container terminates TLS with the self-signed cert."""
    expected = merge_deltas(
        BASELINE_ASSERTIONS,
        PRIVATE_CA_REVERSE_PROXY_ON_ASSERTIONS,
    )
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: Studios
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.studios
@pytest.mark.tfvars(BASELINE + STUDIOS_ON)
def test_studios_active(generated_test_files):
    """Studios: Confirm TOWER_DATA_STUDIO_CONNECT_URL and CONNECT_PROXY_URL."""
    expected = merge_deltas(
        BASELINE_ASSERTIONS,
        STUDIOS_ON_ASSERTIONS,
    )
    assert_all_deltas(generated_test_files, expected)


@pytest.mark.local
@pytest.mark.studios
@pytest.mark.tfvars(BASELINE + STUDIOS_ON + STUDIOS_PATH_ROUTING_ON)
def test_studios_path_routing_active(generated_test_files):
    """Studios + path routing on: TOWER_DATA_STUDIO_CONNECT_URL and CONNECT_PROXY_URL use the custom URL."""
    expected = merge_deltas(
        BASELINE_ASSERTIONS,
        STUDIOS_ON_ASSERTIONS,
        STUDIOS_PATH_ROUTING_ON_ASSERTIONS,
    )
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: Studios SSH
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.studios
@pytest.mark.tfvars(BASELINE + STUDIOS_ON + STUDIOS_SSH_ON)
def test_studios_ssh_active(generated_test_files):
    """Studios + SSH on: 5 SSH-related keys appear in tower_env, 3 in data_studios_env."""
    expected = merge_deltas(
        BASELINE_ASSERTIONS,
        STUDIOS_ON_ASSERTIONS,
        STUDIOS_SSH_ON_ASSERTIONS,
    )
    assert_all_deltas(generated_test_files, expected)


@pytest.mark.local
@pytest.mark.studios
@pytest.mark.tfvars(BASELINE + STUDIOS_ON + STUDIOS_SSH_ON + STUDIOS_SSH_WORKSPACE_RESTRICTION_ON)
def test_studios_ssh_workspace_restriction_active(generated_test_files):
    """Studios + SSH + workspace restriction: TOWER_DATA_STUDIO_SSH_ALLOWED_WORKSPACES flips to the configured CSV."""
    expected = merge_deltas(
        BASELINE_ASSERTIONS,
        STUDIOS_ON_ASSERTIONS,
        STUDIOS_SSH_ON_ASSERTIONS,
        STUDIOS_SSH_WORKSPACE_RESTRICTION_ON_ASSERTIONS,
    )
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: Data Explorer: Active
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.data_explorer
@pytest.mark.tfvars(BASELINE + DATA_EXPLORER_ON)
def test_data_explorer_active(generated_test_files):
    """Data Explorer on: TOWER_DATA_EXPLORER_ENABLED flips true, CLOUD_DISABLED_WORKSPACES surfaces empty."""
    expected = merge_deltas(BASELINE_ASSERTIONS, DATA_EXPLORER_ON_ASSERTIONS)
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: AWS SES: Active
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.tower
@pytest.mark.tfvars(BASELINE + AWS_SES_ON)
def test_aws_ses_active(generated_test_files):
    """AWS SES (IAM) on: TOWER_ENABLE_AWS_SES flips true, container SMTP host/port keys disappear."""
    expected = merge_deltas(BASELINE_ASSERTIONS, AWS_SES_ON_ASSERTIONS)
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: DB (New)
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.db_new
@pytest.mark.tfvars(BASELINE + DB_EXTERNAL_NEW_ON)
def test_db_new_active(generated_test_files):
    """New external DB on top of OFF baseline: TOWER_DB_URL points to the new RDS endpoint."""
    expected = merge_deltas(BASELINE_ASSERTIONS, DB_EXTERNAL_NEW_ON_ASSERTIONS)
    assert_all_deltas(generated_test_files, expected)


@pytest.mark.local
@pytest.mark.db_new
@pytest.mark.groundswell
@pytest.mark.tfvars(BASELINE + GROUNDSWELL_ON + DB_EXTERNAL_NEW_ON)
def test_db_new_with_groundswell(generated_test_files):
    """New external DB + Groundswell on: Groundswell's TOWER_DB_URL and SWELL_DB_URL flip to the new RDS endpoint."""
    expected = merge_deltas(
        BASELINE_ASSERTIONS,
        GROUNDSWELL_ON_ASSERTIONS,
        DB_EXTERNAL_NEW_ON_ASSERTIONS,
        # Cross-feature: new DB flips Groundswell's TOWER_DB_URL and SWELL_DB_URL.
        {
            "groundswell_env": {
                "present": {
                    "TOWER_DB_URL": "jdbc:mysql://mock.tower-db.com:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true",
                    "SWELL_DB_URL": "mysql://mock.tower-db.com:3306/swell",
                },
            },
        },
    )
    assert_all_deltas(generated_test_files, expected)


@pytest.mark.local
@pytest.mark.db_new
@pytest.mark.wave
@pytest.mark.tfvars(BASELINE + WAVE_LITE_ON + DB_EXTERNAL_NEW_ON)
def test_db_new_with_wave_lite(generated_test_files):
    """New external DB + Wave-Lite on: Wave-Lite uses the new RDS for its wave-db; container wave-db is removed.

    Mirror inverse of `test_db_existing_with_wave_lite` (which asserts the
    non-interaction). Unlike existing-DB, new-DB IS a real cross-feature interaction
    for Wave-Lite — Terraform provisions a wave-db RDS that Wave-Lite uses in place
    of the container.
    """
    expected = merge_deltas(
        BASELINE_ASSERTIONS,
        WAVE_LITE_ON_ASSERTIONS,
        DB_EXTERNAL_NEW_ON_ASSERTIONS,
        # Cross-feature: new DB flips Wave-Lite's wave.db.uri to the new RDS host
        # and removes the container wave-db from docker_compose.
        {
            "wave_lite_yml": {
                "present": {"wave.db.uri": "jdbc:postgresql://mock.wave-db.com:5432/wave"},
            },
            "docker_compose": {"omitted": {"services.wave-db"}},
        },
    )
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: DB (Existing)
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.db_existing
@pytest.mark.tfvars(BASELINE + DB_EXTERNAL_EXISTING_ON)
def test_db_existing_active(generated_test_files):
    """Existing external DB on top of OFF baseline: TOWER_DB_URL points to the existing endpoint."""
    expected = merge_deltas(BASELINE_ASSERTIONS, DB_EXTERNAL_EXISTING_ON_ASSERTIONS)
    assert_all_deltas(generated_test_files, expected)


@pytest.mark.local
@pytest.mark.db_existing
@pytest.mark.groundswell
@pytest.mark.tfvars(BASELINE + GROUNDSWELL_ON + DB_EXTERNAL_EXISTING_ON)
def test_db_existing_with_groundswell(generated_test_files):
    """Existing external DB + Groundswell on: Groundswell's TOWER_DB_URL also flips to the existing endpoint."""
    expected = merge_deltas(
        BASELINE_ASSERTIONS,
        GROUNDSWELL_ON_ASSERTIONS,
        DB_EXTERNAL_EXISTING_ON_ASSERTIONS,
        # Cross-feature: existing DB flips Groundswell's TOWER_DB_URL and SWELL_DB_URL.
        {
            "groundswell_env": {
                "present": {
                    "TOWER_DB_URL": "jdbc:mysql://existing.tower-db.com:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true",
                    "SWELL_DB_URL": "mysql://existing.tower-db.com:3306/swell",
                },
            },
        },
    )
    assert_all_deltas(generated_test_files, expected)


@pytest.mark.local
@pytest.mark.db_existing
@pytest.mark.wave
@pytest.mark.tfvars(BASELINE + WAVE_LITE_ON + DB_EXTERNAL_EXISTING_ON)
def test_db_existing_with_wave_lite(generated_test_files):
    """Existing external DB + Wave-Lite on: Wave-Lite ignores existing-DB.

    Documented limitation as of Aug 2025: Wave-Lite always uses its container DB
    regardless of the existing-DB flag. This test serves as a regression guard — if
    Wave-Lite ever grows existing-DB support, `wave_lite_yml.wave.db.uri` will flip
    and break this assertion, forcing a constants update.
    """
    expected = merge_deltas(
        BASELINE_ASSERTIONS,
        WAVE_LITE_ON_ASSERTIONS,
        DB_EXTERNAL_EXISTING_ON_ASSERTIONS,
        # No cross-feature delta — Wave-Lite's wave.db.uri stays at container DB.
    )
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: Redis (New))
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.redis_external
@pytest.mark.tfvars(BASELINE + REDIS_EXTERNAL_ON)
def test_redis_external_active(generated_test_files):
    """External Redis on top of OFF baseline: TOWER_REDIS_URL points to the external endpoint."""
    expected = merge_deltas(BASELINE_ASSERTIONS, REDIS_EXTERNAL_ON_ASSERTIONS)
    assert_all_deltas(generated_test_files, expected)


@pytest.mark.local
@pytest.mark.redis_external
@pytest.mark.studios
@pytest.mark.tfvars(BASELINE + STUDIOS_ON + REDIS_EXTERNAL_ON)
def test_redis_external_with_studios(generated_test_files):
    """External Redis + Studios on: Studios's CONNECT_REDIS_ADDRESS flips to the external endpoint."""
    expected = merge_deltas(
        BASELINE_ASSERTIONS,
        REDIS_EXTERNAL_ON_ASSERTIONS,
        STUDIOS_ON_ASSERTIONS,
        # External Redis flips Studios's redis endpoint.
        {"data_studios_env": {"present": {"CONNECT_REDIS_ADDRESS": "mock.tower-redis.com:6379"}}},
    )
    assert_all_deltas(generated_test_files, expected)


@pytest.mark.local
@pytest.mark.redis_external
@pytest.mark.wave
@pytest.mark.tfvars(BASELINE + WAVE_LITE_ON + REDIS_EXTERNAL_ON)
def test_redis_external_with_wave_lite(generated_test_files):
    """External Redis + Wave-Lite on."""
    expected = merge_deltas(
        BASELINE_ASSERTIONS,
        REDIS_EXTERNAL_ON_ASSERTIONS,
        WAVE_LITE_ON_ASSERTIONS,
        # External Redis flips Wave-Lite's redis endpoint and removes the
        # `wave-redis` container from docker_compose (no container Redis when external).
        {
            "wave_lite_yml": {"present": {"redis.uri": "rediss://mock.wave-redis.com:6379"}},
            "docker_compose": {"omitted": {"services.wave-redis"}},
        },
    )
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: Seqera Wave: Active
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.wave
@pytest.mark.tfvars(BASELINE + WAVE_SEQERA_HOSTED_ON)
def test_seqera_hosted_wave_active(generated_test_files):
    """Activating Seqera-hosted Wave from OFF baseline: assert every generated file vs OFF + Wave delta."""
    expected = merge_deltas(BASELINE_ASSERTIONS, WAVE_SEQERA_HOSTED_ON_ASSERTIONS)
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
