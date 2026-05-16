import pytest
from tests.datafiles.expected_results.expected_results import (
    assertion_modifiers_template,
    generate_assertions_all_active,
    generate_assertions_all_disabled,
)
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
def test_baseline_alb_all_enabled(staged_scenario):
    """Conduct baseline assertions when all SP services turned on."""
    assertion_modifiers = assertion_modifiers_template()
    tc_assertions = generate_assertions_all_active(staged_scenario, assertion_modifiers)

    verify_all_assertions(staged_scenario, tc_assertions)


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
def test_baseline_alb_all_disabled(staged_scenario):
    """Conduct baseline assertions when all SP services turned off."""
    # TODO: Get rid of email disabling. This should be a discrete check.
    assertion_modifiers = assertion_modifiers_template()
    tc_assertions = generate_assertions_all_disabled(staged_scenario, assertion_modifiers)

    verify_all_assertions(staged_scenario, tc_assertions)


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
def test_private_ca_reverse_proxy_active(staged_scenario):
    """Test scenario.

    - Baseline all enabled.
    - Reverseproxy with self-signed private CA active.
    """
    assertion_modifiers = assertion_modifiers_template()
    assertion_modifiers["docker_compose"] = {
        "present": {"services.reverseproxy.labels.seqera": "reverseproxy"},
        "omitted": {},
    }

    tc_assertions = generate_assertions_all_active(staged_scenario, assertion_modifiers)
    verify_all_assertions(staged_scenario, tc_assertions)


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
def test_studio_path_routing_enabled(staged_scenario):
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
    tc_assertions = generate_assertions_all_active(staged_scenario, assertion_modifiers)

    verify_all_assertions(staged_scenario, tc_assertions)


## ------------------------------------------------------------------------------------
## MARK: Studios SSH: Enabled
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.studios
@pytest.mark.tfvars("""
    flag_enable_data_studio_ssh = true
    flag_limit_data_studio_ssh_to_some_workspaces = false
""")
def test_studio_ssh_enabled(staged_scenario):
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

    tc_assertions = generate_assertions_all_active(staged_scenario, assertion_modifiers)
    verify_all_assertions(staged_scenario, tc_assertions)


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
def test_studio_ssh_enabled_workspace_restriction(staged_scenario):
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

    tc_assertions = generate_assertions_all_active(staged_scenario, assertion_modifiers)
    verify_all_assertions(staged_scenario, tc_assertions)


## ------------------------------------------------------------------------------------
## MARK: Studios SSH: Disabled
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.studios
@pytest.mark.tfvars("""
    flag_enable_data_studio_ssh = false
""")
def test_studio_ssh_disabled(staged_scenario):
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

    tc_assertions = generate_assertions_all_active(staged_scenario, assertion_modifiers)
    verify_all_assertions(staged_scenario, tc_assertions)


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
def test_new_db_all_enabled(staged_scenario):
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

    tc_assertions = generate_assertions_all_active(staged_scenario, assertion_modifiers)
    verify_all_assertions(staged_scenario, tc_assertions)


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
def test_new_db_all_disabled(staged_scenario):
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
    tc_assertions = generate_assertions_all_disabled(staged_scenario, assertion_modifiers)

    verify_all_assertions(staged_scenario, tc_assertions)


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
def test_existing_db_all_enabled(staged_scenario):
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
    tc_assertions = generate_assertions_all_active(staged_scenario, assertion_modifiers)

    verify_all_assertions(staged_scenario, tc_assertions)


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
def test_existing_db_all_disabled(staged_scenario):
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
    tc_assertions = generate_assertions_all_disabled(staged_scenario, assertion_modifiers)

    verify_all_assertions(staged_scenario, tc_assertions)


## ------------------------------------------------------------------------------------
## MARK: New Redis: All Active
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.redis_external
@pytest.mark.tfvars("""
    flag_create_external_redis                      = true
    flag_use_container_redis                        = false
""")
def test_new_redis_all_enabled(staged_scenario):
    """Test scenario.

    - Baseline all enabled.
    - Elasticache Redis active.
    """
    assertion_modifiers = assertion_modifiers_template()

    assertion_modifiers["tower_env"] = {
        "present": {
            "TOWER_REDIS_URL": "redis://mock.tower-redis.com:6379",
        },
        "omitted": {},
    }

    assertion_modifiers["data_studios_env"] = {
        "present": {
            "CONNECT_REDIS_ADDRESS": "mock.tower-redis.com:6379",
        },
        "omitted": {},
    }

    assertion_modifiers["wave_lite_yml"] = {
        "present": {
            "redis.uri": "rediss://mock.wave-redis.com:6379",
        },
        "omitted": {},
    }

    assertion_modifiers["docker_compose"] = {
        "present": {
            "services.wave-lite.labels.seqera": "wave-lite",
            "services.wave-lite-reverse-proxy.labels.seqera": "wave-lite-reverse-proxy",
            "services.wave-db.labels.seqera": "wave-db",
        },
        "omitted": {
            "services.wave-redis": "",
        },
    }

    tc_assertions = generate_assertions_all_active(staged_scenario, assertion_modifiers)
    verify_all_assertions(staged_scenario, tc_assertions)


## ------------------------------------------------------------------------------------
## MARK: New Redis: All Disabled
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.redis_external
@pytest.mark.tfvars("""
    flag_use_aws_ses_iam_integration    = false
    flag_use_existing_smtp              = true
    flag_enable_groundswell             = false
    flag_data_explorer_enabled          = false
    flag_enable_data_studio             = false
    flag_use_wave                       = false
    flag_use_wave_lite                  = false

    flag_create_external_redis          = true
    flag_use_container_redis            = false
    flag_allow_aws_instance_credentials = false
    tower_enable_openapi                = false
    tower_enable_pipeline_versioning        = false
    flag_tower_enable_participant_auto_create_user = false
    flag_tower_enable_member_auto_create_user      = false
    tower_workflow_cleanup_enabled                 = false
""")
def test_new_redis_all_disabled(staged_scenario):
    """Test scenario.

    - Baseline all disabled.
    - Elasticache Redis active.
    """
    assertion_modifiers = assertion_modifiers_template()

    assertion_modifiers["tower_env"] = {
        "present": {
            "TOWER_REDIS_URL": "redis://mock.tower-redis.com:6379",
        },
        "omitted": {},
    }

    # When disabled, none of the settings are present other than comment explaining why.
    # TODO: Harmonize behaviour with other files like Groundswell / Wave-Lite.
    assertion_modifiers["data_studios_env"] = {
        "present": {},
        "omitted": {
            "CONNECT_REDIS_ADDRESS": "N/A",
        },
    }

    assertion_modifiers["wave_lite_yml"] = {
        "present": {
            "redis.uri": "N/A",
        },
        "omitted": {},
    }
    tc_assertions = generate_assertions_all_disabled(staged_scenario, assertion_modifiers)

    verify_all_assertions(staged_scenario, tc_assertions)


## ------------------------------------------------------------------------------------
## MARK: Seqera Wave: Active
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.wave
@pytest.mark.tfvars("""
    flag_use_aws_ses_iam_integration    = false
    flag_use_existing_smtp              = true
    flag_enable_groundswell             = false
    flag_data_explorer_enabled          = false
    flag_enable_data_studio             = false
    # flag_use_wave                     = false
    flag_use_wave_lite                  = false

    flag_use_wave                       = true
    wave_server_url                     = "wave.seqera.io"
    flag_tower_enable_participant_auto_create_user = false
    flag_tower_enable_member_auto_create_user      = false
    tower_workflow_cleanup_enabled                 = false
""")
def test_seqera_hosted_wave_active(staged_scenario):
    """Test scenario.

    - Baseline all disabled.
    - Seqera-hosted Wave active.
    """
    assertion_modifiers = assertion_modifiers_template()

    assertion_modifiers["tower_env"] = {
        "present": {
            "WAVE_SERVER_URL": "https://wave.seqera.io",
        },
        "omitted": {},
    }

    assertion_modifiers["wave_lite_yml"] = {
        "present": {
            "wave.server.url": "https://wave.seqera.io",
        },
        "omitted": {},
    }
    tc_assertions = generate_assertions_all_disabled(staged_scenario, assertion_modifiers)

    verify_all_assertions(staged_scenario, tc_assertions)


## ------------------------------------------------------------------------------------
## MARK: Wave-Lite SQL
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.wave
def test_wave_sql_file_content(staged_scenario):
    """Test scenario.

    - Use the SQL files generated by the baseline testcase.
    - Compare against pre-generated result files in `tests/datafiles/expected_results/expected_sql`.
    """
    ## COMPARISON
    ## ========================================================================================
    wave_lite_rds = FileHelper.read_file(f"{staged_scenario['wave_lite_rds']['filepath']}")
    ref_wave_lite_rds = FileHelper.read_file(f"{expected_sql_dir}/wave-lite-rds.sql")

    assert ref_wave_lite_rds == wave_lite_rds
