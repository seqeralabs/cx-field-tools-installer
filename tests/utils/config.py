from dataclasses import dataclass
from pathlib import Path

from tests.utils.filehandling import FileHelper


## ------------------------------------------------------------------------------------
## Universal Configuration
## ------------------------------------------------------------------------------------
@dataclass
class FilePaths:
    """Absolute paths to tfvars files, cache directories, plan artefacts, and secret JSON fixtures."""

    # NOTE: Assumes this file lives at 3rd layer of project (i.e. PROJECT_ROOT/tests/utils/config.py)
    ROOT: str = str(Path(__file__).parent.parent.parent.resolve())

    TFVARS_BASE: str = ""
    TFVARS_BACKUP: str = ""
    TFVARS_TEST_SRC: str = ""
    TFVARS_TEST_DST: str = ""
    TFVARS_BASE_OVERRIDE_SRC: str = ""
    TFVARS_BASE_OVERRIDE_DST: str = ""
    TFVARS_AUTO_OVERRIDE_DST: str = ""

    CACHE_PLAN_DIR: str = ""
    CACHE_SCENARIO_DIR: str = ""
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

        self.CACHE_PLAN_DIR = f"{self.ROOT}/tests/.plan_cache"
        self.CACHE_SCENARIO_DIR = f"{self.ROOT}/tests/.scenario_cache"
        self.TFPLAN_FILE_LOCATION = f"{self.ROOT}/tfplan"
        self.TFPLAN_JSON_LOCATION = f"{self.ROOT}/tfplan.json"

        self.TOWER_SECRETS = f"{self.ROOT}/tests/datafiles/secrets/ssm_sensitive_values_tower_testing.json"
        self.GROUNDSWELL_SECRETS = f"{self.ROOT}/tests/datafiles/secrets/ssm_sensitive_values_groundswell_testing.json"
        self.SEQERAKIT_SECRETS = f"{self.ROOT}/tests/datafiles/secrets/ssm_sensitive_values_seqerakit_testing.json"
        self.WAVE_LITE_SECRETS = f"{self.ROOT}/tests/datafiles/secrets/ssm_sensitive_values_wave_lite_testing.json"


FP = FilePaths()


# Pre-generated reference files for tests
expected_results_dir = f"{FP.ROOT}/tests/datafiles/expected_results"
expected_sql_dir = f"{expected_results_dir}/expected_sql"


# Master test object (REFERNCE ONLY)
all_template_files = {
    "tower_env": {
        "extension": ".env",
        "read_type": FileHelper.parse_kv,
        "validation_type": "kv",
    },
    "tower_yml": {
        "extension": ".yml",
        "read_type": FileHelper.read_yaml,
        "validation_type": "yml",
    },
    "tower_sql": {
        "extension": ".sql",
        "read_type": FileHelper.read_file,
        "validation_type": "sql",
    },
    "data_studios_env": {
        "extension": ".env",
        "read_type": FileHelper.parse_kv,
        "validation_type": "kv",
    },
    "wave_lite_yml": {
        "extension": ".yml",
        "read_type": FileHelper.read_yaml,
        "validation_type": "yml",
    },
    "docker_compose": {
        "extension": ".yml",
        "read_type": FileHelper.read_yaml,
        "validation_type": "yml",
    },
    "wave_lite_rds": {
        "extension": ".sql",
        "read_type": FileHelper.read_file,
        "validation_type": "sql",
    },
    # TODO: ALL REMAINING
    "groundswell_sql": {
        "extension": ".sql",
        "read_type": FileHelper.read_file,
        "validation_type": "sql",
    },
    "groundswell_env": {
        "extension": ".env",
        "read_type": FileHelper.parse_kv,
        "validation_type": "kv",
    },
    "seqerakit_yml": {
        "extension": ".yml",
        "read_type": FileHelper.read_yaml,
        "validation_type": "yml",
    },
    # TODO: aws_batch_manual
    # TODO: aws_batch_forge
    "cleanse_and_configure_host": {
        "extension": ".sh",
        "read_type": FileHelper.read_file,
        "validation_type": "plain_text",
    },
    # Ansible playbooks are structurally YAML but the only assertions we make on them
    # are substring checks (per the legacy `assert "<task name>" in content` pattern).
    # `validation_type = "plain_text"` routes them to `assert_text_delta` in `assert_all_deltas`.
    # `read_type` stays as `read_yaml` so any consumer that wants the parsed structure
    # still gets it.
    "ansible_02_update_file_configurations": {
        "extension": ".yml",
        "read_type": FileHelper.read_yaml,
        "validation_type": "plain_text",
    },
    "ansible_03_pull_containers_and_run_tower": {
        "extension": ".yml",
        "read_type": FileHelper.read_yaml,
        "validation_type": "plain_text",
    },
    "ansible_05_patch_groundswell": {
        "extension": ".yml",
        "read_type": FileHelper.read_yaml,
        "validation_type": "plain_text",
    },
    "ansible_06_run_seqerakit": {
        "extension": ".yml",
        "read_type": FileHelper.read_yaml,
        "validation_type": "plain_text",
    },
    # TODO: codecommit_seqerakit
    # TODO: ssh_config
    "docker_logging": {
        "extension": ".json",
        "read_type": FileHelper.read_json,
        "validation_type": "plain_text",
    },
    "private_ca_conf": {
        "extension": ".conf",
        "read_type": FileHelper.read_file,
        "validation_type": "plain_text",
    },
}
