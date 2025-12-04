import os
from dataclasses import dataclass, field
from pathlib import Path

from tests.utils.filehandling import FileHelper


## ------------------------------------------------------------------------------------
## Universal Configuration
## ------------------------------------------------------------------------------------
# Control how many files are generated for each testcase: every config file or just minimally necessary ones.
# Use limited set by default, but make configurable from pytest invocation (e.g: `TEST_FULL=true pytest tests/unit`)
def get_kitchen_sink_bool(key, default=False):
    value = os.environ.get(key)
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on")


kitchen_sink = get_kitchen_sink_bool("TEST_FULL")


@dataclass
class FilePaths:
    # NOTE: Assumes this file lives at 3rd layer of project (i.e. PROJECT_ROOT/tests/utils/local.py)
    ROOT: str = str(Path(__file__).parent.parent.parent.resolve())

    TFVARS_BASE: str = ""
    TFVARS_BACKUP: str = ""
    TFVARS_TEST_SRC: str = ""
    TFVARS_TEST_DST: str = ""
    TFVARS_BASE_OVERRIDE_SRC: str = ""
    TFVARS_BASE_OVERRIDE_DST: str = ""
    TFVARS_AUTO_OVERRIDE_DST: str = ""
    OUTPUTS_SRC: str = ""
    OUTPUTS_DST: str = ""

    CACHE_PLAN_DIR: str = ""
    CACHE_TEMPLATEFILE_DIR: str = ""
    TFPLAN_FILE_LOCATION: str = ""
    TFPLAN_JSON_LOCATION: str = ""

    TOWER_SECRETS: str = ""
    GROUNDSWELL_SECRETS: str = ""
    SEQERAKIT_SECRETS: str = ""
    WAVE_LITE_SECRETS: str = ""

    def __post_init__(self):
        self.TFVARS_BASE = f"{self.ROOT}/terraform.tfvars"
        self.TFVARS_BACKUP = f"{self.ROOT}/terraform.tfvars.backup"
        self.TFVARS_TEST_SRC = f"{self.ROOT}/tests/datafiles/terraform.tfvars"
        self.TFVARS_TEST_DST = self.TFVARS_BASE
        self.TFVARS_BASE_OVERRIDE_SRC = f"{self.ROOT}/tests/datafiles/base-overrides.auto.tfvars"
        self.TFVARS_BASE_OVERRIDE_DST = f"{self.ROOT}/base-overrides.auto.tfvars"
        self.TFVARS_AUTO_OVERRIDE_DST = f"{self.ROOT}/override.auto.tfvars"
        self.OUTPUTS_SRC = f"{self.ROOT}/tests/datafiles/012_testing_outputs.tf"
        self.OUTPUTS_DST = f"{self.ROOT}/012_testing_outputs.tf"

        self.CACHE_PLAN_DIR = f"{self.ROOT}/tests/.plan_cache"
        self.CACHE_TEMPLATEFILE_DIR = f"{self.ROOT}/tests/.templatefile_cache"
        self.TFPLAN_FILE_LOCATION = f"{self.ROOT}/tfplan"
        self.TFPLAN_JSON_LOCATION = f"{self.ROOT}/tfplan.json"

        self.TOWER_SECRETS = f"{self.ROOT}/tests/datafiles/secrets/ssm_sensitive_values_tower_testing.json"
        self.GROUNDSWELL_SECRETS = f"{self.ROOT}/tests/datafiles/secrets/ssm_sensitive_values_groundswell_testing.json"
        self.SEQERAKIT_SECRETS = f"{self.ROOT}/tests/datafiles/secrets/ssm_sensitive_values_seqerakit_testing.json"
        self.WAVE_LITE_SECRETS = f"{self.ROOT}/tests/datafiles/secrets/ssm_sensitive_values_wave_lite_testing.json"


@dataclass
class TCValues:
    # Convenience object for passing around the dictionary sets used to configure templatefiles
    vars: dict = field(default_factory=dict)
    outputs: dict = field(default_factory=dict)
    tower_secrets: dict = field(default_factory=dict)
    groundswell_secrets: dict = field(default_factory=dict)
    seqerakit_secrets: dict = field(default_factory=dict)
    wave_lite_secrets: dict = field(default_factory=dict)


FP = FilePaths()


# SSM (testing) secrets


# Cache folders & tfplan paths


# Pre-generated reference files for tests
expected_results_dir = f"{FP.ROOT}/tests/datafiles/expected_results"
expected_sql_dir = f"{expected_results_dir}/expected_sql"


# Master test object
all_template_files = {
    "tower_env": {
        "extension": ".env",
        "read_type": FileHelper.parse_kv,
        "content": "",
        "filepath": "",
        "validation_type": "kv",
    },
    "tower_yml": {
        "extension": ".yml",
        "read_type": FileHelper.read_yaml,
        "content": "",
        "filepath": "",
        "validation_type": "yml",
    },
    "tower_sql": {
        "extension": ".sql",
        "read_type": FileHelper.read_file,
        "content": "",
        "filepath": "",
        "validation_type": "sql",
    },
    "data_studios_env": {
        "extension": ".env",
        "read_type": FileHelper.parse_kv,
        "content": "",
        "filepath": "",
        "validation_type": "kv",
    },
    "wave_lite_yml": {
        "extension": ".yml",
        "read_type": FileHelper.read_yaml,
        "content": "",
        "filepath": "",
        "validation_type": "yml",
    },
    "docker_compose": {
        "extension": ".yml",
        "read_type": FileHelper.read_yaml,
        "content": "",
        "filepath": "",
        "validation_type": "yml",
    },
    "wave_lite_rds": {
        "extension": ".sql",
        "read_type": FileHelper.read_file,
        "content": "",
        "filepath": "",
        "validation_type": "sql",
    },
    # TODO: ALL REMAINING
    "groundswell_sql": {
        "extension": ".sql",
        "read_type": FileHelper.read_file,
        "content": "",
        "filepath": "",
        "validation_type": "sql",
    },
    "groundswell_env": {
        "extension": ".env",
        "read_type": FileHelper.parse_kv,
        "content": "",
        "filepath": "",
        "validation_type": "kv",
    },
    "seqerakit_yml": {
        "extension": ".yml",
        "read_type": FileHelper.read_yaml,
        "content": "",
        "filepath": "",
        "validation_type": "yml",
    },
    # TODO: aws_batch_manual
    # TODO: aws_batch_forge
    "cleanse_and_configure_host": {
        "extension": ".sh",
        "read_type": FileHelper.read_file,
        "content": "",
        "filepath": "",
        "validation_type": "TBD",
    },
    "ansible_02_update_file_configurations": {
        "extension": ".yml",
        "read_type": FileHelper.read_yaml,
        "content": "",
        "filepath": "",
        "validation_type": "yml",
    },
    "ansible_03_pull_containers_and_run_tower": {
        "extension": ".yml",
        "read_type": FileHelper.read_yaml,
        "content": "",
        "filepath": "",
        "validation_type": "yml",
    },
    "ansible_05_patch_groundswell": {
        "extension": ".yml",
        "read_type": FileHelper.read_yaml,
        "content": "",
        "filepath": "",
        "validation_type": "yml",
    },
    "ansible_06_run_seqerakit": {
        "extension": ".yml",
        "read_type": FileHelper.read_yaml,
        "content": "",
        "filepath": "",
        "validation_type": "yml",
    },
    # TODO: codecommit_seqerakit
    # TODO: ssh_config
    "docker_logging": {
        "extension": ".json",
        "read_type": FileHelper.read_json,
        "content": "",
        "filepath": "",
        "validation_type": "TBD",
    },
    "private_ca_conf": {
        "extension": ".conf",
        "read_type": FileHelper.read_file,
        "content": "",
        "filepath": "",
        "validation_type": "TBD",
    },
}

# Subset of SP config files
config_file_list = [
    "tower_env",
    "tower_yml",
    "data_studios_env",
    "tower_sql",
    "docker_compose",
    "wave_lite_yml",
    "wave_lite_rds",
    "groundswell_env",
]

# Subset of Ansible files
ansible_file_list = [
    "ansible_02_update_file_configurations",
    "ansible_03_pull_containers_and_run_tower",
    "ansible_05_patch_groundswell",
    "ansible_06_run_seqerakit",
]

all_config_files = {k: v for k, v in all_template_files.items() if k in config_file_list}
all_ansible_files = {k: v for k, v in all_template_files.items() if k in ansible_file_list}
