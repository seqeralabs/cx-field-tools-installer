"""OFF baseline + per-feature delta constants for the assertion retrofit.

Constants come in **pairs**, one for each side of a test:

  * `<NAME>`              — tfvars string (input side).        Consumed by `@pytest.mark.tfvars(...)`.
  * `<NAME>_ASSERTIONS`   — nested assertion dict (output side). Consumed by `merge_deltas(...)`.

The two halves of a pair describe the same scenario from different sides — what to
configure (tfvars) and what should result (rendered file state) — and should be
kept in sync. The naming convention makes drift obvious in code review.

----------------------------------------------------------------------------------------
Base baseline
----------------------------------------------------------------------------------------
`BASELINE` is a tfvars string that turns off every feature that
`tests/datafiles/generate_core_data.sh` enables by default via
`base-overrides.auto.tfvars`. Tests stage this directly to render the off-state,
or concatenate `BASELINE + <FEATURE>_ON` to activate one feature on top.

`BASELINE_ASSERTIONS` is the *expected post-state* of every generated file when
only `BASELINE` is applied. Tests overlay one or more per-feature `_ASSERTIONS`
constants on top via `merge_deltas(BASELINE_ASSERTIONS, <FEATURE>_ON_ASSERTIONS, ...)`
to get the expected state for a given scenario, then call the appropriate
`assert_*_delta` helper per template.

----------------------------------------------------------------------------------------
Per-feature deltas
----------------------------------------------------------------------------------------
`<FEATURE>_ON` is a tfvars string fragment that enables one feature. Concatenated onto
`BASELINE` it produces a single-feature-on scenario.

`<FEATURE>_ON_ASSERTIONS` is the nested-dict delta — `{template_name: {"present": {...},
"omitted": {...}}}` — declaring only the keys that differ from `BASELINE_ASSERTIONS`
when this feature is enabled.

**Convention: each `<FEATURE>_ON_ASSERTIONS` captures the feature's effects assuming
containerised defaults for every other knob** (container DB, container Redis, etc.).
Cross-feature interactions — e.g. external Redis flipping Studios's
`CONNECT_REDIS_ADDRESS`, or Wave-Lite + external Redis removing the `wave-redis`
container — are NOT baked into individual `<FEATURE>_ON_ASSERTIONS` constants. They're
declared inline at the test site as an additional dict passed to `merge_deltas(...)`.
This keeps each feature constant composable: it produces the same effects whether
stacked with one feature or three.

Canonical test shape:

    @pytest.mark.tfvars(BASELINE + WAVE_SEQERA_HOSTED_ACTIVE)
    def test_wave_on(generated_test_files):
        expected = merge_deltas(BASELINE_ASSERTIONS, WAVE_SEQERA_HOSTED_ACTIVE_ASSERTIONS)
        assert_all_deltas(generated_test_files, expected)

Co-located with `test_config_file_content.py` so the test file stays focused on
test logic and the constants stay focused on expected-state declarations.
"""

from tests.utils.config import expected_sql_dir
from tests.utils.filehandling.filehandling import FileHelper


# MARK: ----- TFVARS
BASELINE = """
    flag_use_existing_smtp              = true
    flag_use_aws_ses_iam_integration    = false
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
    flag_enable_preflight_checks                   = false
    tower_aws_secrets_kms_key_id                   = ""
    # tower_actions is written on one line so the fragment dedup ("last wins", per line) can override it.
    tower_actions = { bucket_trigger_allowed_workspaces = "", cron_trigger_allowed_workspaces = "", pipeline_trigger_allowed_workspaces = "", trigger_rate_max_per_window = 20, trigger_rate_window = "1h" }
"""  # noqa: E501

REDIS_EXTERNAL_ACTIVE = """
    flag_create_external_redis = true
    flag_use_container_redis   = false
"""

DB_EXTERNAL_NEW_ACTIVE = """
    flag_create_external_db       = true
    flag_use_existing_external_db = false
    flag_use_container_db         = false
"""

DB_EXTERNAL_EXISTING_ACTIVE = """
    flag_use_existing_external_db = true
    flag_use_container_db         = false
    tower_db_url                  = "existing.tower-db.com"
"""

STUDIOS_ACTIVE = """
    flag_enable_data_studio = true
"""

STUDIOS_PATH_ROUTING_ACTIVE = """
    flag_studio_enable_path_routing = true
    data_studio_path_routing_url    = "connect-example.com"
"""

STUDIOS_SSH_ACTIVE = """
    flag_enable_data_studio_ssh                   = true
    flag_limit_data_studio_ssh_to_some_workspaces = false
"""

STUDIOS_SSH_WORKSPACE_RESTRICTION_ACTIVE = """
    flag_limit_data_studio_ssh_to_some_workspaces = true
    data_studio_ssh_eligible_workspaces           = "12,34"
"""

WAVE_SEQERA_HOSTED_ACTIVE = """
    flag_use_wave   = true
    wave_server_url = "wave.seqera.io"
"""

WAVE_LITE_ACTIVE = """
    flag_use_wave_lite = true
"""

GROUNDSWELL_ACTIVE = """
    flag_enable_groundswell = true
"""

DATA_EXPLORER_ACTIVE = """
    flag_data_explorer_enabled = true
"""

AWS_SES_ACTIVE = """
    flag_use_aws_ses_iam_integration = true
    flag_use_existing_smtp           = false
"""

TOWER_OPT_IN_FLAGS_ACTIVE = """
    flag_allow_aws_instance_credentials            = true
    tower_enable_openapi                           = true
    tower_enable_pipeline_versioning               = true
    flag_tower_enable_participant_auto_create_user = true
    flag_tower_enable_member_auto_create_user      = true
    tower_workflow_cleanup_enabled                 = true
    flag_enable_preflight_checks                   = true
    tower_actions = { bucket_trigger_allowed_workspaces = "-1", cron_trigger_allowed_workspaces = "12,34", pipeline_trigger_allowed_workspaces = "56", trigger_rate_max_per_window = 50, trigger_rate_window = "2h" }
    tower_aws_secrets_kms_key_id = "arn:aws:kms:us-east-1:123456789012:key/1234abcd-12ab-34cd-56ef-1234567890ab"
"""  # noqa: E501

PRIVATE_CA_REVERSE_PROXY_ACTIVE = """
    flag_create_load_balancer = false
    flag_use_private_cacert   = true
    flag_do_not_use_https     = false
"""

HOSTS_FILE_ENTRY_ACTIVE = """
    flag_create_hosts_file_entry = true
"""

INSECURE_HTTP_ACTIVE = """
    flag_do_not_use_https = true
"""

DATA_LINEAGE_ACTIVE = """
    flag_enable_data_lineage = true
"""

DATA_LINEAGE_WORKSPACE_RESTRICTION_ACTIVE = """
    data_lineage_options = {
        allowed_workspaces    = "12,34"
        store_prefix          = "seqera-lineage"
        sns_max_retries       = 17
        sns_max_delay_seconds = 300
        migrate_sqs_transport = true
        global_search_enabled = true
    }
"""

COMPUTE_ENV_CLEANUP_ACTIVE = """
    tower_compute_env_cleanup = {
      enabled = true
    }
"""

AUDIT_LOG_V2_CLEANUP_DISABLED_ACTIVE = """
    tower_audit_log_v2 = {
      cleanup = { enabled = false }
    }
"""

FRONTEND_PRE_26_2_ACTIVE = """
    tower_container_version = "v26.1.3"
"""

IDENTITY_FEDERATION_ACTIVE = """
    tower_identity_federation_enabled = true
"""

DB_TLS_DISABLED_ACTIVE = """
    db_enforce_tls = false
"""

DB_8_0_ACTIVE = """
    db_container_engine_version = "8.0"
"""

IDENTITY_FEDERATION_WORKSPACE_RESTRICTION_ACTIVE = """
    tower_identity_federation_allowed_workspaces = "12,34"
"""

TELEMETRY_BASIC_ACTIVE = """
    flag_enable_standard_telemetry = "basic"
"""

TELEMETRY_AIR_GAPPED_ACTIVE = """
    flag_enable_standard_telemetry = "air-gapped"
"""

TELEMETRY_OPTIONS_CUSTOM_ACTIVE = """
    telemetry_options = {
      window_days          = 30
      file_collector_delay = "10m"
    }
"""

STUDIOS_PRIVATE_CA_ACTIVE = """
    flag_run_studios_via_private_ca = true
"""


## ------------------------------------------------------------------------------------
## MARK: ----- Assertions
## OFF baseline expected post-state (per template)
## ------------------------------------------------------------------------------------
# Section comments (`# CREDENTIALS`, `# MAIL`, etc.) group related keys for readability —
# they were originally ported from the deleted `generate_*_all_disabled` functions and the
# grouping is preserved as a navigation aid. The literal `"# XYZ_NOT_ENABLED"` dict keys are
# actual key/value entries the rendered .env files contain (rendered with a leading `#`
# as a commented-out marker line, but parsed as a regular `key=value` by `FileHelper.parse_kv`).
BASELINE_ASSERTIONS = {
    "tower_env": {
        "present": {
            "TOWER_ENABLE_AWS_SSM": "true",
            "TOWER_SERVER_URL": "https://autodc.dev-seqera.net",
            "TOWER_CONTACT_EMAIL": "graham.wright@seqera.io",
            "TOWER_ENABLE_PLATFORMS": "awsbatch-platform,slurm-platform",
            "TOWER_ROOT_USERS": "graham.wright@seqera.io,gwright99@hotmail.com",
            "TOWER_DB_URL": "jdbc:mysql://db:3306/tower?useSSL=true&trustServerCertificate=true&permitMysqlScheme=true",
            "TOWER_DB_DRIVER": "org.mariadb.jdbc.Driver",
            "TOWER_DB_DIALECT": "io.seqera.util.MySQL55DialectCollateBin",
            "TOWER_DB_MIN_POOL_SIZE": 5,
            "TOWER_DB_MAX_POOL_SIZE": 10,
            "TOWER_DB_MAX_LIFETIME": 18000000,
            "TOWER_REDIS_URL": "redis://redis:6379",
            "TOWER_ENABLE_UNSAFE_MODE": "false",
            "TOWER_ENABLE_OPENAPI": "false",
            # CREDENTIALS
            "TOWER_ALLOW_INSTANCE_CREDENTIALS": "false",
            # OIDC
            # MAIL
            "TOWER_ENABLE_AWS_SES": "false",
            "TOWER_SMTP_HOST": "email-smtp.us-east-1.amazonaws.com",
            "TOWER_SMTP_PORT": "587",
            # WAVE
            "TOWER_ENABLE_WAVE": "false",
            "WAVE_SERVER_URL": "N/A",
            # GROUNDSWELL
            "TOWER_ENABLE_GROUNDSWELL": "false",
            # DATA_EXPLORER
            "TOWER_DATA_EXPLORER_ENABLED": "false",
            # DATA_STUDIOS
            "# STUDIOS_NOT_ENABLED": "DO_NOT_UNCOMMENT",
            # PIPELINE_VERSIONING
            "# TOWER_PIPELINE_VERSIONING_NOT_ENABLED": "DO_NOT_UNCOMMENT",
            # DATA_LINEAGE
            # v26.2.0+ (test pin `v26.2.0-RC16`): lineage off renders `-1`, since unset means all workspaces.
            "TOWER_LINEAGE_ALLOWED_WORKSPACES": "-1",
            # COMPUTE_ENV_CLEANUP
            "# TOWER_COMPUTE_ENV_CLEANUP_NOT_ENABLED": "DO_NOT_UNCOMMENT",
            # AUDIT_LOG_V2
            # v26.2.0+ (test pin `v26.2.0-RC16`): the write mode is removed upstream.
            "# TOWER_AUDIT_LOG_V2_WRITE_MODE": "NOT_AVAILABLE_DO_NOT_UNCOMMENT",
            "TOWER_AUDIT_LOG_V2_CSV_EXPORT_MAX_LOGS": "500000",
            "TOWER_AUDIT_LOG_V2_PRE_POST_CHANGE_ENABLED": "false",
            # CRON_AUDIT_LOG_CLEANUP
            "TOWER_CRON_AUDIT_LOG_CLEAN_UP_ENABLED": "true",
            "TOWER_CRON_AUDIT_LOG_CLEAN_UP_INTERVAL": "5m",
            "TOWER_CRON_AUDIT_LOG_CLEAN_UP_DELAY": "10s",
            "TOWER_CRON_AUDIT_LOG_CLEAN_UP_CHUNK_SIZE": "1000",
            # TELEMETRY (TEMPLATE default: "standard")
            "TOWER_TELEMETRY_STANDARD_ENABLED": "true",
            "TOWER_TELEMETRY_BASIC_ENABLED": "true",
            "TOWER_TELEMETRY_WINDOW_DAYS": "7",
            "LICENSE_SERVER_URL": "https://licenses.seqera.io",
            "# LICENSE_CERTS_AIRGAPPED_BUNDLE": "NOT_ACTIVE_DO_NOT_UNCOMMENT",
            "TOWER_CRON_USAGE_METRICS_FILE_COLLECTOR_ENABLED": "false",
            "TOWER_CRON_USAGE_METRICS_FILE_COLLECTOR_DELAY": "5s",
            "TOWER_CRON_USAGE_METRICS_FILE_COLLECTOR_INTERVAL": "24h",
            "TOWER_CRON_USAGE_METRICS_FILE_COLLECTOR_DIR": "/usage-metrics",
            "TOWER_CRON_USAGE_METRICS_FILE_COLLECTOR_HISTORY": "90",
            # PREFLIGHT CHECKS (off in BASELINE)
            "TOWER_PREFLIGHT_CHECK_ENABLED": "false",
            "TOWER_CREDENTIALS_VALIDATION_ENABLED": "false",
            # PIPELINE SECRETS KMS KEY (unset in BASELINE)
            "# TOWER_AWS_SECRETS_KMS_KEY_ID_NOT_SET": "DO_NOT_UNCOMMENT",
            # ACTIONS (Platform defaults in BASELINE: all triggers on everywhere, 20 per 1h)
            "# TOWER_ACTIONS_BUCKET_TRIGGER_ALL_WORKSPACES": "DO_NOT_UNCOMMENT",
            "# TOWER_ACTIONS_CRON_TRIGGER_ALL_WORKSPACES": "DO_NOT_UNCOMMENT",
            "# TOWER_ACTIONS_PIPELINE_TRIGGER_ALL_WORKSPACES": "DO_NOT_UNCOMMENT",
            "TOWER_ACTIONS_TRIGGER_RATE_MAX_PER_WINDOW": "20",
            "TOWER_ACTIONS_TRIGGER_RATE_WINDOW": "1h",
            # STUDIOS PRIVATE CA (off in BASELINE)
            "# TOWER_SSL_CUSTOM_CA_CERT_FILE_NOT_SET": "DO_NOT_UNCOMMENT",
            # OIDC PROVIDER (off in BASELINE: no Studios, no workload identity federation)
            "# TOWER_OIDC_PEM_PATH_NOT_SET": "DO_NOT_UNCOMMENT",
            # WORKLOAD IDENTITY FEDERATION (v26.2.0+, off in BASELINE)
            "TOWER_IDENTITY_FEDERATION_ALLOWED_WORKSPACES": "-1",
        },
        "omitted": {
            # PIPELINE SECRETS KMS KEY
            "TOWER_AWS_SECRETS_KMS_KEY_ID",
            # TELEMETRY               Wrong doubled names used before the 2026-09-30 fix
            "TOWER_CRON_USAGE_METRICS_FILE_COLLECTOR_FILE_COLLECTOR_ENABLED",
            "TOWER_CRON_USAGE_METRICS_FILE_COLLECTOR_FILE_COLLECTOR_INTERVAL",
            "TOWER_CRON_USAGE_METRICS_FILE_COLLECTOR_FILE_COLLECTOR_DIR",
            "TOWER_CRON_USAGE_METRICS_FILE_COLLECTOR_FILE_COLLECTOR_HISTORY",
            "LICENSE_CERTS_AIRGAPPED_BUNDLE",
            # ACTIONS (allow-lists only written when they restrict)
            "TOWER_ACTIONS_BUCKET_TRIGGER_ALLOWED_WORKSPACES",
            "TOWER_ACTIONS_CRON_TRIGGER_ALLOWED_WORKSPACES",
            "TOWER_ACTIONS_PIPELINE_TRIGGER_ALLOWED_WORKSPACES",
            # STUDIOS PRIVATE CA
            "TOWER_SSL_CUSTOM_CA_CERT_FILE",
            # DB                      Never generated in file
            "TOWER_DB_USER",
            "TOWER_DB_PASSWORD",
            # OIDC
            # MAIL                    Not present if SES active
            "TOWER_SMTP_USER",
            "TOWER_SMTP_PASSWORD",
            # GROUNDSWELL
            "GROUNDSWELL_SERVER_URL",
            # DATA_EXPLORER
            "TOWER_DATA_EXPLORER_CLOUD_DISABLED_WORKSPACES",
            # DATA_STUDIOS
            "TOWER_DATA_STUDIO_ENABLE_PATH_ROUTING",
            "TOWER_DATA_STUDIO_CONNECT_URL",
            "TOWER_OIDC_PEM_PATH",
            "TOWER_OIDC_REGISTRATION_INITIAL_ACCESS_TOKEN",
            # ---
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-12-2_ICON",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-12-2_REPOSITORY",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-12-2_TOOL",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-12-2_STATUS",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-6-0-0-14-0_ICON",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-6-0-0-14-0_REPOSITORY",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-6-0-0-14-0_TOOL",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-6-0-0-14-0_STATUS",
            # ---
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-12-2_ICON",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-12-2_REPOSITORY",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-12-2_TOOL",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-12-2_STATUS",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2026-01-2-0-14-0_ICON",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2026-01-2-0-14-0_REPOSITORY",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2026-01-2-0-14-0_TOOL",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2026-01-2-0-14-0_STATUS",
            # ---
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-12-2_ICON",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-12-2_REPOSITORY",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-12-2_TOOL",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-12-2_STATUS",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-105-1-0-14-0_ICON",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-105-1-0-14-0_REPOSITORY",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-105-1-0-14-0_TOOL",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-105-1-0-14-0_STATUS",
            # ---
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-2-0-R2-1-0-12-2_ICON",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-2-0-R2-1-0-12-2_REPOSITORY",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-2-0-R2-1-0-12-2_TOOL",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-2-0-R2-1-0-12-2_STATUS",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-3-6-R0-1-0-14-0_ICON",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-3-6-R0-1-0-14-0_REPOSITORY",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-3-6-R0-1-0-14-0_TOOL",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-3-6-R0-1-0-14-0_STATUS",
            # ---
            "# TOWER_DATA_STUDIO_ALLOWED_WORKSPACES",
            # DATA_LINEAGE
            "# TOWER_LINEAGE_NOT_ENABLED",
            "TOWER_LINEAGE_STORE_PREFIX",
            "TOWER_LINEAGE_SNS_MAX_RETRIES",
            "TOWER_LINEAGE_SNS_MAX_DELAY_SECONDS",
            "TOWER_LINEAGE_MIGRATE_SQS_TRANSPORT",
            "TOWER_GLOBAL_SEARCH_ENABLED",
            # AUDIT_LOG_V2
            "TOWER_AUDIT_LOG_V2_WRITE_MODE",
            # COMPUTE_ENV_CLEANUP
            "TOWER_COMPUTE_ENV_CLEANUP_ENABLED",
            "TOWER_COMPUTE_ENV_CLEANUP_DELAY",
            "TOWER_COMPUTE_ENV_CLEANUP_INTERVAL",
            "TOWER_COMPUTE_ENV_CLEANUP_BATCH_SIZE",
            "TOWER_COMPUTE_ENV_CLEANUP_TIME_OFFSET",
            "TOWER_COMPUTE_ENV_CLEANUP_STUCK_CREATING_TIMEOUT",
            "TOWER_COMPUTE_ENV_CLEANUP_STUCK_DELETING_TIMEOUT",
        },
    },
    "tower_yml": {
        "present": {
            "mail.smtp.auth": True,
            "mail.smtp.starttls.enable": True,
            "mail.smtp.starttls.required": True,
            "mail.smtp.ssl.protocols": "TLSv1.2",
            "micronaut.application.name": "tower-testing",
            "tower.cron.audit-log.clean-up.time-offset": "1095d",
            "tower.member.auto-create-user": False,
            "tower.participant.auto-create-user": False,
            "tower.trustedEmails[0]": "'graham.wright@seqera.io,gwright99@hotmail.com'",
            "tower.trustedEmails[1]": "'*@abc.com,*@def.com'",
            "tower.trustedEmails[2]": "'123@abc.com,456@def.com'",
            "tower.workflow-cleanup.enabled": False,
        },
        "omitted": {
            "tower.auth",
            "tower.data-studio",
        },
    },
    "data_studios_env": {
        "present": {
            "# STUDIOS_NOT_ENABLED": "DO_NOT_UNCOMMENT",
        },
        "omitted": {
            "PLATFORM_URL",
            "CONNECT_HTTP_PORT",
            "CONNECT_TUNNEL_URL",
            "CONNECT_PROXY_URL",
            "CONNECT_REDIS_ADDRESS",
            "CONNECT_REDIS_DB",
            "CONNECT_OIDC_CLIENT_REGISTRATION_TOKEN",
        },
    },
    "tower_sql": {
        # `payload` is a sentinel: the whole expected file content as a single substring.
        # Consumed by `assert_text_delta`.
        "present": {FileHelper.read_file(f"{expected_sql_dir}/tower.sql")},
        "omitted": set(),
    },
    "docker_compose": {
        "present": {
            # v26.2.0+ (test pin `v26.2.0-RC16`): the default frontend tag is unprivileged, so no suffix.
            "services.frontend.image": "cr.seqera.io/enterprise/platform/frontend:v26.2.0-RC16",
            # Container MySQL 8.4 with db_enforce_tls (template defaults): plaintext clients refused.
            "services.db.image": "mysql:8.4",
            "services.db.command[0]": "--require-secure-transport=ON",
        },
        "omitted": {
            "services.reverseproxy",
            "services.wave-lite",
            "services.wave-lite-reverse-proxy",
            "services.wave-db",
            "services.wave-redis",
            # Air-gapped telemetry only: the cron container's usage-metrics mount.
            "services.cron.volumes[.%usage-metrics]",
            # Studios via private CA only: the rootCA.crt mount in backend and cron.
            "services.backend.volumes[.%rootCA]",
            "services.cron.volumes[.%rootCA]",
            # Studios or workload identity federation only: the OIDC signing key mount.
            "services.backend.volumes[.%data-studios-rsa]",
            "services.cron.volumes[.%data-studios-rsa]",
        },
    },
    "wave_lite_yml": {
        # TODO: Aug 13 — fix Wave-Lite file population so passwords don't end up in file when N/A.
        "present": {
            "wave.server.url": "N/A",
            "wave.db.uri": "N/A",
            "wave.db.user": "wave_lite_test_limited",
            "wave.db.password": "wave_lite_test_limited_password",
            "redis.uri": "N/A",
            "redis.password": "wave_lite_test_redis_password",
            "mail.from": "graham.wright@seqera.io",
            "tower.endpoint.url": "https://autodc.dev-seqera.net/api",
            "license.server.url": "https://licenses.seqera.io",
        },
        "omitted": set(),
    },
    "wave_lite_rds": {
        "present": {FileHelper.read_file(f"{expected_sql_dir}/wave-lite-rds.sql")},
        "omitted": set(),
    },
    "groundswell_env": {
        "present": {
            "SWELL_DB_URL": "N/A",
        },
        "omitted": set(),
    },
    "groundswell_sql": {
        # Whole expected file as one substring (same sentinel pattern as `tower_sql`).
        "present": {FileHelper.read_file(f"{expected_sql_dir}/groundswell.sql")},
        "omitted": set(),
    },
    # TODO: Build out stubs OR identify as not-in-scope due to other testing method.
    "seqerakit_yml": {"present": {}, "omitted": set()},
    "cleanse_and_configure_host": {"present": {}, "omitted": set()},
    "ansible_02_update_file_configurations": {
        "present": set(),
        # Conditional blocks that only appear when the gating features are on.
        # As each feature's `_ON_ASSERTIONS` adds its substring to `present`, the
        # prefix-aware merge clears it from `omitted` automatically.
        "omitted": {
            "Populating external Platform DB.",
            "Populating Wave Lite Postgres.",
            "Populating external DB with Groundswell.",
            "Configuring private certificates.",
            "Creating data directory on host for Studios.",
            "Creating usage-metrics directory on host.",
            "Checking private root CA encoding.",
        },
    },
    "ansible_03_pull_containers_and_run_tower": {"present": {}, "omitted": set()},
    "ansible_05_patch_groundswell": {
        "present": set(),
        # Triggered by container DB x Groundswell. Under BASELINE neither prerequisite is on
        # (Groundswell off); under e.g. `BASELINE + GROUNDSWELL_ACTIVE` both prerequisites are on
        # (container DB is BASELINE default); under `BASELINE + DB_EXTERNAL_* + GROUNDSWELL_ACTIVE`
        # container DB is off and the block doesn't render (cleared inline at those test sites).
        "omitted": {"Patching container db with groundswell init script."},
    },
    "ansible_06_run_seqerakit": {
        "present": {"Seqerakit - Using truststore."},
        # The truststore branch is the "neither hosts file nor insecure HTTP" default;
        # flipping either flag on removes it (per the
        # `!flag_create_hosts_file_entry && !flag_do_not_use_https` gate in the
        # template) and adds the corresponding alternative substring.
        "omitted": {"Seqerakit - Using hosts file.", "Seqerakit - Using insecure."},
    },
    "docker_logging": {"present": {}, "omitted": set()},
    "private_ca_conf": {"present": {}, "omitted": set()},
}


## ------------------------------------------------------------------------------------
## Per-feature delta constants
## ------------------------------------------------------------------------------------


# MARK: DB (New)
# Activates a Terraform-provisioned new RDS instance on top of BASELINE. Universal effect:
# `TOWER_DB_URL` points at the mock new-RDS host. Groundswell-aware and Wave-Lite-aware DB
# paths only differ when those features are also on; declared inline at the test site.
# Unlike existing-DB, Wave-Lite DOES integrate with new-DB (uses the same RDS infra) — see
# `test_new_external_db_with_wave_lite` for the real cross-feature interaction.
DB_EXTERNAL_NEW_ACTIVE_ASSERTIONS = {
    "tower_env": {
        "present": {
            "TOWER_DB_URL": "jdbc:mysql://mock.tower-db.com:3306/tower?useSSL=true&trustServerCertificate=true&permitMysqlScheme=true",
        },
        "omitted": set(),
    },
    "ansible_02_update_file_configurations": {
        "present": {"Populating external Platform DB."},
        "omitted": set(),
    },
    "docker_compose": {"present": {}, "omitted": {"services.db"}},
}


# MARK: DB (Existing)
# Activates an existing external RDS instance instead of the containerised default. When
# enabled on top of BASELINE with `flag_use_existing_external_db = true`, `TOWER_DB_URL`
# points at the supplied `tower_db_url` host. Groundswell-aware DB paths only differ when
# Groundswell is also on; that interaction is declared inline at the test site.
# Wave-Lite does NOT support the existing-DB flow (documented limitation as of Aug 2025) —
# `wave_lite_yml.wave.db.uri` stays at the container DB URL when both are on.
DB_EXTERNAL_EXISTING_ACTIVE_ASSERTIONS = {
    "tower_env": {
        "present": {
            "TOWER_DB_URL": "jdbc:mysql://existing.tower-db.com:3306/tower?useSSL=true&trustServerCertificate=true&permitMysqlScheme=true",
        },
        "omitted": set(),
    },
    "ansible_02_update_file_configurations": {
        "present": {"Populating external Platform DB."},
        "omitted": set(),
    },
    "docker_compose": {"present": {}, "omitted": {"services.db"}},
}


# MARK: Redis (External)
# Activates Elasticache Redis instead of the containerised default. When enabled on top
# of BASELINE with `flag_create_external_redis = true`, `TOWER_REDIS_URL` switches
# to the mock external endpoint. Studios/Wave-Lite-aware Redis paths only differ when
# their own features are also on — those interactions are declared inline at the test
# site as a cross-feature delta passed to `merge_deltas`.
REDIS_EXTERNAL_ACTIVE_ASSERTIONS = {
    "tower_env": {
        "present": {"TOWER_REDIS_URL": "redis://mock.tower-redis.com:6379"},
        "omitted": set(),
    },
}


# OIDC signing key mount in backend and cron, present when Studios or workload identity federation is on.
OIDC_KEY_MOUNT = "$HOME/target/tower_config/data-studios-rsa.pem:/data-studios-rsa.pem"


# MARK: Studios
# Activates Data Studios on top of BASELINE. Brings the entire Studios config online —
# `data_studios_env` populates, `# STUDIOS_NOT_ENABLED` markers flip out, the matrix of
# `TOWER_DATA_STUDIO_TEMPLATES_*` entries appears in `tower_env`, and `tower.data-studio.*`
# becomes a real sub-tree in `tower_yml`.
STUDIOS_ACTIVE_ASSERTIONS = {
    "tower_env": {
        "present": {
            "TOWER_DATA_STUDIO_ENABLE_PATH_ROUTING": "false",
            "TOWER_DATA_STUDIO_CONNECT_URL": "https://connect.autodc.dev-seqera.net",
            "TOWER_OIDC_PEM_PATH": "/data-studios-rsa.pem",
            # random_password.oidc_registration_token, stubbed in tests/utils/terraform/precompute.py.
            "TOWER_OIDC_REGISTRATION_INITIAL_ACCESS_TOKEN": "mockoidcregistrationtoken",
            "TOWER_DATA_STUDIO_DEFAULT_LIFESPAN": "8",
            "TOWER_DATA_STUDIO_PRIVATE_STUDIO_BY_DEFAULT": "false",
            # Templates: JUPYTER
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-6-0-0-14-0_ICON": "jupyter",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-6-0-0-14-0_REPOSITORY": "public.cr.seqera.io/platform/data-studio-jupyter:4.6.0-0.14.0",  # noqa: E501
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-6-0-0-14-0_TOOL": "jupyter",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-6-0-0-14-0_STATUS": "recommended",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-12-2_ICON": "jupyter",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-12-2_REPOSITORY": "public.cr.seqera.io/platform/data-studio-jupyter:4.2.5-0.12.2",  # noqa: E501
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-12-2_TOOL": "jupyter",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-12-2_STATUS": "deprecated",
            # Templates: RIDE (RStudio)
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2026-01-2-0-14-0_ICON": "rstudio",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2026-01-2-0-14-0_REPOSITORY": "public.cr.seqera.io/platform/data-studio-ride:2026.01.2-0.14.0",  # noqa: E501
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2026-01-2-0-14-0_TOOL": "rstudio",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2026-01-2-0-14-0_STATUS": "recommended",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-12-2_ICON": "rstudio",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-12-2_REPOSITORY": "public.cr.seqera.io/platform/data-studio-ride:2025.04.1-0.12.2",  # noqa: E501
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-12-2_TOOL": "rstudio",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-12-2_STATUS": "deprecated",
            # Templates: VSCODE
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-105-1-0-14-0_ICON": "vscode",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-105-1-0-14-0_REPOSITORY": "public.cr.seqera.io/platform/data-studio-vscode:1.105.1-0.14.0",  # noqa: E501
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-105-1-0-14-0_TOOL": "vscode",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-105-1-0-14-0_STATUS": "recommended",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-12-2_ICON": "vscode",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-12-2_REPOSITORY": "public.cr.seqera.io/platform/data-studio-vscode:1.101.2-0.12.2",  # noqa: E501
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-12-2_TOOL": "vscode",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-12-2_STATUS": "deprecated",
            # Templates: XPRA
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-3-6-R0-1-0-14-0_ICON": "xpra",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-3-6-R0-1-0-14-0_REPOSITORY": "public.cr.seqera.io/platform/data-studio-xpra:6.3.6-r0-1-0.14.0",  # noqa: E501
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-3-6-R0-1-0-14-0_TOOL": "xpra",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-3-6-R0-1-0-14-0_STATUS": "recommended",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-2-0-R2-1-0-12-2_ICON": "xpra",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-2-0-R2-1-0-12-2_REPOSITORY": "public.cr.seqera.io/platform/data-studio-xpra:6.2.0-r2-1-0.12.2",  # noqa: E501
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-2-0-R2-1-0-12-2_TOOL": "xpra",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-2-0-R2-1-0-12-2_STATUS": "deprecated",
            "# TOWER_DATA_STUDIO_ALLOWED_WORKSPACES": "DO_NOT_UNCOMMENT",
            # Optional v26.1 vars — renders commented marker when set to empty string (the default).
            "# TOWER_STUDIO_METRICS_ENABLED_WORKSPACES_NOT_SET": "DO_NOT_UNCOMMENT",
        },
        "omitted": {
            "# STUDIOS_NOT_ENABLED",
            # SSH off by default — explicit assertion that these keys aren't rendered.
            # `STUDIOS_SSH_ACTIVE_ASSERTIONS` transitions them into `present` via the
            # prefix-aware merge.
            "TOWER_SSH_KEYS_MANAGEMENT_ENABLED",
            "TOWER_DATA_STUDIO_CONNECT_SSH_PORT",
            "TOWER_DATA_STUDIO_CONNECT_SSH_ADDRESS",
            # Active var names are absent — only the _NOT_SET markers render (see present above).
            "TOWER_STUDIO_METRICS_ENABLED_WORKSPACES",
            # iframe and SSH key type vars not exposed by installer — omitted entirely (see Design Decision #21).
            "TOWER_DATA_STUDIO_CONNECT_IFRAME_ALLOWED_WORKSPACES",
            "# TOWER_DATA_STUDIO_CONNECT_IFRAME_ALLOWED_WORKSPACES_NOT_SET",
            # Studios turns the OIDC provider on.
            "# TOWER_OIDC_PEM_PATH_NOT_SET",
            # Wave Studios vars — only emitted when flag_use_wave=true.
            "TOWER_DATA_STUDIO_WAVE_DISALLOWED_REGISTRIES",
            # Vars not exposed by installer — omitted entirely (see Design Decision #21).
            "TOWER_DATA_STUDIO_LIST_MAX_ALLOWED",
            "TOWER_DATA_STUDIO_FEATURE_MANIFEST_URL",
            "# TOWER_DATA_STUDIO_FEATURE_MANIFEST_URL_NOT_SET",
            "TOWER_STUDIO_METRICS_RETENTION_DAYS",
            "TOWER_DATA_STUDIO_WAVE_CUSTOM_IMAGE_NAME_STRATEGY",
            "TOWER_DATA_STUDIO_WAVE_STATUS_CHECK_INITIAL_DELAY",
            "TOWER_DATA_STUDIO_WAVE_STATUS_CHECK_RATE",
        },
    },
    "data_studios_env": {
        "present": {
            "PLATFORM_URL": "https://autodc.dev-seqera.net",
            "CONNECT_HTTP_PORT": 9090,
            "CONNECT_TUNNEL_URL": "connect-server:7070",
            "CONNECT_PROXY_URL": "https://connect.autodc.dev-seqera.net",
            # Optional server config — renders commented marker when empty (the default).
            "# CONNECT_MANAGEMENT_PORT_NOT_SET": "DO_NOT_UNCOMMENT",
            "CONNECT_REDIS_ADDRESS": "redis:6379",
            "CONNECT_REDIS_DB": 1,
            "CONNECT_OIDC_CLIENT_REGISTRATION_TOKEN": "mockoidcregistrationtoken",
            "CONNECT_LOG_LEVEL": "debug",
        },
        "omitted": {
            "# STUDIOS_NOT_ENABLED",
            # SSH off by default.
            "CONNECT_SSH_ENABLED",
            "CONNECT_SSH_ADDR",
            "CONNECT_SSH_KEY_PATH",
            # Active var names absent when NOT_SET markers render.
            "CONNECT_MANAGEMENT_PORT",
            "CONNECT_MANAGEMENT_AUTH_KEY",
            # Auth key NOT_SET marker only renders when port is set (nested block).
            "# CONNECT_MANAGEMENT_AUTH_KEY_NOT_SET",
            # Vars not exposed by installer — omitted entirely.
            "CONNECT_HOST_DOMAIN",
            "CONNECT_REDIS_PREFIX",
            "CONNECT_CLIENT_NAME",
            "CONNECT_GRANT_TYPE",
            "CONNECT_SSH_MAX_CONNECTIONS",
            "CONNECT_SSH_MAX_CONN_CHANNELS",
            "CONNECT_SSH_HANDSHAKE_TIMEOUT",
        },
    },
    "tower_yml": {
        # Specific sub-key from the `tower.data-studio` sub-tree — its mere presence
        # clears the parent `tower.data-studio` from OFF's omitted via prefix-aware merge.
        "present": {"tower.data-studio.allowed-workspaces": None},
        "omitted": set(),
    },
    "ansible_02_update_file_configurations": {
        "present": {"Creating data directory on host for Studios."},
        "omitted": set(),
    },
    "docker_compose": {
        "present": {
            "services.backend.volumes[.%data-studios-rsa]": OIDC_KEY_MOUNT,
            "services.cron.volumes[.%data-studios-rsa]": OIDC_KEY_MOUNT,
        },
        "omitted": set(),
    },
}


# MARK: Studios Path Routing
# Sub-feature of Studios — requires `STUDIOS_ACTIVE` to be stacked first. Flips Studios's
# path-routing flag on and replaces the default Connect URL with the supplied custom URL.
# When merged on top of `STUDIOS_ACTIVE_ASSERTIONS` via `merge_deltas`, the three URL/flag
# keys get overridden; the rest of Studios's footprint (templates matrix, data_studios_env
# defaults) flows through unchanged.
STUDIOS_PATH_ROUTING_ACTIVE_ASSERTIONS = {
    "tower_env": {
        "present": {
            "TOWER_DATA_STUDIO_ENABLE_PATH_ROUTING": "true",
            "TOWER_DATA_STUDIO_CONNECT_URL": "https://connect-example.com",
        },
        "omitted": set(),
    },
    "data_studios_env": {
        "present": {"CONNECT_PROXY_URL": "https://connect-example.com"},
        "omitted": set(),
    },
}


# MARK: Studios SSH
# Sub-feature of Studios — requires `STUDIOS_ACTIVE` to be stacked first. Brings the SSH
# stanza online: 5 keys appear in `tower_env`, 3 in `data_studios_env`. The SSH-off
# defaults declared in `STUDIOS_ACTIVE_ASSERTIONS.omitted` get transitioned into `present`
# via the prefix-aware merge. Workspace restriction stays off by default
# (`TOWER_DATA_STUDIO_SSH_ALLOWED_WORKSPACES = ""`); turn it on with
# `STUDIOS_SSH_WORKSPACE_RESTRICTION_ACTIVE_ASSERTIONS`.
STUDIOS_SSH_ACTIVE_ASSERTIONS = {
    "tower_env": {
        "present": {
            "TOWER_SSH_KEYS_MANAGEMENT_ENABLED": "true",
            "CONNECT_SSH_ENABLED": "true",
            "TOWER_DATA_STUDIO_CONNECT_SSH_PORT": "2222",
            "TOWER_DATA_STUDIO_SSH_ALLOWED_WORKSPACES": "",
            "TOWER_DATA_STUDIO_CONNECT_SSH_ADDRESS": "https://connect-ssh.autodc.dev-seqera.net",
            "TOWER_SSH_KEYS_SUPPORTED_TYPES": "ssh-rsa,ssh-ed25519,ecdsa-sha2-nistp256,ecdsa-sha2-nistp384,ecdsa-sha2-nistp521",  # noqa: E501
        },
        "omitted": set(),
    },
    "data_studios_env": {
        "present": {
            "CONNECT_SSH_ENABLED": "true",
            "CONNECT_SSH_ADDR": ":2222",
            "CONNECT_SSH_KEY_PATH": "/data/ssh-host-key",
        },
        "omitted": {
            # Not exposed by installer — see Design Decision #20.
            "CONNECT_SSH_KEY_VALUE_BASE64",
            "# CONNECT_SSH_KEY_VALUE_BASE64_NOT_SET",
        },
    },
}


# MARK: Studios Wave integration
# Sub-feature of Studios — requires both `STUDIOS_ACTIVE` and `WAVE_SEQERA_HOSTED_ACTIVE`
# stacked first. Adds the DATA STUDIO - WAVE INTEGRATION block to `tower_env`, which is
# only rendered when both `flag_enable_data_studio` and `flag_use_wave` are true.
STUDIOS_WAVE_ACTIVE_ASSERTIONS = {
    "tower_env": {
        "present": {
            "TOWER_DATA_STUDIO_WAVE_DISALLOWED_REGISTRIES": "community.wave.seqera.io",
            # Custom registry/repo renders commented marker when set to empty string (the default).
            "# TOWER_DATA_STUDIO_WAVE_CUSTOM_IMAGE_REGISTRY_NOT_SET": "DO_NOT_UNCOMMENT",
            "# TOWER_DATA_STUDIO_WAVE_CUSTOM_IMAGE_REPOSITORY_NOT_SET": "DO_NOT_UNCOMMENT",
        },
        "omitted": {
            # Active var names are absent — only the _NOT_SET markers render (see present above).
            "TOWER_DATA_STUDIO_WAVE_CUSTOM_IMAGE_REGISTRY",
            "TOWER_DATA_STUDIO_WAVE_CUSTOM_IMAGE_REPOSITORY",
            # Vars not exposed by installer — omitted entirely (see Design Decision #21).
            "TOWER_DATA_STUDIO_WAVE_CUSTOM_IMAGE_NAME_STRATEGY",
            "TOWER_DATA_STUDIO_WAVE_STATUS_CHECK_INITIAL_DELAY",
            "TOWER_DATA_STUDIO_WAVE_STATUS_CHECK_RATE",
        },
    },
}


# MARK: Studios SSH Workspace Restriction
# Sub-feature of Studios SSH — requires both `STUDIOS_ACTIVE` and `STUDIOS_SSH_ACTIVE` stacked
# first. Replaces SSH's empty workspace allowlist with the supplied CSV.
STUDIOS_SSH_WORKSPACE_RESTRICTION_ACTIVE_ASSERTIONS = {
    "tower_env": {
        "present": {"TOWER_DATA_STUDIO_SSH_ALLOWED_WORKSPACES": "12,34"},
        "omitted": set(),
    },
}


# MARK: Wave (Hosted)
# Activates Seqera-hosted Wave (the SaaS endpoint, NOT Wave Lite). When enabled on top
# of BASELINE with `flag_use_wave = true` and `wave_server_url = "wave.seqera.io"`,
# the Tower and Wave-Lite configs both pick up the public Wave URL.
WAVE_SEQERA_HOSTED_ACTIVE_ASSERTIONS = {
    "tower_env": {
        "present": {
            "TOWER_ENABLE_WAVE": "true",
            "WAVE_SERVER_URL": "https://wave.seqera.io",
        },
        "omitted": set(),
    },
    "wave_lite_yml": {
        "present": {
            "wave.server.url": "https://wave.seqera.io",
        },
        "omitted": set(),
    },
}


# MARK: Wave-Lite
# Activates the self-hosted Wave-Lite stack on top of BASELINE. Brings the four
# Wave-Lite containers into `docker_compose` and populates `wave_lite_yml`'s redis/db/wave
# URLs (vs the `N/A` defaults the OFF baseline asserts when Wave-Lite is off). Also flips
# `TOWER_ENABLE_WAVE` true and points `WAVE_SERVER_URL` at the local Wave-Lite endpoint
# (the same env vars Seqera-hosted Wave uses — Tower treats them generically).
WAVE_LITE_ACTIVE_ASSERTIONS = {
    "tower_env": {
        "present": {
            "TOWER_ENABLE_WAVE": "true",
            "WAVE_SERVER_URL": "https://wave.autodc.dev-seqera.net",
        },
        "omitted": set(),
    },
    "wave_lite_yml": {
        "present": {
            "wave.server.url": "https://wave.autodc.dev-seqera.net",
            "wave.db.uri": "jdbc:postgresql://wave-db:5432/wave",
            "redis.uri": "redis://wave-redis:6379",
        },
        "omitted": set(),
    },
    "docker_compose": {
        # Each `services.<name>.labels.seqera` clears the matching parent path
        # (`services.<name>`) from OFF's omitted via prefix-aware merge.
        "present": {
            "services.wave-lite.labels.seqera": "wave-lite",
            "services.wave-lite.image": "cr.seqera.io/enterprise/wave/server:v1.38.0",
            "services.wave-lite-reverse-proxy.labels.seqera": "wave-lite-reverse-proxy",
            "services.wave-db.labels.seqera": "wave-db",
            "services.wave-redis.labels.seqera": "wave-redis",
        },
        "omitted": set(),
    },
    # NOTE: "Populating Wave Lite Postgres." in ansible_02 is gated by
    # `flag_use_wave_lite && populate_external_db`, so it only renders when an external
    # DB is also active. That substring lives on the cross-feature deltas
    # (DB_EXTERNAL_NEW_X_WAVE_LITE_DELTA / DB_EXTERNAL_EXISTING_X_WAVE_LITE_DELTA), not
    # here.
}


# MARK: Groundswell
# Activates Groundswell on top of BASELINE. Flips `TOWER_ENABLE_GROUNDSWELL` to true,
# adds the in-cluster `GROUNDSWELL_SERVER_URL`, and populates `groundswell_env` with
# the DB / SWELL connection strings (assuming container DB per the convention).
GROUNDSWELL_ACTIVE_ASSERTIONS = {
    "tower_env": {
        "present": {
            "TOWER_ENABLE_GROUNDSWELL": "true",
            "GROUNDSWELL_SERVER_URL": "http://groundswell:8090",
        },
        "omitted": set(),
    },
    "groundswell_env": {
        "present": {
            "TOWER_DB_URL": "jdbc:mysql://db:3306/tower?useSSL=true&trustServerCertificate=true&permitMysqlScheme=true",
            "TOWER_DB_USER": "tower_test_user",
            "TOWER_DB_PASSWORD": "tower_test_password",
            "SWELL_DB_URL": "mysql://db:3306/swell",
            "SWELL_DB_USER": "swell_test_user",
            "SWELL_DB_PASSWORD": "swell_test_password",
        },
        "omitted": set(),
    },
    "ansible_05_patch_groundswell": {
        # Assumes containerised default DB (per convention). When `DB_EXTERNAL_*_ON` is
        # also stacked, container DB is off and this block doesn't render — cleared
        # inline at those test sites via cross-feature delta.
        "present": {"Patching container db with groundswell init script."},
        "omitted": set(),
    },
}


# MARK: Data Explorer
# Activates Tower's Data Explorer feature on top of BASELINE. Flips
# `TOWER_DATA_EXPLORER_ENABLED` to true and surfaces
# `TOWER_DATA_EXPLORER_CLOUD_DISABLED_WORKSPACES` (empty string = no workspace restrictions).
DATA_EXPLORER_ACTIVE_ASSERTIONS = {
    "tower_env": {
        "present": {
            "TOWER_DATA_EXPLORER_ENABLED": "true",
            "TOWER_DATA_EXPLORER_CLOUD_DISABLED_WORKSPACES": "",
        },
        "omitted": set(),
    },
}


# MARK: AWS SES (IAM-based)
# Switches Tower from container SMTP to AWS SES (IAM-authenticated). Two complementary
# tfvars: SES on, existing-SMTP off. Tower_env-only feature — flips `TOWER_ENABLE_AWS_SES`
# true and removes the SMTP host/port keys (TOWER_SMTP_USER/PASSWORD stay absent from
# BASELINE regardless of SES state).
AWS_SES_ACTIVE_ASSERTIONS = {
    "tower_env": {
        "present": {"TOWER_ENABLE_AWS_SES": "true"},
        "omitted": {"TOWER_SMTP_HOST", "TOWER_SMTP_PORT"},
    },
}


# MARK: Tower Opt-In Flags (bundled Tower-side config knobs)
# Six Tower-level config flags grouped together for compactness — they're independent
# knobs that all happen to live in tower_env and tower_yml. If any one of them grows
# complex enough (e.g., pipeline versioning gaining a workspace-restriction sub-feature
# similar to Studios SSH), break it out into its own `<FEATURE>_ON` constant + test.
TOWER_OPT_IN_FLAGS_ACTIVE_ASSERTIONS = {
    "tower_env": {
        "present": {
            "TOWER_ALLOW_INSTANCE_CREDENTIALS": "true",
            "TOWER_ENABLE_OPENAPI": "true",
            "TOWER_PREFLIGHT_CHECK_ENABLED": "true",
            "TOWER_CREDENTIALS_VALIDATION_ENABLED": "true",
            "TOWER_ACTIONS_BUCKET_TRIGGER_ALLOWED_WORKSPACES": "-1",
            "TOWER_ACTIONS_CRON_TRIGGER_ALLOWED_WORKSPACES": "12,34",
            "TOWER_ACTIONS_PIPELINE_TRIGGER_ALLOWED_WORKSPACES": "56",
            "TOWER_ACTIONS_TRIGGER_RATE_MAX_PER_WINDOW": "50",
            "TOWER_ACTIONS_TRIGGER_RATE_WINDOW": "2h",
            "TOWER_AWS_SECRETS_KMS_KEY_ID": "arn:aws:kms:us-east-1:123456789012:key/1234abcd-12ab-34cd-56ef-1234567890ab",  # noqa: E501
            "TOWER_PIPELINE_VERSIONING_ALLOWED_WORKSPACES": "",
        },
        "omitted": {
            "# TOWER_PIPELINE_VERSIONING_NOT_ENABLED",
            "# TOWER_AWS_SECRETS_KMS_KEY_ID_NOT_SET",
            "# TOWER_ACTIONS_BUCKET_TRIGGER_ALL_WORKSPACES",
            "# TOWER_ACTIONS_CRON_TRIGGER_ALL_WORKSPACES",
            "# TOWER_ACTIONS_PIPELINE_TRIGGER_ALL_WORKSPACES",
        },
    },
    "tower_yml": {
        "present": {
            "tower.member.auto-create-user": True,
            "tower.participant.auto-create-user": True,
            "tower.workflow-cleanup.enabled": True,
        },
        "omitted": set(),
    },
}


# MARK: Private CA Reverse Proxy
# Activates a self-hosted reverseproxy + private CA cert as the TLS termination point,
# in lieu of an ALB. Three tfvars together describe a deployment topology, not three
# independent features. Brings up the `services.reverseproxy` container in docker_compose;
# `services.reverseproxy` is cleared from BASELINE.omitted via the prefix-aware merge.
PRIVATE_CA_REVERSE_PROXY_ACTIVE_ASSERTIONS = {
    "docker_compose": {
        "present": {"services.reverseproxy.labels.seqera": "reverseproxy"},
        "omitted": set(),
    },
    "ansible_02_update_file_configurations": {
        "present": {"Configuring private certificates."},
        "omitted": set(),
    },
}


# MARK: Seqerakit — Hosts File Entry
# Activates the hosts-file branch of ansible_06. Triggered by
# `flag_create_hosts_file_entry`; replaces BASELINE's truststore branch with the
# hosts-file substring (the truststore branch is gated by
# `!flag_create_hosts_file_entry && !flag_do_not_use_https`, so either flag flipping
# on removes it).
HOSTS_FILE_ENTRY_ACTIVE_ASSERTIONS = {
    "ansible_06_run_seqerakit": {
        "present": {"Seqerakit - Using hosts file."},
        "omitted": {"Seqerakit - Using truststore."},
    },
}


# MARK: Seqerakit — Insecure HTTP
# Activates insecure-HTTP mode platform-wide. Triggered by `flag_do_not_use_https`,
# which has effects beyond ansible_06:
#   - `tower_env.TOWER_SERVER_URL` flips from `https://...` to `http://...:8000`
#     (the explicit `:8000` port is added in insecure mode).
#   - `tower_env.TOWER_ENABLE_UNSAFE_MODE` flips from `false` to `true`.
#   - ansible_06 swaps the truststore substring for the insecure substring (gated by
#     `!flag_create_hosts_file_entry && !flag_do_not_use_https`).
# Studios and Wave-Lite are also force-disabled under insecure mode, but BASELINE has
# both off already so no extra delta is needed here. If a future test stacks
# `INSECURE_HTTP_ACTIVE` with `STUDIOS_ACTIVE` or `WAVE_LITE_ACTIVE`, a cross-feature delta will
# be required (Studios → disabled, Wave-Lite → disabled).
INSECURE_HTTP_ACTIVE_ASSERTIONS = {
    "tower_env": {
        "present": {
            "TOWER_SERVER_URL": "http://autodc.dev-seqera.net:8000",
            "TOWER_ENABLE_UNSAFE_MODE": "true",
        },
        "omitted": set(),
    },
    # `wave_lite_yml` is rendered even when Wave-Lite is off; `tower.endpoint.url`
    # derives from `tower_server_url` and inherits the insecure scheme + port.
    "wave_lite_yml": {
        "present": {"tower.endpoint.url": "http://autodc.dev-seqera.net:8000/api"},
        "omitted": set(),
    },
    "ansible_06_run_seqerakit": {
        "present": {"Seqerakit - Using insecure."},
        "omitted": {"Seqerakit - Using truststore."},
    },
}


# MARK: Data Lineage
# Activates Nextflow data lineage. On v26.2.0+ the off-state renders `-1`; activation
# swaps it for the empty allowlist (all workspaces) and adds the v26.2 keys. Workspace
# restriction is a separate constant (see below) that overrides the empty allowlist
# with a specific CSV.
DATA_LINEAGE_ACTIVE_ASSERTIONS = {
    "tower_env": {
        "present": {
            "TOWER_LINEAGE_ALLOWED_WORKSPACES": "",
            "TOWER_LINEAGE_STORE_PREFIX": "seqera-lineage",
            "TOWER_LINEAGE_SNS_MAX_RETRIES": "17",
            "TOWER_LINEAGE_SNS_MAX_DELAY_SECONDS": "300",
            "TOWER_LINEAGE_MIGRATE_SQS_TRANSPORT": "true",
            "TOWER_GLOBAL_SEARCH_ENABLED": "true",
        },
        "omitted": set(),
    },
}


# Platform < v26.2.0 with lineage on: only the allowlist renders. Stack after
# `FRONTEND_PRE_26_2_ACTIVE_ASSERTIONS` and `DATA_LINEAGE_ACTIVE_ASSERTIONS`.
DATA_LINEAGE_X_PRE_26_2_DELTA = {
    "tower_env": {
        "present": {},
        "omitted": {
            "# TOWER_LINEAGE_NOT_ENABLED",
            "TOWER_LINEAGE_STORE_PREFIX",
            "TOWER_LINEAGE_SNS_MAX_RETRIES",
            "TOWER_LINEAGE_SNS_MAX_DELAY_SECONDS",
            "TOWER_LINEAGE_MIGRATE_SQS_TRANSPORT",
            "TOWER_GLOBAL_SEARCH_ENABLED",
        },
    },
}


# MARK: Data Lineage Workspace Restriction
# Sub-feature of Data Lineage — requires `DATA_LINEAGE_ACTIVE` stacked first.
# Replaces the empty workspace allowlist with the supplied CSV.
DATA_LINEAGE_WORKSPACE_RESTRICTION_ACTIVE_ASSERTIONS = {
    "tower_env": {
        "present": {"TOWER_LINEAGE_ALLOWED_WORKSPACES": "12,34"},
        "omitted": set(),
    },
}


# MARK: Compute Environment Cleanup
COMPUTE_ENV_CLEANUP_ACTIVE_ASSERTIONS = {
    "tower_env": {
        "present": {
            "TOWER_COMPUTE_ENV_CLEANUP_ENABLED": "true",
            "TOWER_COMPUTE_ENV_CLEANUP_DELAY": "1m",
            "TOWER_COMPUTE_ENV_CLEANUP_INTERVAL": "1h",
            "TOWER_COMPUTE_ENV_CLEANUP_BATCH_SIZE": "10",
            "TOWER_COMPUTE_ENV_CLEANUP_TIME_OFFSET": "60s",
            "TOWER_COMPUTE_ENV_CLEANUP_STUCK_CREATING_TIMEOUT": "1h",
            "TOWER_COMPUTE_ENV_CLEANUP_STUCK_DELETING_TIMEOUT": "1h",
        },
        "omitted": {"# TOWER_COMPUTE_ENV_CLEANUP_NOT_ENABLED"},
    },
}


# MARK: Audit Log v2 Cleanup Disabled
# Overrides only the `cleanup.enabled` sub-field of `tower_audit_log_v2`. The other
# audit-log-v2 settings (write_mode, csv_export_max_logs, pre_post_change_enabled)
# fall through to their `optional()` defaults — identical to BASELINE. The cleanup
# block in tower.env.tpl wraps the four cron-sub vars in `%{ if cleanup.enabled }`,
# so disabling cleanup emits TOWER_CRON_AUDIT_LOG_CLEAN_UP_ENABLED=false and skips
# the interval/delay/chunk_size lines entirely.
AUDIT_LOG_V2_CLEANUP_DISABLED_ACTIVE_ASSERTIONS = {
    "tower_env": {
        "present": {
            "TOWER_CRON_AUDIT_LOG_CLEAN_UP_ENABLED": "false",
        },
        "omitted": {
            "TOWER_CRON_AUDIT_LOG_CLEAN_UP_INTERVAL",
            "TOWER_CRON_AUDIT_LOG_CLEAN_UP_DELAY",
            "TOWER_CRON_AUDIT_LOG_CLEAN_UP_CHUNK_SIZE",
        },
    },
}


# Platform < v26.2.0: the unprivileged frontend ships as a separate `-unprivileged` tag
# (see `local.frontend_image_suffix` in 000_main.tf). Lineage off renders the comment
# marker instead of `-1`.
FRONTEND_PRE_26_2_ACTIVE_ASSERTIONS = {
    "docker_compose": {
        "present": {
            "services.frontend.image": "cr.seqera.io/enterprise/platform/frontend:v26.1.3-unprivileged",
        },
        "omitted": set(),
    },
    "tower_env": {
        "present": {
            "# TOWER_LINEAGE_NOT_ENABLED": "DO_NOT_UNCOMMENT",
            "TOWER_AUDIT_LOG_V2_WRITE_MODE": "dual",
        },
        "omitted": {
            "TOWER_LINEAGE_ALLOWED_WORKSPACES",
            "# TOWER_AUDIT_LOG_V2_WRITE_MODE",
            "TOWER_IDENTITY_FEDERATION_ALLOWED_WORKSPACES",
        },
    },
}


# MARK: Workload Identity Federation
# v26.2.0+ with Studios off: enabling federation turns the OIDC provider on (signing key path and mount)
# and replaces the `-1` off value with the allow-list (empty = all workspaces).
IDENTITY_FEDERATION_ACTIVE_ASSERTIONS = {
    "tower_env": {
        "present": {
            "TOWER_OIDC_PEM_PATH": "/data-studios-rsa.pem",
            "TOWER_IDENTITY_FEDERATION_ALLOWED_WORKSPACES": "",
        },
        "omitted": {"# TOWER_OIDC_PEM_PATH_NOT_SET"},
    },
    "docker_compose": {
        "present": {
            "services.backend.volumes[.%data-studios-rsa]": OIDC_KEY_MOUNT,
            "services.cron.volumes[.%data-studios-rsa]": OIDC_KEY_MOUNT,
        },
        "omitted": set(),
    },
}


# Sub-feature of Workload Identity Federation — requires `IDENTITY_FEDERATION_ACTIVE` stacked first.
IDENTITY_FEDERATION_WORKSPACE_RESTRICTION_ACTIVE_ASSERTIONS = {
    "tower_env": {
        "present": {"TOWER_IDENTITY_FEDERATION_ALLOWED_WORKSPACES": "12,34"},
        "omitted": set(),
    },
}


# MARK: Database TLS (Design Decision 25)
# TLS is off: Platform uses the plaintext JDBC suffix, and the container DB accepts plaintext.
# `DB_8_0_ACTIVE_ASSERTIONS` adds the 8.0 image; on 8.0, TLS stays off even with db_enforce_tls = true.
DB_TLS_OFF_ASSERTIONS = {
    "tower_env": {
        "present": {
            "TOWER_DB_URL": "jdbc:mysql://db:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true",
        },
        "omitted": set(),
    },
    "docker_compose": {
        "present": {},
        # Both keys: the merge doesn't treat `[0]` as a child of `services.db.command`.
        "omitted": {"services.db.command", "services.db.command[0]"},
    },
}

DB_8_0_ACTIVE_ASSERTIONS = {
    "docker_compose": {
        "present": {"services.db.image": "mysql:8.0"},
        "omitted": set(),
    },
}


# Telemetry "basic": standard telemetry off. Basic stays on, and the file collector stays off.
TELEMETRY_BASIC_ACTIVE_ASSERTIONS = {
    "tower_env": {
        "present": {"TOWER_TELEMETRY_STANDARD_ENABLED": "false"},
        "omitted": set(),
    },
}


# Telemetry "air-gapped": standard stays on, basic turns off, and the usage-metrics file collector turns on.
# Ansible (02) creates the host folder, and docker-compose mounts it into cron at /usage-metrics.
TELEMETRY_AIR_GAPPED_ACTIVE_ASSERTIONS = {
    "tower_env": {
        "present": {
            "TOWER_CRON_USAGE_METRICS_FILE_COLLECTOR_ENABLED": "true",
            "TOWER_TELEMETRY_BASIC_ENABLED": "false",
            "LICENSE_SERVER_URL": "",
            "LICENSE_CERTS_AIRGAPPED_BUNDLE": "/etc/seqera/license-bundle.pem",
        },
        "omitted": {"# LICENSE_CERTS_AIRGAPPED_BUNDLE"},
    },
    "docker_compose": {
        "present": {"services.cron.volumes[.%usage-metrics]": "$HOME/.tower/usage-metrics:/usage-metrics"},
        "omitted": set(),
    },
    "ansible_02_update_file_configurations": {
        "present": {"Creating usage-metrics directory on host."},
        "omitted": set(),
    },
}


# Telemetry options: non-default values reach tower.env, so they are not hard-coded in the template.
TELEMETRY_OPTIONS_CUSTOM_ACTIVE_ASSERTIONS = {
    "tower_env": {
        "present": {
            "TOWER_TELEMETRY_WINDOW_DAYS": "30",
            "TOWER_CRON_USAGE_METRICS_FILE_COLLECTOR_DELAY": "10m",
        },
        "omitted": set(),
    },
}


# Studios via private CA: sub-feature of the private CA. Stack on PRIVATE_CA_REVERSE_PROXY_ACTIVE
# (+ STUDIOS_ACTIVE). The mount, the tower.env variable, and the Ansible PEM check all follow
# `local.studios_private_ca_active` in 000_main.tf, so they render together or not at all.
STUDIOS_PRIVATE_CA_ACTIVE_ASSERTIONS = {
    "tower_env": {
        "present": {"TOWER_SSL_CUSTOM_CA_CERT_FILE": "/private-ca/rootCA.crt"},
        "omitted": {"# TOWER_SSL_CUSTOM_CA_CERT_FILE_NOT_SET"},
    },
    "docker_compose": {
        "present": {
            "services.backend.volumes[.%rootCA]": "/etc/pki/ca-trust/source/anchors/rootCA.crt:/private-ca/rootCA.crt:ro",  # noqa: E501
            "services.cron.volumes[.%rootCA]": "/etc/pki/ca-trust/source/anchors/rootCA.crt:/private-ca/rootCA.crt:ro",
        },
        "omitted": set(),
    },
    "ansible_02_update_file_configurations": {
        "present": {"Checking private root CA encoding."},
        "omitted": set(),
    },
}


## ------------------------------------------------------------------------------------
## MARK: Cross-feature deltas
##
## Constants below describe the *additional* deltas that emerge when two features are
## stacked together — effects that aren't part of either feature's standalone
## `_ON_ASSERTIONS` (per the "containerised defaults for unrelated features" convention).
##
## **Only meaningful when BOTH component features are stacked.** Using a cross-feature
## delta without its two component `_ON_ASSERTIONS` constants will produce nonsense.
## Naming follows `<FEATURE_A>_X_<FEATURE_B>_DELTA` (alphabetical to keep order
## deterministic) with the `_DELTA` suffix distinguishing these from the tfvars-paired
## `_ON_ASSERTIONS` constants.
## ------------------------------------------------------------------------------------


# When external new-DB is paired with Groundswell, Groundswell's `groundswell_env` URLs
# flip to the new RDS host, and the ansible_05 container-DB patching block doesn't render
# (container DB is off).
DB_EXTERNAL_NEW_X_GROUNDSWELL_DELTA = {
    "groundswell_env": {
        "present": {
            "TOWER_DB_URL": "jdbc:mysql://mock.tower-db.com:3306/tower?useSSL=true&trustServerCertificate=true&permitMysqlScheme=true",
            "SWELL_DB_URL": "mysql://mock.tower-db.com:3306/swell",
        },
    },
    "ansible_02_update_file_configurations": {
        "present": {"Populating external DB with Groundswell."},
    },
    "ansible_05_patch_groundswell": {
        "omitted": {"Patching container db with groundswell init script."},
    },
}


# When existing external-DB is paired with Groundswell, Groundswell's `groundswell_env`
# URLs flip to the existing host, and the ansible_05 container-DB patching block doesn't
# render (container DB is off).
DB_EXTERNAL_EXISTING_X_GROUNDSWELL_DELTA = {
    "groundswell_env": {
        "present": {
            "TOWER_DB_URL": "jdbc:mysql://existing.tower-db.com:3306/tower?useSSL=true&trustServerCertificate=true&permitMysqlScheme=true",
            "SWELL_DB_URL": "mysql://existing.tower-db.com:3306/swell",
        },
    },
    "ansible_02_update_file_configurations": {
        "present": {"Populating external DB with Groundswell."},
    },
    "ansible_05_patch_groundswell": {
        "omitted": {"Patching container db with groundswell init script."},
    },
}


# When external new-DB is paired with Wave-Lite, Wave-Lite uses the new RDS for its
# wave-db, the container wave-db is removed from docker_compose, and ansible_02 renders
# the Wave-Lite Postgres population block (gated by `flag_use_wave_lite &&
# populate_external_db`).
DB_EXTERNAL_NEW_X_WAVE_LITE_DELTA = {
    "wave_lite_yml": {
        "present": {"wave.db.uri": "jdbc:postgresql://mock.wave-db.com:5432/wave"},
    },
    "docker_compose": {"omitted": {"services.wave-db"}},
    "ansible_02_update_file_configurations": {
        "present": {"Populating Wave Lite Postgres."},
    },
}


# When existing external-DB is paired with Wave-Lite, Wave-Lite still uses its container
# wave-db (the existing-DB flag is for Tower's DB, not Wave-Lite's) — so wave_lite_yml
# and docker_compose stay at the Wave-Lite-only values. The only cross-feature effect is
# in ansible_02: the Wave-Lite Postgres population block renders because
# `populate_external_db` is true (gated by either external-DB flag).
DB_EXTERNAL_EXISTING_X_WAVE_LITE_DELTA = {
    "ansible_02_update_file_configurations": {
        "present": {"Populating Wave Lite Postgres."},
    },
}


# When external Redis is paired with Studios, Studios's Redis endpoint flips to the
# external host.
REDIS_EXTERNAL_X_STUDIOS_DELTA = {
    "data_studios_env": {"present": {"CONNECT_REDIS_ADDRESS": "mock.tower-redis.com:6379"}},
}


# When external Redis is paired with Wave-Lite, Wave-Lite's Redis endpoint flips
# (note the `rediss://` TLS scheme) and the container wave-redis service is removed.
REDIS_EXTERNAL_X_WAVE_LITE_DELTA = {
    "wave_lite_yml": {"present": {"redis.uri": "rediss://mock.wave-redis.com:6379"}},
    "docker_compose": {"omitted": {"services.wave-redis"}},
}
