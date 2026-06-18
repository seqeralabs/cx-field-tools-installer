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
"""

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
"""

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
    data_lineage_allowed_workspaces = "12,34"
"""

COMPUTE_ENV_CLEANUP_ACTIVE = """
    tower_compute_env_cleanup = {
      enabled = true
    }
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
            "LICENSE_SERVER_URL": "https://licenses.seqera.io",
            "TOWER_SERVER_URL": "https://autodc.dev-seqera.net",
            "TOWER_CONTACT_EMAIL": "graham.wright@seqera.io",
            "TOWER_ENABLE_PLATFORMS": "awsbatch-platform,slurm-platform",
            "TOWER_ROOT_USERS": "graham.wright@seqera.io,gwright99@hotmail.com",
            "TOWER_DB_URL": "jdbc:mysql://db:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true",
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
            "# TOWER_LINEAGE_NOT_ENABLED": "DO_NOT_UNCOMMENT",
            # COMPUTE_ENV_CLEANUP
            "# TOWER_COMPUTE_ENV_CLEANUP_NOT_ENABLED": "DO_NOT_UNCOMMENT",
        },
        "omitted": {
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
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-11-0_ICON",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-11-0_REPOSITORY",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-11-0_TOOL",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-11-0_STATUS",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-12-1_ICON",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-12-1_REPOSITORY",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-12-1_TOOL",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-12-1_STATUS",
            # ---
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-11-0_ICON",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-11-0_REPOSITORY",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-11-0_TOOL",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-11-0_STATUS",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-12-1_ICON",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-12-1_REPOSITORY",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-12-1_TOOL",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-12-1_STATUS",
            # ---
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-11-0_ICON",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-11-0_REPOSITORY",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-11-0_TOOL",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-11-0_STATUS",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-12-1_ICON",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-12-1_REPOSITORY",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-12-1_TOOL",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-12-1_STATUS",
            # ---
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R2-1-0-11-0_ICON",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R2-1-0-11-0_REPOSITORY",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R2-1-0-11-0_TOOL",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R2-1-0-11-0_STATUS",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-2-0-R2-0-12-1_ICON",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-2-0-R2-0-12-1_REPOSITORY",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-2-0-R2-0-12-1_TOOL",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-2-0-R2-0-12-1_STATUS",
            # ---
            "# TOWER_DATA_STUDIO_ALLOWED_WORKSPACES",
            # DATA_LINEAGE
            "TOWER_LINEAGE_ALLOWED_WORKSPACES",
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
        "present": {},
        "omitted": {
            "services.reverseproxy",
            "services.wave-lite",
            "services.wave-lite-reverse-proxy",
            "services.wave-db",
            "services.wave-redis",
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
    # TODO: Build out stubs OR identify as not-in-scope due to other testing method.
    "groundswell_sql": {"present": {}, "omitted": set()},
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
            "TOWER_DB_URL": "jdbc:mysql://mock.tower-db.com:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true",
        },
        "omitted": set(),
    },
    "ansible_02_update_file_configurations": {
        "present": {"Populating external Platform DB."},
        "omitted": set(),
    },
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
            "TOWER_DB_URL": "jdbc:mysql://existing.tower-db.com:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true",
        },
        "omitted": set(),
    },
    "ansible_02_update_file_configurations": {
        "present": {"Populating external Platform DB."},
        "omitted": set(),
    },
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
            "TOWER_OIDC_REGISTRATION_INITIAL_ACCESS_TOKEN": "ipsemlorem",
            # Templates: JUPYTER
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-12-1_ICON": "jupyter",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-12-1_REPOSITORY": "public.cr.seqera.io/platform/data-studio-jupyter:4.2.5-0.12.1",  # noqa: E501
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-12-1_TOOL": "jupyter",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-12-1_STATUS": "recommended",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-11-0_ICON": "jupyter",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-11-0_REPOSITORY": "public.cr.seqera.io/platform/data-studio-jupyter:4.2.5-0.11.0",  # noqa: E501
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-11-0_TOOL": "jupyter",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-11-0_STATUS": "deprecated",
            # Templates: RIDE (RStudio)
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-12-1_ICON": "rstudio",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-12-1_REPOSITORY": "public.cr.seqera.io/platform/data-studio-ride:2025.04.1-0.12.1",  # noqa: E501
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-12-1_TOOL": "rstudio",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-12-1_STATUS": "recommended",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-11-0_ICON": "rstudio",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-11-0_REPOSITORY": "public.cr.seqera.io/platform/data-studio-ride:2025.04.1-0.11.0",  # noqa: E501
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-11-0_TOOL": "rstudio",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-11-0_STATUS": "deprecated",
            # Templates: VSCODE
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-12-1_ICON": "vscode",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-12-1_REPOSITORY": "public.cr.seqera.io/platform/data-studio-vscode:1.101.2-0.12.1",  # noqa: E501
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-12-1_TOOL": "vscode",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-12-1_STATUS": "recommended",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-11-0_ICON": "vscode",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-11-0_REPOSITORY": "public.cr.seqera.io/platform/data-studio-vscode:1.101.2-0.11.0",  # noqa: E501
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-11-0_TOOL": "vscode",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-11-0_STATUS": "deprecated",
            # Templates: XPRA
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-2-0-R2-1-0-12-1_ICON": "xpra",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-2-0-R2-1-0-12-1_REPOSITORY": "public.cr.seqera.io/platform/data-studio-xpra:6.2.0-r2-1-0.12.1",  # noqa: E501
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-2-0-R2-1-0-12-1_TOOL": "xpra",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-2-0-R2-1-0-12-1_STATUS": "recommended",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-2-0-R2-1-0-11-0_ICON": "xpra",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-2-0-R2-1-0-11-0_REPOSITORY": "public.cr.seqera.io/platform/data-studio-xpra:6.2.0-r2-1-0.11.0",  # noqa: E501
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-2-0-R2-1-0-11-0_TOOL": "xpra",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-2-0-R2-1-0-11-0_STATUS": "deprecated",
            "# TOWER_DATA_STUDIO_ALLOWED_WORKSPACES": "DO_NOT_UNCOMMENT",
        },
        "omitted": {
            "# STUDIOS_NOT_ENABLED",
            # SSH off by default — explicit assertion that these keys aren't rendered.
            # `STUDIOS_SSH_ACTIVE_ASSERTIONS` transitions them into `present` via the
            # prefix-aware merge.
            "TOWER_SSH_KEYS_MANAGEMENT_ENABLED",
            "TOWER_DATA_STUDIO_CONNECT_SSH_PORT",
            "TOWER_DATA_STUDIO_CONNECT_SSH_ADDRESS",
        },
    },
    "data_studios_env": {
        "present": {
            "PLATFORM_URL": "https://autodc.dev-seqera.net",
            "CONNECT_HTTP_PORT": 9090,
            "CONNECT_TUNNEL_URL": "connect-server:7070",
            "CONNECT_PROXY_URL": "https://connect.autodc.dev-seqera.net",
            "CONNECT_REDIS_ADDRESS": "redis:6379",
            "CONNECT_REDIS_DB": 1,
            "CONNECT_OIDC_CLIENT_REGISTRATION_TOKEN": "ipsemlorem",
        },
        "omitted": {
            "# STUDIOS_NOT_ENABLED",
            # SSH off by default — see tower_env note above.
            "CONNECT_SSH_ENABLED",
            "CONNECT_SSH_ADDR",
            "CONNECT_SSH_KEY_PATH",
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
        },
        "omitted": set(),
    },
    "data_studios_env": {
        "present": {
            "CONNECT_SSH_ENABLED": "true",
            "CONNECT_SSH_ADDR": ":2222",
            "CONNECT_SSH_KEY_PATH": "/data/ssh-host-key",
        },
        "omitted": set(),
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
            "services.wave-lite.image": "cr.seqera.io/enterprise/wave/server:v1.33.0",
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
            "TOWER_DB_URL": "jdbc:mysql://db:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true",
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
            "TOWER_PIPELINE_VERSIONING_ALLOWED_WORKSPACES": "",
        },
        "omitted": {"# TOWER_PIPELINE_VERSIONING_NOT_ENABLED"},
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
# Activates Nextflow data lineage. The off-state renders a `# TOWER_LINEAGE_NOT_ENABLED`
# comment marker; activation flips that into a real `TOWER_LINEAGE_ALLOWED_WORKSPACES`
# entry. Workspace restriction is a separate constant (see below) that overrides the
# empty allowlist with a specific CSV.
DATA_LINEAGE_ACTIVE_ASSERTIONS = {
    "tower_env": {
        "present": {
            "TOWER_LINEAGE_ALLOWED_WORKSPACES": "",
        },
        "omitted": {"# TOWER_LINEAGE_NOT_ENABLED"},
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
            "TOWER_DB_URL": "jdbc:mysql://mock.tower-db.com:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true",
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
            "TOWER_DB_URL": "jdbc:mysql://existing.tower-db.com:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true",
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
