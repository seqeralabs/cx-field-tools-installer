import os
from pathlib import Path

from tests.utils.filehandling import read_json, read_yaml, read_file
from tests.utils.filehandling import write_file, move_file, copy_file
from tests.utils.filehandling import parse_key_value_file


## ------------------------------------------------------------------------------------
## Universal Configuration
## ------------------------------------------------------------------------------------
# Control how many files are generated for each testcase: every config file or just minimally necessary ones.
# Use limited set by default, but make configurable from pytest invocation (e.g: `KITCHEN_SINK=true pytest tests/unit`)
def get_kitchen_sink_bool(key, default=False):
    value = os.environ.get(key)
    if value is None:
        return default
    return value.lower() in ('true', '1', 'yes', 'on')

kitchen_sink = get_kitchen_sink_bool('KITCHEN_SINK')


# Assumes this file lives at 3rd layer of project (i.e. PROJECT_ROOT/tests/utils/local.py)
root = str(Path(__file__).parent.parent.parent.resolve())

# Tfvars and override files filepaths
tfvars_path                         = f"{root}/terraform.tfvars"
tfvars_backup_path                  = f"{root}/terraform.tfvars.backup"

test_tfvars_source                  = f"{root}/tests/datafiles/terraform.tfvars"
test_tfvars_target                  = f"{root}/terraform.tfvars"
test_tfvars_override_source         = f"{root}/tests/datafiles/base-overrides.auto.tfvars"
test_tfvars_override_target         = f"{root}/base-overrides.auto.tfvars"

test_case_override_target           = f"{root}/override.auto.tfvars"
test_case_override_outputs_source   = f"{root}/tests/datafiles/012_testing_outputs.tf"
test_case_override_outputs_target   = f"{root}/012_testing_outputs.tf"

test_docker_compose_file            = f"/tmp/cx-testing-docker-compose.yml"

# SSM (testing) secrets
secrets_dir                         = f"{root}/tests/datafiles/secrets"
ssm_tower                           = f"{secrets_dir}/ssm_sensitive_values_tower_testing.json"
ssm_groundswell                     = f"{secrets_dir}/ssm_sensitive_values_groundswell_testing.json"
ssm_seqerakit                       = f"{secrets_dir}/ssm_sensitive_values_seqerakit_testing.json"
ssm_wave_lite                       = f"{secrets_dir}/ssm_sensitive_values_wave_lite_testing.json"

# Tfplan files and caching folder
plan_cache_dir                      = f"{root}/tests/.plan_cache"

test_case_tfplan_file               = f"{root}/tfplan"
test_case_tfplan_json_file          = f"{root}/tfplan.json"

templatefile_cache_dir              = f"{root}/tests/.templatefile_cache"

sql_test_scratch_dir                     = "/tmp/cx-testing/sql"
expected_sql                        = f"{root}/tests/datafiles/expected_results/expected_sql"

all_template_files = {
    "tower_env": {
        "extension"         : ".env", 
        "read_type"         : parse_key_value_file,
        "content"           : "",
        "filepath"          : "",
        "validation_type"   : "kv",
    },
    "tower_yml": {
        "extension"         : ".yml", 
        "read_type"         : read_yaml,
        "content"           : "",
        "filepath"          : "",
        "validation_type"   : "yml",
    },
    "tower_sql": {
        "extension"         : ".sql", 
        "read_type"         : read_file,
        "content"           : "",
        "filepath"          : "",
        "validation_type"   : "sql",
    },
    "data_studios_env": {
        "extension"         : ".env", 
        "read_type"         : parse_key_value_file,
        "content"           : "",
        "filepath"          : "",
        "validation_type"   : "kv",
    },
    "wave_lite_yml": {
        "extension"         : ".yml", 
        "read_type"         : read_yaml,
        "content"           : "",
        "filepath"          : "",
        "validation_type"   : "yml",
    },
    "docker_compose": {
        "extension"         : ".yml", 
        "read_type"         : read_yaml,
        "content"           : "",
        "filepath"          : "",
        "validation_type"   : "yml",
    },
    "wave_lite_container_1": {
        "extension"         : ".sql", 
        "read_type"         : read_file,
        "content"           : "",
        "filepath"          : "",
        "validation_type"   : "sql",
    },
    "wave_lite_container_2": {
        "extension"         : ".sql", 
        "read_type"         : read_file,
        "content"           : "",
        "filepath"          : "",
        "validation_type"   : "sql",
    },
    "wave_lite_rds": {
        "extension"         : ".sql", 
        "read_type"         : read_file,
        "content"           : "",
        "filepath"          : "",
        "validation_type"   : "sql",
    },

    # TODO: ALL REMAINING
    "groundswell_sql": {
        "extension"         : ".sql", 
        "read_type"         : read_file,
        "content"           : "",
        "filepath"          : "",
        "validation_type"   : "sql",
    },
    "groundswell_env": {
        "extension"         : ".env", 
        "read_type"         : parse_key_value_file,
        "content"           : "",
        "filepath"          : "",
        "validation_type"   : "kv",
    },
    "seqerakit_yml": {
        "extension"         : ".yml", 
        "read_type"         : read_yaml,
        "content"           : "",
        "filepath"          : "",
        "validation_type"   : "yml",
    },
    # TODO: aws_batch_manual
    # TODO: aws_batch_forge
    "cleanse_and_configure_host": {
        "extension"         : ".sh", 
        "read_type"         : read_file,
        "content"           : "",
        "filepath"          : "",
        "validation_type"   : "TBD",
    },
    "ansible_02_update_file_configurations": {
        "extension"         : ".yml", 
        "read_type"         : read_yaml,
        "content"           : "",
        "filepath"          : "",
        "validation_type"   : "yml",
    },
    "ansible_03_pull_containers_and_run_tower": {
        "extension"         : ".yml", 
        "read_type"         : read_yaml,
        "content"           : "",
        "filepath"          : "",
        "validation_type"   : "yml",
    },
    "ansible_05_patch_groundswell": {
        "extension"         : ".yml", 
        "read_type"         : read_yaml,
        "content"           : "",
        "filepath"          : "",
        "validation_type"   : "yml",
    },
    "ansible_06_run_seqerakit": {
        "extension"         : ".yml", 
        "read_type"         : read_yaml,
        "content"           : "",
        "filepath"          : "",
        "validation_type"   : "yml",
    },
    # TODO: codecommit_seqerakit
    # TODO: ssh_config
    "docker_logging": {
        "extension"         : ".json", 
        "read_type"         : read_json,
        "content"           : "",
        "filepath"          : "",
        "validation_type"   : "TBD",
    },
    "private_ca_conf": {
        "extension"         : ".conf", 
        "read_type"         : read_file,
        "content"           : "",
        "filepath"          : "",
        "validation_type"   : "TBD",
    },
}

# Generate subset of config files to make sure we don't pull in more files than the validation can handle.
config_file_list = [
    "tower_env",
    "tower_yml",
    "data_studios_env",
    "tower_sql" ,
    "docker_compose",
    "wave_lite_yml",
    "wave_lite_container_1",
    "wave_lite_container_2",
    "wave_lite_rds",
]

all_config_files = {k:v for k,v in all_template_files.items() if k in config_file_list}

