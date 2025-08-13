import pytest
import subprocess
import json
import os
import tempfile
import time
import hashlib
from pathlib import Path
import sys
from copy import deepcopy

from types import SimpleNamespace

from tests.utils.local import root, test_tfvars_target, test_tfvars_override_target, test_case_override_target
from tests.utils.local import prepare_plan, run_terraform_apply, execute_subprocess
from tests.utils.local import parse_key_value_file, read_file, read_yaml, read_json, write_file
from tests.utils.local import get_reconciled_tfvars

from tests.utils.local import ssm_tower, ssm_groundswell, ssm_seqerakit, ssm_wave_lite
from tests.utils.local import templatefile_cache_dir

from tests.utils.local import generate_namespaced_dictionaries, generate_interpolated_templatefiles, all_template_files
from tests.utils.local import set_up_testcase
from tests.utils.local import assert_present_and_omitted

from tests.datafiles.expected_results import generate_baseline_entries_all_active, generate_baseline_entries_all_disabled

from testcontainers.mysql import MySqlContainer


# NOTE: To avoid creating VPC assets, use an existing VPC in the account the AWS provider is configured to use.



overrides_template = {
    "tower_env"         : {},
    "tower_yml"         : {},
    "data_studios_env"  : {},
    "tower_sql"         : {},
    "docker_compose"    : {},
    "wave_lite_yml"     : {},
}

file_targets_all = {
    "tower_env"         : "kv",
    "tower_yml"         : "yml",
    "data_studios_env"  : "kv",
    "tower_sql"         : "sql",
    "docker_compose"    : "yml",
    "wave_lite_yml"     : "yml",
}
# REFERENCE: How to target a subset of files in each testcase versus full set."""
# target_keys = ["docker_compose"]
# needed_template_files = {k: v for k,v in all_template_files.items() if k in target_keys}
# test_template_files = set_up_testcase(plan, needed_template_files)


## ------------------------------------------------------------------------------------
## MARK: Baseline: All Active
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.container
def test_baseline_all_enabled(session_setup):
    """
    Baseline check of configuration.
        - All services enabled (Wave Lite, Groundswell, Data Explorer, Studios)
        - Use of machine identity whenever possible (SES).
        - Use of HTTPS
        - Use of container Redis & DB
        - TODO: No OIDC (have not figured out how to configure in public yet -- maybe use pre-generated environment variables?)
    """

    override_data = """
        # No override values needed. Using base template and base-overrides only.
    """
    # Plan with ALL resources rather than targeted, to get all outputs in plan document.
    plan = prepare_plan(override_data)

    needed_template_files = all_template_files
    test_template_files = set_up_testcase(plan, needed_template_files, sys._getframe().f_code.co_name)

    overrides = deepcopy(overrides_template)
    baseline_all_entries = generate_baseline_entries_all_active(test_template_files, overrides)

    # ------------------------------------------------------------------------------------
    # Test files
    # ------------------------------------------------------------------------------------
    keys = file_targets_all
    
    for key, type in keys.items():
        print(f"Testing {sys._getframe().f_code.co_name}.{key} generated from default settings.")
        file = test_template_files[key]["content"]
        entries = baseline_all_entries[key]
        assert_present_and_omitted(entries, file, type)


## ------------------------------------------------------------------------------------
## MARK: Baseline: All Disabled
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.container
def test_baseline_all_disabled(session_setup):
    """
    Baseline check of configuration.
        - All services disabled (Wave Lite, Groundswell, Data Explorer, Studios)
        - No machine identity (SES).
        - Use of HTTPS
        - Use of container Redis & DB
        - TODO: No OIDC (have not figured out how to configure in public yet -- maybe use pre-generated environment variables?)
    """

    override_data = """
        flag_use_aws_ses_iam_integration    = false
        flag_use_existing_smtp              = true
        flag_enable_groundswell             = false
        flag_data_explorer_enabled          = false
        flag_enable_data_studio             = false
        flag_use_wave                       = false
        flag_use_wave_lite                  = false
    """
    # Plan with ALL resources rather than targeted, to get all outputs in plan document.
    plan = prepare_plan(override_data)

    needed_template_files = all_template_files
    test_template_files = set_up_testcase(plan, needed_template_files, sys._getframe().f_code.co_name)

    overrides = deepcopy(overrides_template)
    baseline_all_entries = generate_baseline_entries_all_disabled(test_template_files, overrides)

    # ------------------------------------------------------------------------------------
    # Test files
    # ------------------------------------------------------------------------------------
    keys = file_targets_all
    
    for key, type in keys.items():
        print(f"Testing {sys._getframe().f_code.co_name}.{key} generated from default settings.")
        file = test_template_files[key]["content"]
        entries = baseline_all_entries[key]
        assert_present_and_omitted(entries, file, type)



## ------------------------------------------------------------------------------------
## MARK: Studios: Path Routing
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.studios
def test_studio_path_routing_enabled(session_setup):
    """
    Confirm configurations when Studio active and path-routing enabled.
    Requires Studios to be active so use 'generate_baseline_entries_all_active'.
    Affects files: 
        - tower.env
        - data_studios.env
    """

    override_data = """
        flag_enable_data_studio         = true
        flag_studio_enable_path_routing = true
        data_studio_path_routing_url    = "connect-example.com"
    """
    # Plan with ALL resources rather than targeted, to get all outputs in plan document.
    plan = prepare_plan(override_data)

    needed_template_files = all_template_files
    test_template_files = set_up_testcase(plan, needed_template_files, sys._getframe().f_code.co_name)

    overrides = deepcopy(overrides_template)
    overrides["tower_env"]= {
        "present": {
            "TOWER_DATA_STUDIO_ENABLE_PATH_ROUTING"     : "true",
            "TOWER_DATA_STUDIO_CONNECT_URL"             : "https://connect-example.com"
        },
        "omitted": {}
    }

    overrides["data_studios_env"]= {
        "present": {
            "CONNECT_PROXY_URL"                         : "https://connect-example.com"
        },
        "omitted": {}
    }

    baseline_all_entries = generate_baseline_entries_all_active(test_template_files, overrides)

    # ------------------------------------------------------------------------------------
    # Test files
    # ------------------------------------------------------------------------------------
    keys = file_targets_all
    
    for key, type in keys.items():
        print(f"Testing {sys._getframe().f_code.co_name}.{key} generated from default settings.")
        file = test_template_files[key]["content"]
        entries = baseline_all_entries[key]
        assert_present_and_omitted(entries, file, type)


## ------------------------------------------------------------------------------------
## MARK: Private CA: Active
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.private_ca
def test_private_ca_reverse_proxy_active(session_setup):
    """
    Confirm configurations when Private CA cert must be served by local reverse-proxy.
    Affects files: 
        - docker-compose.yml
    """

    override_data = """
        flag_create_load_balancer        = false
        flag_use_private_cacert          = true
        flag_do_not_use_https            = false
    """
    # Plan with ALL resources rather than targeted, to get all outputs in plan document.
    plan = prepare_plan(override_data)

    needed_template_files = all_template_files
    test_template_files = set_up_testcase(plan, needed_template_files, sys._getframe().f_code.co_name)

    overrides = deepcopy(overrides_template)
    overrides["docker_compose"]= {
        "present": {
            "services.reverseproxy.container_name" : 'reverseproxy'
        },
        "omitted": {}
    }
    baseline_all_entries = generate_baseline_entries_all_active(test_template_files, overrides)

    # ------------------------------------------------------------------------------------
    # Test docker-compose.yml
    # ------------------------------------------------------------------------------------
    keys = file_targets_all

    for key, type in keys.items():
        print(f"Testing {sys._getframe().f_code.co_name}.{key} generated from default settings.")
        file = test_template_files[key]["content"]
        entries = baseline_all_entries[key]
        assert_present_and_omitted(entries, file, type)


## ------------------------------------------------------------------------------------
## MARK: New DB: All Active
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.db_new
def test_new_db_all_enabled(session_setup):
    """
    Baseline check of configuration.
        - All services enabled (Wave Lite, Groundswell, Data Explorer, Studios)
        - Use of machine identity whenever possible (SES).
        - Use of HTTPS
        - Use of container Redis & DB
        - TODO: No OIDC (have not figured out how to configure in public yet -- maybe use pre-generated environment variables?)
    """

    override_data = """
        flag_create_external_db         = true
        flag_use_existing_external_db   = false
        flag_use_container_db           = false
    """
    # Plan with ALL resources rather than targeted, to get all outputs in plan document.
    plan = prepare_plan(override_data)

    needed_template_files = all_template_files
    test_template_files = set_up_testcase(plan, needed_template_files, sys._getframe().f_code.co_name)

    overrides = deepcopy(overrides_template)
    overrides["tower_env"]= {
        "present": {
            "TOWER_DB_URL"                : "jdbc:mysql://mock.tower-db.com:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true",
        },
        "omitted": {}
    }

    overrides["groundswell_env"]= {
        "present": {
            "TOWER_DB_URL"                : "jdbc:mysql://mock.tower-db.com:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true",
        },
        "omitted": {}
    }

    overrides["wave_lite_yml"]= {
        "present": {
            'wave.db.uri'                 : "jdbc:postgresql://mock.wave-db.com:5432/wave",
        },
        "omitted": {}
    }

    baseline_all_entries = generate_baseline_entries_all_active(test_template_files, overrides)

    # ------------------------------------------------------------------------------------
    # Test files
    # ------------------------------------------------------------------------------------
    keys = file_targets_all
    
    for key, type in keys.items():
        print(f"Testing {sys._getframe().f_code.co_name}.{key} generated from default settings.")
        file = test_template_files[key]["content"]
        entries = baseline_all_entries[key]
        assert_present_and_omitted(entries, file, type)


## ------------------------------------------------------------------------------------
## MARK: New DB: All Disabled
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.db_new
def test_new_db_all_disabled(session_setup):
    """
    Baseline check of configuration.
        - All services disabled (Wave Lite, Groundswell, Data Explorer, Studios)
        - No machine identity (SES).
        - Use of HTTPS
        - Use of container Redis & DB
        - TODO: No OIDC (have not figured out how to configure in public yet -- maybe use pre-generated environment variables?)
    """

    override_data = """
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
    """
    # Plan with ALL resources rather than targeted, to get all outputs in plan document.
    plan = prepare_plan(override_data)

    needed_template_files = all_template_files
    test_template_files = set_up_testcase(plan, needed_template_files, sys._getframe().f_code.co_name)

    overrides = deepcopy(overrides_template)
    overrides["tower_env"]= {
        "present": {
            "TOWER_DB_URL"                : "jdbc:mysql://mock.tower-db.com:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true",
        },
        "omitted": {}
    }

    # No need for custom overrides -- core testcase handles this one.
    overrides["groundswell_env"]= {
        "present": {},
        "omitted": {}
    }

    # No need for custom overrides -- core testcase handles this one.
    overrides["wave_lite_yml"]= {
        "present": {},
        "omitted": {}
    }
    baseline_all_entries = generate_baseline_entries_all_disabled(test_template_files, overrides)

    # ------------------------------------------------------------------------------------
    # Test files
    # ------------------------------------------------------------------------------------
    keys = file_targets_all
    
    for key, type in keys.items():
        print(f"Testing {sys._getframe().f_code.co_name}.{key} generated from default settings.")
        file = test_template_files[key]["content"]
        entries = baseline_all_entries[key]
        assert_present_and_omitted(entries, file, type)


## ------------------------------------------------------------------------------------
## MARK: Existing DB: All Active
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.db_existing
def test_existing_db_all_enabled(session_setup):
    """
    Baseline check of configuration.
        - All services enabled (Wave Lite, Groundswell, Data Explorer, Studios)
        - Use of machine identity whenever possible (SES).
        - Use of HTTPS
        - Use of container Redis & DB
        - TODO: No OIDC (have not figured out how to configure in public yet -- maybe use pre-generated environment variables?)
    """

    override_data = """
        flag_create_external_db         = false
        flag_use_existing_external_db   = true
        flag_use_container_db           = false
        tower_db_url                        = "existing.tower-db.com"
    """
    # Plan with ALL resources rather than targeted, to get all outputs in plan document.
    plan = prepare_plan(override_data)

    needed_template_files = all_template_files
    test_template_files = set_up_testcase(plan, needed_template_files, sys._getframe().f_code.co_name)

    overrides = deepcopy(overrides_template)
    overrides["tower_env"]= {
        "present": {
            "TOWER_DB_URL"                : "jdbc:mysql://existing.tower-db.com:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true",
        },
        "omitted": {}
    }

    overrides["groundswell_env"]= {
        "present": {
            "TOWER_DB_URL"                : "jdbc:mysql://existing.tower-db.com:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true",
        },
        "omitted": {}
    }

    # NOTE: Current as of Aug 13/2025, Wave-Lite does not support existing db flow.
    # TODO: Extend functionality.
    overrides["wave_lite_yml"]= {
        "present": {
            'wave.db.uri'                 : "jdbc:postgresql://wave-db:5432/wave",
        },
        "omitted": {}
    }

    baseline_all_entries = generate_baseline_entries_all_active(test_template_files, overrides)

    # ------------------------------------------------------------------------------------
    # Test files
    # ------------------------------------------------------------------------------------
    keys = file_targets_all
    
    for key, type in keys.items():
        print(f"Testing {sys._getframe().f_code.co_name}.{key} generated from default settings.")
        file = test_template_files[key]["content"]
        entries = baseline_all_entries[key]
        assert_present_and_omitted(entries, file, type)


## ------------------------------------------------------------------------------------
## MARK: New DB: All Disabled
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.db_existing
def test_existing_db_all_disabled(session_setup):
    """
    Baseline check of configuration.
        - All services disabled (Wave Lite, Groundswell, Data Explorer, Studios)
        - No machine identity (SES).
        - Use of HTTPS
        - Use of container Redis & DB
        - TODO: No OIDC (have not figured out how to configure in public yet -- maybe use pre-generated environment variables?)
    """

    override_data = """
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
    """
    # Plan with ALL resources rather than targeted, to get all outputs in plan document.
    plan = prepare_plan(override_data)

    needed_template_files = all_template_files
    test_template_files = set_up_testcase(plan, needed_template_files, sys._getframe().f_code.co_name)

    overrides = deepcopy(overrides_template)
    overrides["tower_env"]= {
        "present": {
            "TOWER_DB_URL"                : "jdbc:mysql://existing.tower-db.com:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true",
        },
        "omitted": {}
    }

    # No need for custom overrides -- core testcase handles this one.
    overrides["groundswell_env"]= {
        "present": {},
        "omitted": {}
    }

    # No need for custom overrides -- core testcase handles this one.
    overrides["wave_lite_yml"]= {
        "present": {},
        "omitted": {}
    }
    baseline_all_entries = generate_baseline_entries_all_disabled(test_template_files, overrides)

    # ------------------------------------------------------------------------------------
    # Test files
    # ------------------------------------------------------------------------------------
    keys = file_targets_all
    
    for key, type in keys.items():
        print(f"Testing {sys._getframe().f_code.co_name}.{key} generated from default settings.")
        file = test_template_files[key]["content"]
        entries = baseline_all_entries[key]
        assert_present_and_omitted(entries, file, type)


## ------------------------------------------------------------------------------------
## MARK: New Redis: All Active
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.redis_external
def test_new_redis_all_enabled(session_setup):
    """
    Baseline check of configuration.
        - All services enabled (Wave Lite, Groundswell, Data Explorer, Studios)
        - Use of machine identity whenever possible (SES).
        - Use of HTTPS
        - Use of container Redis & DB
        - TODO: No OIDC (have not figured out how to configure in public yet -- maybe use pre-generated environment variables?)
    """

    override_data = """
        flag_create_external_redis                      = true
        flag_use_container_redis                        = false
    """
    # Plan with ALL resources rather than targeted, to get all outputs in plan document.
    plan = prepare_plan(override_data)

    needed_template_files = all_template_files
    test_template_files = set_up_testcase(plan, needed_template_files, sys._getframe().f_code.co_name)

    overrides = deepcopy(overrides_template)
    overrides["tower_env"]= {
        "present": {
            "TOWER_REDIS_URL"                : "redis://mock.tower-redis.com:6379",
        },
        "omitted": {}
    }

    overrides["data_studios_env"]= {
        "present": {
            "CONNECT_REDIS_ADDRESS"          : "mock.tower-redis.com:6379",
        },
        "omitted": {}
    }

    overrides["wave_lite_yml"]= {
        "present": {
            'redis.uri'                      : "rediss://mock.wave-redis.com:6379",
        },
        "omitted": {}
    }

    baseline_all_entries = generate_baseline_entries_all_active(test_template_files, overrides)

    # ------------------------------------------------------------------------------------
    # Test files
    # ------------------------------------------------------------------------------------
    keys = file_targets_all
    
    for key, type in keys.items():
        print(f"Testing {sys._getframe().f_code.co_name}.{key} generated from default settings.")
        file = test_template_files[key]["content"]
        entries = baseline_all_entries[key]
        assert_present_and_omitted(entries, file, type)


## ------------------------------------------------------------------------------------
## MARK: New Redis: All Disabled
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.redis_external
def test_new_redis_all_disabled(session_setup):
    """
    Baseline check of configuration.
        - All services disabled (Wave Lite, Groundswell, Data Explorer, Studios)
        - No machine identity (SES).
        - Use of HTTPS
        - Use of container Redis & DB
        - TODO: No OIDC (have not figured out how to configure in public yet -- maybe use pre-generated environment variables?)
    """

    override_data = """
        flag_use_aws_ses_iam_integration    = false
        flag_use_existing_smtp              = true
        flag_enable_groundswell             = false
        flag_data_explorer_enabled          = false
        flag_enable_data_studio             = false
        flag_use_wave                       = false
        flag_use_wave_lite                  = false

        flag_create_external_redis          = true
        flag_use_container_redis            = false
    """
    # Plan with ALL resources rather than targeted, to get all outputs in plan document.
    plan = prepare_plan(override_data)

    needed_template_files = all_template_files
    test_template_files = set_up_testcase(plan, needed_template_files, sys._getframe().f_code.co_name)

    overrides = deepcopy(overrides_template)
    overrides["tower_env"]= {
        "present": {
            "TOWER_REDIS_URL"                : "redis://mock.tower-redis.com:6379",
        },
        "omitted": {}
    }

    # When disabled, none of the settings are present other than comment explaining why.
    # TODO: Harmonize behaviour with other files like Groundswell / Wave-Lite.
    overrides["data_studios_env"]= {
        "present": {},
        "omitted": {
            "CONNECT_REDIS_ADDRESS"          : "N/A",
        }
    }

    overrides["wave_lite_yml"]= {
        "present": {
            'redis.uri'                      : "N/A",
        },
        "omitted": {}
    }
    baseline_all_entries = generate_baseline_entries_all_disabled(test_template_files, overrides)

    # ------------------------------------------------------------------------------------
    # Test files
    # ------------------------------------------------------------------------------------
    keys = file_targets_all
    
    for key, type in keys.items():
        print(f"Testing {sys._getframe().f_code.co_name}.{key} generated from default settings.")
        file = test_template_files[key]["content"]
        entries = baseline_all_entries[key]
        assert_present_and_omitted(entries, file, type)
