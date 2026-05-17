import pytest
from tests.datafiles.expected_results.expected_results import (
    assertion_modifiers_template,
    generate_assertions_all_active,
    generate_assertions_all_disabled,
)
from tests.unit.config_files.expected_deltas import (
    EXTERNAL_REDIS_ON,
    EXTERNAL_REDIS_ON_ASSERTIONS,
    OFF_BASELINE,
    OFF_BASELINE_ASSERTIONS,
    SEQERA_HOSTED_WAVE_ON,
    SEQERA_HOSTED_WAVE_ON_ASSERTIONS,
    STUDIOS_ON_BASE,
    STUDIOS_ON_BASE_ASSERTIONS,
    WAVE_LITE_ON_BASE,
    WAVE_LITE_ON_BASE_ASSERTIONS,
)
from tests.utils.assertions.delta import assert_all_deltas, merge_deltas
from tests.utils.assertions.verify_assertions import verify_all_assertions
from tests.utils.config import expected_sql_dir
from tests.utils.filehandling import FileHelper


## ------------------------------------------------------------------------------------
## MARK: Baseline ON/OFF
## ------------------------------------------------------------------------------------
## This establishes a baseline set of files using testing defaults:
##    - ALB is active,
##    - Containerized DB / Redis
##    - Wave Lite & Groundswell & Data Explorer are active / inactive.


@pytest.mark.local
def test_baseline_alb_all_enabled(generated_test_files):
    """Conduct baseline assertions when all SP services turned on."""
    assertion_modifiers = assertion_modifiers_template()
    tc_assertions = generate_assertions_all_active(generated_test_files, assertion_modifiers)

    verify_all_assertions(generated_test_files, tc_assertions)


@pytest.mark.local
@pytest.mark.tfvars("""
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
""")
def test_baseline_alb_all_disabled(generated_test_files):
    """Conduct baseline assertions when all SP services turned off."""
    # TODO: Get rid of email disabling. This should be a discrete check.
    assertion_modifiers = assertion_modifiers_template()
    tc_assertions = generate_assertions_all_disabled(generated_test_files, assertion_modifiers)

    verify_all_assertions(generated_test_files, tc_assertions)


## ------------------------------------------------------------------------------------
## MARK: Private CA: Active
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.private_ca
@pytest.mark.tfvars("""
    flag_create_load_balancer        = false
    flag_use_private_cacert          = true
    flag_do_not_use_https            = false
""")
def test_private_ca_reverse_proxy_active(generated_test_files):
    """Test scenario.

    - Baseline all enabled.
    - Reverseproxy with self-signed private CA active.
    """
    assertion_modifiers = assertion_modifiers_template()
    assertion_modifiers["docker_compose"] = {
        "present": {"services.reverseproxy.labels.seqera": "reverseproxy"},
        "omitted": {},
    }

    tc_assertions = generate_assertions_all_active(generated_test_files, assertion_modifiers)
    verify_all_assertions(generated_test_files, tc_assertions)


## ------------------------------------------------------------------------------------
## MARK: Studios: Path Routing
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.studios
@pytest.mark.tfvars("""
    flag_enable_data_studio         = true
    flag_studio_enable_path_routing = true
    data_studio_path_routing_url    = "connect-example.com"
""")
def test_studio_path_routing_enabled(generated_test_files):
    """Test scenario.

    - Baseline all enabled.
    - Studios path-routing enabled.
    """
    assertion_modifiers = assertion_modifiers_template()

    assertion_modifiers["tower_env"] = {
        "present": {
            "TOWER_DATA_STUDIO_ENABLE_PATH_ROUTING": "true",
            "TOWER_DATA_STUDIO_CONNECT_URL": "https://connect-example.com",
        },
        "omitted": {},
    }

    assertion_modifiers["data_studios_env"] = {
        "present": {"CONNECT_PROXY_URL": "https://connect-example.com"},
        "omitted": {},
    }
    tc_assertions = generate_assertions_all_active(generated_test_files, assertion_modifiers)

    verify_all_assertions(generated_test_files, tc_assertions)


## ------------------------------------------------------------------------------------
## MARK: Studios SSH: Enabled
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.studios
@pytest.mark.tfvars("""
    flag_enable_data_studio_ssh = true
    flag_limit_data_studio_ssh_to_some_workspaces = false
""")
def test_studio_ssh_enabled(generated_test_files):
    """Test scenario.

    - Baseline all enabled.
    - Studios SSH enabled.
    """
    assertion_modifiers = assertion_modifiers_template()

    assertion_modifiers["tower_env"] = {
        "present": {
            "TOWER_SSH_KEYS_MANAGEMENT_ENABLED": "true",
            "CONNECT_SSH_ENABLED": "true",
            "TOWER_DATA_STUDIO_CONNECT_SSH_PORT": "2222",
            "TOWER_DATA_STUDIO_SSH_ALLOWED_WORKSPACES": "",
            "TOWER_DATA_STUDIO_CONNECT_SSH_ADDRESS": "https://connect-ssh.autodc.dev-seqera.net",
        },
        "omitted": {},
    }

    assertion_modifiers["data_studios_env"] = {
        "present": {
            "CONNECT_SSH_ENABLED": "true",
            "CONNECT_SSH_ADDR": ":2222",
            "CONNECT_SSH_KEY_PATH": "/data/ssh-host-key",
        },
        "omitted": {},
    }

    tc_assertions = generate_assertions_all_active(generated_test_files, assertion_modifiers)
    verify_all_assertions(generated_test_files, tc_assertions)


## ------------------------------------------------------------------------------------
## MARK: Studios SSH: Enabled — workspace restriction active
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.studios
@pytest.mark.tfvars("""
    flag_enable_data_studio_ssh = true
    flag_limit_data_studio_ssh_to_some_workspaces = true
    data_studio_ssh_eligible_workspaces = "12,34"
""")
def test_studio_ssh_enabled_workspace_restriction(generated_test_files):
    """Test scenario.

    - Baseline all enabled.
    - Studios SSH enabled.
    - SSH restricted to specific workspaces.
    """
    assertion_modifiers = assertion_modifiers_template()

    assertion_modifiers["tower_env"] = {
        "present": {
            "TOWER_DATA_STUDIO_SSH_ALLOWED_WORKSPACES": "12,34",
        },
        "omitted": {},
    }

    tc_assertions = generate_assertions_all_active(generated_test_files, assertion_modifiers)
    verify_all_assertions(generated_test_files, tc_assertions)


## ------------------------------------------------------------------------------------
## MARK: Studios SSH: Disabled
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.studios
@pytest.mark.tfvars("""
    flag_enable_data_studio_ssh = false
""")
def test_studio_ssh_disabled(generated_test_files):
    """Test scenario.

    - Baseline all enabled.
    - Studios on, SSH explicitly disabled.
    """
    assertion_modifiers = assertion_modifiers_template()

    assertion_modifiers["tower_env"] = {
        "present": {},
        "omitted": {
            "TOWER_SSH_KEYS_MANAGEMENT_ENABLED": "",
            "TOWER_DATA_STUDIO_CONNECT_SSH_PORT": "",
            "TOWER_DATA_STUDIO_CONNECT_SSH_ADDRESS": "",
        },
    }

    assertion_modifiers["data_studios_env"] = {
        "present": {},
        "omitted": {
            "CONNECT_SSH_ENABLED": "",
            "CONNECT_SSH_ADDR": "",
            "CONNECT_SSH_KEY_PATH": "",
        },
    }

    tc_assertions = generate_assertions_all_active(generated_test_files, assertion_modifiers)
    verify_all_assertions(generated_test_files, tc_assertions)


## ------------------------------------------------------------------------------------
## MARK: New DB: All Active
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.db_new
@pytest.mark.tfvars("""
    flag_create_external_db         = true
    flag_use_existing_external_db   = false
    flag_use_container_db           = false
""")
def test_new_db_all_enabled(generated_test_files):
    """Test scenario.

    - Baseline all enabled.
    - New RDS active.
    """
    assertion_modifiers = assertion_modifiers_template()

    assertion_modifiers["tower_env"] = {
        "present": {
            "TOWER_DB_URL": "jdbc:mysql://mock.tower-db.com:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true",
        },
        "omitted": {},
    }

    assertion_modifiers["groundswell_env"] = {
        "present": {
            "TOWER_DB_URL": "jdbc:mysql://mock.tower-db.com:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true",
        },
        "omitted": {},
    }

    assertion_modifiers["wave_lite_yml"] = {
        "present": {
            "wave.db.uri": "jdbc:postgresql://mock.wave-db.com:5432/wave",
        },
        "omitted": {},
    }

    assertion_modifiers["docker_compose"] = {
        "present": {
            "services.wave-lite.labels.seqera": "wave-lite",
            "services.wave-lite-reverse-proxy.labels.seqera": "wave-lite-reverse-proxy",
            "services.wave-redis.labels.seqera": "wave-redis",
        },
        "omitted": {
            "services.wave-db": "",
        },
    }

    tc_assertions = generate_assertions_all_active(generated_test_files, assertion_modifiers)
    verify_all_assertions(generated_test_files, tc_assertions)


## ------------------------------------------------------------------------------------
## MARK: New DB: All Disabled
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.db_new
@pytest.mark.tfvars("""
    flag_use_aws_ses_iam_integration    = false
    flag_use_existing_smtp              = true
    flag_enable_groundswell             = false
    flag_data_explorer_enabled          = false
    flag_enable_data_studio             = false
    flag_use_wave                       = false
    flag_use_wave_lite                  = false

    flag_create_external_db             = true
    flag_use_existing_external_db       = false
    flag_use_container_db               = false
    flag_allow_aws_instance_credentials = false
    flag_tower_enable_participant_auto_create_user = false
    flag_tower_enable_member_auto_create_user      = false
    tower_workflow_cleanup_enabled                 = false
""")
def test_new_db_all_disabled(generated_test_files):
    """Test scenario.

    - Baseline all disabled.
    - New RDS active.
    """
    assertion_modifiers = assertion_modifiers_template()

    assertion_modifiers["tower_env"] = {
        "present": {
            "TOWER_DB_URL": "jdbc:mysql://mock.tower-db.com:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true",
        },
        "omitted": {},
    }

    # No need for custom assertion_modifiers -- core testcase handles this one.
    assertion_modifiers["groundswell_env"] = {"present": {}, "omitted": {}}

    # No need for custom assertion_modifiers -- core testcase handles this one.
    assertion_modifiers["wave_lite_yml"] = {"present": {}, "omitted": {}}
    tc_assertions = generate_assertions_all_disabled(generated_test_files, assertion_modifiers)

    verify_all_assertions(generated_test_files, tc_assertions)


## ------------------------------------------------------------------------------------
## MARK: Existing DB: All Active
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.db_existing
@pytest.mark.tfvars("""
    flag_create_external_db         = false
    flag_use_existing_external_db   = true
    flag_use_container_db           = false
    tower_db_url                        = "existing.tower-db.com"
""")
def test_existing_db_all_enabled(generated_test_files):
    """Test scenario.

    - Baseline all enabled.
    - Existing RDS active.
    """
    assertion_modifiers = assertion_modifiers_template()

    assertion_modifiers["tower_env"] = {
        "present": {
            "TOWER_DB_URL": "jdbc:mysql://existing.tower-db.com:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true",
        },
        "omitted": {},
    }

    assertion_modifiers["groundswell_env"] = {
        "present": {
            "TOWER_DB_URL": "jdbc:mysql://existing.tower-db.com:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true",
        },
        "omitted": {},
    }

    # NOTE: Current as of Aug 13/2025, Wave-Lite does not support existing db flow.
    # TODO: Extend functionality.
    assertion_modifiers["wave_lite_yml"] = {
        "present": {
            "wave.db.uri": "jdbc:postgresql://wave-db:5432/wave",
        },
        "omitted": {},
    }
    tc_assertions = generate_assertions_all_active(generated_test_files, assertion_modifiers)

    verify_all_assertions(generated_test_files, tc_assertions)


## ------------------------------------------------------------------------------------
## MARK: Existing DB: All Disabled
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.db_existing
@pytest.mark.tfvars("""
    flag_use_aws_ses_iam_integration    = false
    flag_use_existing_smtp              = true
    flag_enable_groundswell             = false
    flag_data_explorer_enabled          = false
    flag_enable_data_studio             = false
    flag_use_wave                       = false
    flag_use_wave_lite                  = false

    flag_create_external_db             = false
    flag_use_existing_external_db       = true
    flag_use_container_db               = false
    tower_db_url                        = "existing.tower-db.com"
    flag_allow_aws_instance_credentials = false
    tower_enable_openapi                = false
    tower_enable_pipeline_versioning        = false
    flag_tower_enable_participant_auto_create_user = false
    flag_tower_enable_member_auto_create_user      = false
    tower_workflow_cleanup_enabled                 = false
""")
def test_existing_db_all_disabled(generated_test_files):
    """Test scenario.

    - Baseline all disabled.
    - Existing RDS active.
    """
    assertion_modifiers = assertion_modifiers_template()

    assertion_modifiers["tower_env"] = {
        "present": {
            "TOWER_DB_URL": "jdbc:mysql://existing.tower-db.com:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true",
        },
        "omitted": {},
    }

    # No need for custom assertion_modifiers -- core testcase handles this one.
    assertion_modifiers["groundswell_env"] = {"present": {}, "omitted": {}}

    # No need for custom assertion_modifiers -- core testcase handles this one.
    assertion_modifiers["wave_lite_yml"] = {"present": {}, "omitted": {}}
    tc_assertions = generate_assertions_all_disabled(generated_test_files, assertion_modifiers)

    verify_all_assertions(generated_test_files, tc_assertions)


## ------------------------------------------------------------------------------------
## MARK: External Redis + Studios (feature pair)
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.redis_external
@pytest.mark.studios
@pytest.mark.tfvars(OFF_BASELINE + STUDIOS_ON_BASE + EXTERNAL_REDIS_ON)
def test_external_redis_with_studios(generated_test_files):
    """External Redis + Studios on: Studios's CONNECT_REDIS_ADDRESS flips to the external endpoint."""
    expected = merge_deltas(
        OFF_BASELINE_ASSERTIONS,
        EXTERNAL_REDIS_ON_ASSERTIONS,
        STUDIOS_ON_BASE_ASSERTIONS,
        # External Redis flips Studios's redis endpoint.
        {"data_studios_env": {"present": {"CONNECT_REDIS_ADDRESS": "mock.tower-redis.com:6379"}}},
    )
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: External Redis + Wave-Lite (feature pair)
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.redis_external
@pytest.mark.wave
@pytest.mark.tfvars(OFF_BASELINE + WAVE_LITE_ON_BASE + EXTERNAL_REDIS_ON)
def test_external_redis_with_wave_lite(generated_test_files):
    """External Redis + Wave-Lite on."""
    expected = merge_deltas(
        OFF_BASELINE_ASSERTIONS,
        EXTERNAL_REDIS_ON_ASSERTIONS,
        WAVE_LITE_ON_BASE_ASSERTIONS,
        # External Redis flips Wave-Lite's redis endpoint and removes the
        # `wave-redis` container from docker_compose (no container Redis when external).
        {
            "wave_lite_yml": {"present": {"redis.uri": "rediss://mock.wave-redis.com:6379"}},
            "docker_compose": {"omitted": {"services.wave-redis"}},
        },
    )
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: New Redis: All Disabled
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.redis_external
@pytest.mark.tfvars(OFF_BASELINE + EXTERNAL_REDIS_ON)
def test_new_redis_all_disabled(generated_test_files):
    """External Redis on top of OFF baseline: TOWER_REDIS_URL points to the external endpoint."""
    expected = merge_deltas(OFF_BASELINE_ASSERTIONS, EXTERNAL_REDIS_ON_ASSERTIONS)
    assert_all_deltas(generated_test_files, expected)


## ------------------------------------------------------------------------------------
## MARK: Seqera Wave: Active
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.wave
@pytest.mark.tfvars(OFF_BASELINE + SEQERA_HOSTED_WAVE_ON)
def test_seqera_hosted_wave_active(generated_test_files):
    """Activating Seqera-hosted Wave from OFF baseline: assert every generated file vs OFF + Wave delta."""
    expected = merge_deltas(OFF_BASELINE_ASSERTIONS, SEQERA_HOSTED_WAVE_ON_ASSERTIONS)
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
