# CHANGELOG
> Last updated: Sept 28, 2026

This file was updated as part of the 1.8.0 Release.

```bash
# Example:
$ git log origin/master..origin/gwright99/25_2_0_update --oneline
```


## 1.9.0 (TBD)

- **Notable Changes**
    - **CX Installer**
        - General
            - Enabled SSH `ControlMaster` multiplexing in the rendered SSH config so every `ssh`/`scp` call made by `configure_vm` shares a single tunnel instead of opening a fresh one each. Roughly halves `terraform apply` wall-clock on private (EICE-tunneled) deployments. Sockets live at `<project_root>/.ssh-control/cm-%C` (gitignored) with a 10-minute persist timeout.
            - `ec2-user` is now added to the `docker` group at instance launch via `launch_template_ec2.tpl` (cloud-init). The `ssh_probe` phase now waits for cloud-init to finish (`sudo cloud-init status --wait`, 10-minute timeout; `sudo` because cloud-init 22.x reads a root-only file even for `status`) and then closes the `ControlMaster`, so the SSH session that runs Ansible always has the `docker` group. This avoids the staleness interaction between `ControlMaster` and mid-apply group membership changes that surfaced as `permission denied … /var/run/docker.sock`. An unfinished or failed cloud-init now stops the apply with a clear error. **Existing sites: this is a fresh-deploy fix only.** Running EC2s will not pick up the new user_data without instance replacement (`terraform taint aws_instance.ec2 && terraform apply`); AMI pin is preserved across the replace. In-place workaround: `sudo usermod -aG docker ec2-user` on the host, then `ssh -O exit <host>; rm -f .ssh-control/cm-*` locally (from the project root). **Custom launch templates:** the Ansible tasks that added `ec2-user` to `docker` were removed. If you maintain your own `launch_template_ec2.tpl`, copy in the `groupadd -f docker` / `usermod -aG docker ec2-user` lines, or `ec2-user` will have no docker access.
            - Re-monolithised the VM-configuration pipeline in `011_configure_vm.tf` (issue #410). The previous chain of 10 sequential `null_resource` blocks (`ssh_connectivity_check` → `file_transfer` → 8 mid-pipeline Ansible steps) is now a **single** `null_resource` (`configure_vm`) with three locally-bracketed phases (`ssh_probe` / `file_transfer` / `remote_orchestrator`) and a remote orchestrator (`assets/src/bash/remote/orchestrate.sh`) that runs the 7 Ansible stages on the host. Failure attribution survives via bracketed log markers (`STAGE START` / `STAGE OK` / `STAGE FAILED`) at both layers — search terraform output / on-host log for `STAGE FAILED` to find the failure point. Persistent on-host log at `/home/ec2-user/tower-installer-logs/apply-<UTC>.log`. The `count` gate (`flag_vm_copy_files_to_instance`) lives on `null_resource.allow_file_copy_to_start` in `010_prepare_config_files.tf`; `configure_vm` derives its count via `length(...)`. Net plan output: 1 `null_resource` line per apply instead of 10. **Drift defence is unchanged** — `always_run = timestamp()` triggers a full Ansible reconcile every apply. [`#410`](https://github.com/seqeralabs/cx-field-tools-installer/issues/410)
            - `aws_batch_manual` / `aws_batch_forge` (`010_prepare_config_files.tf`) now also require `flag_run_seqerakit = true`. When Seqerakit is off, the compute-environment block is no longer appended to `setup.yml`. No functional impact: only Seqerakit reads that file.
            - Removed the unused `tower_server_port` variable (no effect since 1.6.0). See `Configuration File Changes`.
            - Cleared all `tflint` warnings: removed 4 unused locals, a duplicate map key in each of 2 templatefile arg maps, and deprecated `"${...}"` wrappers. No behaviour change.
            - Pinned the `null` (`~> 3.0`), `random` (`~> 3.1`), and `tls` (`~> 4.0`) providers to block untested major versions. Existing lock files still satisfy these pins.
            - `tower.sql` and `groundswell.sql` now create the database and user with `IF NOT EXISTS`, so the re-run on every `terraform apply` succeeds. Previously the re-run stopped at the first statement and the error was hidden. [`#434`](https://github.com/seqeralabs/cx-field-tools-installer/issues/434)
            - The DB population steps no longer ignore failures (`|| true` removed in `02_update_file_configurations.yml.tpl` and `05_patch_groundswell.yml.tpl`). **Existing external DB sites:** if the SSM `db-master-user` / `db-master-password` values are placeholders or lack privileges, `terraform apply` now fails at this step instead of skipping it silently. [`#434`](https://github.com/seqeralabs/cx-field-tools-installer/issues/434)
            - `tower.sql` and `groundswell.sql` (`ALTER USER … IDENTIFIED BY …`) and `wave-lite-rds.sql` (`ALTER ROLE … PASSWORD …`) now reset the DB user's password on every apply, so it always matches SSM. **DBA-managed databases:** a password changed directly in the DB, and not in SSM, is reset to the SSM value on the next apply. [`#434`](https://github.com/seqeralabs/cx-field-tools-installer/issues/434)
            - The EC2 boot script (`launch_template_ec2.tpl`) now installs and starts `amazon-ssm-agent`, which the `al2023-ami-minimal` AMI does not include. The installer-created EC2 role gets a new `AllowSSMSessionManagerAgent` statement (`ssm:UpdateInstanceInformation` plus four `ssmmessages:*` actions), so the instance registers with SSM and supports Session Manager.
                - **Existing sites:** the IAM change applies on the next `terraform apply`. The agent only installs on new instances (`user_data` changes are ignored). On a running instance, run `sudo dnf install -y amazon-ssm-agent && sudo systemctl enable --now amazon-ssm-agent`.
                - **Pre-existing IAM role** (`flag_iam_use_prexisting_role_arn = true`): add the same five actions to your role.
                - **Private instances without a NAT:** add `ssm` and `ssmmessages` to `vpc_interface_endpoints_tower`.
            - Default images for Platform v26.2: `tower_container_version` `v26.2.0-RC16`, `data_studio_container_version` `0.14.0` (Connect proxy and server), `wave_lite_container_version` `v1.38.0`. Groundswell stays at `0.4.15`.
            - The frontend image tag now follows the Platform version: `<version>-unprivileged` before v26.2.0, and `<version>` from v26.2.0, where the default image is unprivileged. Pre-release tags such as `v26.2.0-RC16` count as v26.2.
            - Studio templates: added the Connect 0.14.0 images (VSCode 1.105.1, Jupyter 4.6.0, RStudio 2026.01.2, Xpra 6.3.6) as `recommended`. The 0.12.2 images are now `deprecated`, and the 0.11.0 images are removed.
            - New `flag_enable_standard_telemetry` (Platform v26.2.0+): `"standard"` (default) sends standard and basic telemetry; `"basic"` sends basic telemetry only; `"air-gapped"` sends standard telemetry only (basic off) and also writes usage-metric files every 24h (kept 90 days). In every mode, Platform still attempts a call to the Seqera telemetry server; without a route, the call fails and is logged. In air-gapped mode, Ansible creates `/home/ec2-user/.tower/usage-metrics` on the host and mounts it into the `cron` container at `/usage-metrics`, outside `~/target`, which each apply replaces.
            - New `flag_enable_preflight_checks` (Platform v26.2.0+) sets both `TOWER_PREFLIGHT_CHECK_ENABLED` and `TOWER_CREDENTIALS_VALIDATION_ENABLED`. The template default, `true`, matches the upstream default.
            - New `tower_aws_secrets_kms_key_id` (Platform v26.2.0+) sets `TOWER_AWS_SECRETS_KMS_KEY_ID`, an installation-wide customer-managed KMS key that encrypts the temporary AWS Secrets Manager secrets Platform creates for pipeline runs. It applies to every AWS Batch and AWS Cloud compute environment that does not set its own key (Advanced options > Pipeline secrets KMS key), including existing ones. Key ARN or key ID only; aliases are rejected. Empty (the template default) keeps the AWS-managed key. `variables.tf` validates the format, because Platform will not start with an invalid value. No installer IAM change: the compute environment credentials and execution role use the key, not the installer's EC2 role. [`#435`](https://github.com/seqeralabs/cx-field-tools-installer/issues/435)
            - New `tower_actions` (Platform v26.2.0+) restricts the three new Action triggers (bucket event, schedule, pipeline run event), which Platform turns on in every workspace by default, including personal workspaces. Set each `*_allowed_workspaces` to `""` (all workspaces, the default), `"-1"` (off everywhere; the same off value as lineage and WIF), or a comma-separated list of workspace IDs. Restricting a trigger pauses its existing Actions in the excluded workspaces. `trigger_rate_max_per_window` / `trigger_rate_window` set the limit after which an Action is paused (Platform default: 20 per `1h`). `check_configuration.py` warns when bucket triggers are on but can't work: Platform must be reachable from AWS over public HTTPS with a publicly trusted certificate, and Data Explorer must be on. No installer IAM change: bucket triggers use the data repository's credential, not the EC2 instance role. [`#435`](https://github.com/seqeralabs/cx-field-tools-installer/issues/435)
            - New `flag_run_studios_via_private_ca` (Platform v26.2.0+) mounts the private root CA (`rootCA.crt`, PEM) into the `backend` and `cron` containers at `/private-ca/rootCA.crt` and sets `TOWER_SSL_CUSTOM_CA_CERT_FILE`, so Platform and Studios trust services signed by the private CA. Requires `flag_use_private_cacert = true`, `tower_container_version` >= v26.2.0, and `data_studio_container_version` >= 0.12.2; `make verify` enforces these (the matching `variables.tf` validations are commented out until the minimum Terraform version supports cross-variable checks). `make verify` also warns for each Studio template whose image is older than Connect 0.13.0, because those sessions won't trust the CA. Ansible now fails early if `rootCA.crt` is not PEM-encoded. [`#435`](https://github.com/seqeralabs/cx-field-tools-installer/issues/435)
            - Wave-Lite config (`wave-lite.yml.tpl`) updated for v1.38.0: explicit `wave.capabilities` ( set one to `false` to harden, or add `strict` to `MICRONAUT_ENVIRONMENTS`), a dedicated streaming thread pool for blob transfers, `INFO` level for the trace loggers that 1.38 prints at DEBUG, and a commented egress-proxy block. None of these are exposed as tfvars. [`#435`](https://github.com/seqeralabs/cx-field-tools-installer/issues/435)
            - Data lineage updated for Platform v26.2.0, which uses SNS in place of SQS (see Design Decision 23). On v26.2.0+: [`#435`](https://github.com/seqeralabs/cx-field-tools-installer/issues/435)
                - `flag_enable_data_lineage = false` now renders `TOWER_LINEAGE_ALLOWED_WORKSPACES=-1`, because v26.2 treats an unset value as "all workspaces". **Existing sites:** without this, upgrading to v26.2 would turn lineage on in every workspace.
                - `flag_enable_data_lineage = true` also renders `TOWER_LINEAGE_STORE_PREFIX`, `TOWER_LINEAGE_SNS_MAX_RETRIES`, `TOWER_LINEAGE_SNS_MAX_DELAY_SECONDS`, `TOWER_LINEAGE_MIGRATE_SQS_TRANSPORT`, and `TOWER_GLOBAL_SEARCH_ENABLED` from the new `data_lineage_options`, which replaces `data_lineage_allowed_workspaces`.
                - `make verify` fails when lineage is on and AWS SNS can't reach Platform over public HTTPS (private instance, HTTP, private CA, or private-only DNS), and warns when `sg_ingress_cidrs` doesn't include `0.0.0.0/0`.
            - Audit log on Platform v26.2.0+: Platform writes audit events only to the v2 table and has removed `TOWER_AUDIT_LOG_V2_WRITE_MODE`, so `tower.env` now renders it as the `# TOWER_AUDIT_LOG_V2_WRITE_MODE=NOT_AVAILABLE_DO_NOT_UNCOMMENT` marker. `tower_audit_log_v2.write_mode` still applies on v26.1. The template default stays `"dual"` for v26.1 sites. On v26.2.0+, `make verify` warns when `write_mode` is anything other than `"v2"` (including the default `"dual"`), because v1 writes no longer happen; set `write_mode = "v2"` once your readers have moved. **Breaking change for direct DB readers:** no new rows are written to the legacy `tw_audit_log` table. Move scripts and ETL jobs to the v2 schema (or the `/admin/audit-logs-v2` API) before upgrading. Existing v1 rows stay readable in the Admin panel until `tower_audit_retention_days` removes them. [`#435`](https://github.com/seqeralabs/cx-field-tools-installer/issues/435)
            - New `tower_identity_federation_enabled` and `tower_identity_federation_allowed_workspaces` (Platform v26.2.0+) control workload identity federation for AWS and Google Cloud credentials. `false` (the template default) writes `TOWER_IDENTITY_FEDERATION_ALLOWED_WORKSPACES=-1`, so WIF stays off on upgrade even though Platform enables it by default once its OIDC provider is configured. `true` writes the allow-list (empty = all workspaces) and turns on Platform's OIDC provider. `TOWER_OIDC_PEM_PATH` and the `data-studios-rsa.pem` mount into `backend` and `cron` now apply when Studios **or** WIF is on; before, only Studios set them. `make verify` fails when WIF is on before v26.2.0, and warns when STS can't reach `${tower_server_url}/api/.well-known/*` over public HTTPS (private instance, HTTP, private CA, or private-only DNS). The cloud-side trust setup is yours, and Seqerakit can't create WIF credentials. **Existing Google Cloud WIF credentials:** in enabled workspaces, tokens carry `platform` / `data` / `studio` / `workflow` subjects instead of always `workflow`, so update bindings before enabling. See Design Decision 24. [`#435`](https://github.com/seqeralabs/cx-field-tools-installer/issues/435)
            - `make verify` now compares Platform and Connect versions numerically. Text comparison had sorted `0.14.0` before `0.8.2`, so `make verify` rejected Studios path routing with the default Connect `0.14.0`, and skipped the Studios SSH warning for Connect `0.9.x`. Pre-release tags such as `v26.2.0-RC16` count as their release. An unreadable `data_studio_container_version` (for example, `latest`) now stops `make verify` with an error that names the value.
            - `-1` is now the off value for every workspace allow-list the installer writes: Actions triggers (`tower_actions.*_allowed_workspaces = "-1"`), data lineage, and workload identity federation. Platform documents `0` for Actions; `-1` works the same way, because no workspace has that ID.
            - MySQL 8.4 is now the default database, and existing 8.0 databases can be upgraded in place ([`#271`](https://github.com/seqeralabs/cx-field-tools-installer/issues/271); see Design Decision 25 and `documentation/setup/upgrade_mysql_8_4.md`). Platform v26.1+ supports only MySQL 8.4, and RDS for MySQL 8.0 left standard support on 2026-07-31.
                - **Existing sites:** nothing changes until you follow the runbook. Your `terraform.tfvars` keeps `db_engine_version = "8.0"`; `make verify` warns that 8.0 is unsupported on Platform v26.1+.
                - New `db_allow_major_version_upgrade` and `db_apply_immediately` (both `false`) pass through to the RDS module for the upgrade apply. The upgrade changes the instance in place; the parameter and option groups move to 8.4 without replacing the instance.
                - New `make check_db_replacement` fails if the plan deletes or replaces an RDS instance. Run it before the upgrade apply.
                - `make verify` fails if `db_param_group` doesn't match `db_engine_version` (for example, `mysql8.0` with `8.4`).
                - The `connection_strings` module moved to v2.1.0 (`modules/connection_strings/v2.1.0`; v2.0.0 removed). It adds the `platform_db_tls` input; with it off, output is unchanged. **Existing sites:** run `terraform init` after pulling 1.9.0, or `terraform plan` stops with "Module not installed". The module holds no resources, so there is no state change.
                - The MySQL client image in the Ansible DB population steps moved from `mysql:8.0` to `mysql:8.4`. The Seqerakit helper `get_access_token.py` keeps its `mysql:8.0` client, which connects to 8.4 servers (with TLS when the server requires it).
        <br /><br />

        - Security
            - Temporarily suppressed 10 Checkov checks repo-wide in a new root `.checkov.yaml`, pending review. The file lists each check ID and why it is skipped. No infrastructure change.
            - SSM Session Manager is now a supported access path to the EC2 instance. The installer does not restrict who can connect: anyone in the AWS account with `ssm:StartSession` on the instance can open a shell as `ssm-user` (which has `sudo`). Control access, and set up session logging, at the account level. The role deliberately does not get `AmazonSSMManagedInstanceCore`, which would allow reading every SSM parameter in the account. See Design Decision 22.
            - On Platform v26.2.0+, the lineage IAM policy adds the `LineageEnhancedPermissionsforv2620*` statements: SNS topic management and S3 `GetObject` / `ListBucket` on `<store_prefix>-*`, and `sqs:DeleteQueue` on `seqera-lineage-*` for Platform's SQS→SNS migration. The v26.1 SQS permissions are kept. **Pre-existing IAM role:** add the new statements to your role. See Design Decision 23.
            - The OIDC client registration token that Connect uses to register with Platform (`TOWER_OIDC_REGISTRATION_INITIAL_ACCESS_TOKEN` in `tower.env`, `CONNECT_OIDC_CLIENT_REGISTRATION_TOKEN` in `data-studios.env`) was hard-coded as `ipsemlorem`, a value published in this repo. It is now a random 32-character value (`random_password.oidc_registration_token`), generated once and kept in Terraform state. It stays the same across applies and changes only on `terraform destroy` or lost state. No tfvars or SSM change. **Existing Studios sites:** the first 1.9.0 apply changes the token, and Connect re-registers when it restarts.
            - New `db_enforce_tls` (template default `true`) turns on TLS for the Platform database on MySQL 8.4 and later. Platform connects with `useSSL=true&trustServerCertificate=true` (encrypted; the server certificate isn't verified, so no AWS CA bundle is needed), installer-created RDS gets `require_secure_transport=1`, and the container DB runs with `--require-secure-transport=ON`. On MySQL 8.0 nothing changes. **Groundswell:** not yet confirmed to connect with TLS; if it can't, set `db_enforce_tls = false`. See Design Decision 25.
        <br /><br />

        - Documentation
            - Added Design Decision 22 (`documentation/design_decisions.md`): the installer enables SSM Session Manager on the instance, and the AWS account owner controls who can connect.
            - `documentation/setup/optional_private_certificates.md`: `rootCA.crt` must be PEM-encoded, with a DER conversion command.
            - Rewrote Design Decision 19 (lineage infrastructure is Platform's responsibility) to cover SNS, and added Design Decision 23 (data lineage on Platform v26.2.0+). `documentation/setup/optional_data_lineage.md` covers `data_lineage_options`, the v26.2 requirements, and upgrading a v26.1 lineage site.
            - Added Design Decision 24 (workload identity federation) and `documentation/setup/optional_workload_identity_federation.md`, linked from the README.
            - Rewrote `.claude/guidelines/testing_for_tfvars_changes.md` for the current test framework (`expected_deltas.py`, `merge_deltas`, `assert_all_deltas`). It had described the removed `expected_results.py` framework.
            - Added `documentation/setup/upgrade_mysql_8_4.md` (RDS and container DB upgrade runbook) and Design Decision 25 (in-place upgrade, TLS default, replacement guard).
        <br /><br />

        - Testing
            - Added testcontainer tests that run each SQL file twice (`test_tower_sql_rerun`, `test_groundswell_sql_rerun`, `test_wave_sql_rds_rerun`), plus `test_groundswell_sql_population` and `test_tower_sql_rerun_resets_password` (a re-run restores a password changed in the DB). `groundswell.sql` content is now checked in the baseline assertions. [`#434`](https://github.com/seqeralabs/cx-field-tools-installer/issues/434)
            - Test data now pins `tower_container_version = "v26.2.0-RC16"`. The baseline checks the frontend image, and the Xpra keys in the baseline's omitted list are fixed (they had typos). Added `test_frontend_pre_26_2_active` for the `-unprivileged` tag on Platform < v26.2.0.
            - Added `test_telemetry_basic_active` and `test_telemetry_air_gapped_active`. The baseline checks the telemetry keys for the default `"standard"` mode. The variable-validation suite rejects values other than `standard` / `basic` / `air-gapped`.
            - `test_tower_opt_in_flags_active` now also covers `flag_enable_preflight_checks` (`true`), and the baseline covers `false`.
            - `test_tower_opt_in_flags_active` now also covers `tower_aws_secrets_kms_key_id` (set), and the baseline covers it unset. The variable-validation suite rejects an alias name, an alias ARN, and an uppercase key ID.
            - `test_tower_opt_in_flags_active` now also covers `tower_actions` (bucket `"-1"`, schedule and pipeline-run restricted to workspace IDs, rate limit `50` per `2h`), and the baseline covers Platform's defaults (no allow-lists written, `20` per `1h`).
            - Added `test_studios_private_ca_active` (the `rootCA.crt` mount, `TOWER_SSL_CUSTOM_CA_CERT_FILE`, and the PEM check render together) and `test_studios_private_ca_without_private_cacert` (nothing renders without the private CA).
            - The baseline covers lineage off on v26.2 (`-1`), and `test_data_lineage_active` covers the v26.2 lineage keys. Added `test_data_lineage_pre_26_2_active`, and `test_frontend_pre_26_2_active` now covers lineage off on v26.1.
            - The baseline covers the `TOWER_AUDIT_LOG_V2_WRITE_MODE` marker on v26.2, and `test_frontend_pre_26_2_active` covers `TOWER_AUDIT_LOG_V2_WRITE_MODE=dual` on v26.1.
            - Added `test_identity_federation_active` and `test_identity_federation_workspace_restriction_active`. The baseline covers WIF off (`-1`, no OIDC key path or mount), and the Studios assertions now check the key mount in `backend` and `cron`.
            - Added `tests/unit/validation/test_version_checks.py` (16 cases) for the numeric version checks in `check_configuration.py`, including the `0.14.0` path-routing regression.
            - `test_wave_containers` can now fail. A retry-loop bug had turned every failed attempt into a pass. The test also stops at the first good answer, allows about 60 seconds for start-up, and starts Compose with `up --detach` (`wait=False`), because podman-compose's `up --wait` never returns (podman-compose #1535). **Podman users:** run the container tests with `PODMAN_COMPOSE_PROVIDER` set to your `podman-compose`, or set `compose_providers` in `containers.conf`.
            - The test cache key now also covers `wave-lite-rds.sql`, `sedalternative.py`, and `tests/utils/terraform/precompute.py`. Editing one of them no longer leaves an old render in the cache.
            - The baseline now runs on container MySQL 8.4 with TLS (the TLS JDBC suffix and `--require-secure-transport=ON`). Added `test_db_tls_disabled_active` and `test_db_8_0_active` (plaintext on 8.0 even with `db_enforce_tls = true`), and `tests/unit/validation/test_database_checks.py` for the `make verify` database checks and the replacement guard. The SQL testcontainer tests now run against `mysql:8.4`.


### Configuration File Changes
#### `terraform.tfvars`
| Status | Component | Parameter Name | Description |
| ------ | --------- | -------------- | ----------- |
| Deleted | Platform | `tower_server_port` | Unused since 1.6.0: the HTTP-only URL always uses port `8000`, so this value had no effect. Delete the line from your `terraform.tfvars`. If you keep it, Terraform prints a non-fatal "Value for undeclared variable" warning. |
| Modified | Platform | `tower_container_version` | Default `v26.1.3` → `v26.2.0-RC16`. Switch to `v26.2.0` once it is published. |
| Modified | Studios | `data_studio_container_version` | Default `0.11.0` → `0.14.0` (Connect proxy and server). |
| Modified | Wave-Lite | `wave_lite_container_version` | Default `v1.33.0` → `v1.38.0`. |
| Modified | Studios | `data_studio_options` | Added the 0.14.0 templates (`recommended`), marked 0.12.2 `deprecated`, and removed 0.11.0. Copy the new block from `TEMPLATE_terraform.tfvars` into your `terraform.tfvars`. |
| New | Telemetry | `flag_enable_standard_telemetry` | Telemetry mode for Platform v26.2.0+: `"standard"`, `"basic"`, or `"air-gapped"`. Required: add `flag_enable_standard_telemetry = "standard"` to your `terraform.tfvars` to keep Platform's default behaviour. |
| New | Platform | `flag_enable_preflight_checks` | Enables Platform preflight checks and credential validation before pipeline launch (v26.2.0+). Required: add `flag_enable_preflight_checks = true` to your `terraform.tfvars` to keep Platform's default behaviour. |
| New | Platform | `tower_aws_secrets_kms_key_id` | Installation-wide customer-managed KMS key for pipeline secrets (v26.2.0+). Key ARN or key ID; aliases are rejected. Required: add `tower_aws_secrets_kms_key_id = ""` to your `terraform.tfvars` to keep the AWS-managed key. |
| New | Actions | `tower_actions` | Per-trigger workspace allow-lists and trigger rate limit for Actions (v26.2.0+). Required: copy the `tower_actions` block from `TEMPLATE_terraform.tfvars` into your `terraform.tfvars`. The template values keep Platform's defaults (all triggers on everywhere, 20 per `1h`). |
| New | Studios | `flag_run_studios_via_private_ca` | Make Platform and Studios trust the private root CA (v26.2.0+). Requires `flag_use_private_cacert = true`. Required: add `flag_run_studios_via_private_ca = false` to your `terraform.tfvars` unless you use a private CA with Studios. |
| Modified | Audit Log v2 | `tower_audit_log_v2` | `write_mode` no longer accepts `"v1"` (Platform documents only `"dual"` and `"v2"`). If you set `write_mode = "v1"`, change it to `"dual"` or `"v2"`, or `terraform plan` fails. From Platform v26.2.0, `write_mode` is ignored and no longer rendered to `tower.env`. |
| New | Workload Identity Federation | `tower_identity_federation_enabled` | Turns workload identity federation on (v26.2.0+). Required: add `tower_identity_federation_enabled = false` to your `terraform.tfvars` to keep it off. |
| New | Workload Identity Federation | `tower_identity_federation_allowed_workspaces` | Workspaces allowed to use WIF when enabled: `""` = all, or a comma-separated list of workspace IDs. Required: add `tower_identity_federation_allowed_workspaces = ""`. |
| Modified | Database | `db_engine_version` / `db_param_group` | Template defaults `"8.0"` / `"mysql8.0"` → `"8.4"` / `"mysql8.4"`. Existing sites keep their values; to upgrade, follow `documentation/setup/upgrade_mysql_8_4.md`. The two must match, or `make verify` fails. |
| Modified | Database | `db_container_engine_version` | Template default `"8.0"` → `"8.4"`. Back up `~/.tower/db/mysql` before changing it: MySQL 8.4 converts the data files one way. |
| New | Database | `db_enforce_tls` | TLS for the Platform database on MySQL 8.4+ (ignored on 8.0). Required: add `db_enforce_tls = true` (the template default), or `false` if a client can't use TLS. |
| New | Database | `db_allow_major_version_upgrade` | Lets RDS upgrade to a new major version. Required: add `db_allow_major_version_upgrade = false`; set `true` only for the upgrade apply. |
| New | Database | `db_apply_immediately` | Applies RDS changes now instead of in the maintenance window. Required: add `db_apply_immediately = false`; set `true` only for the upgrade apply. |
| Deleted | Data Lineage | `data_lineage_allowed_workspaces` | Replaced by `data_lineage_options.allowed_workspaces`. Move your value into the new block, then delete the line. |
| New | Data Lineage | `data_lineage_options` | Lineage settings: `allowed_workspaces` (all versions), plus `store_prefix`, `sns_max_retries`, `sns_max_delay_seconds`, `migrate_sqs_transport`, and `global_search_enabled` (v26.2.0+). Required: copy the block from `TEMPLATE_terraform.tfvars`. |
| Modified | Data Lineage | `flag_enable_data_lineage` | On v26.2.0+, `false` renders `TOWER_LINEAGE_ALLOWED_WORKSPACES=-1`, and `true` adds SNS permissions and needs public HTTPS. |


## 1.8.1 (July 2026)

- **Notable Changes**
    - **CX Installer**
        - General
            - Added logger config in `tower.yml` to disable noisy (but benign) JWT validation stack traces.
            - Security groups now attach to the EC2 instance directly, not only via the launch template — toggling SG-gating flags (e.g., `flag_enable_data_studio_ssh`) after the initial deploy now propagates to running instances on the next `terraform apply`. Affected sites will see a one-time in-place SG attachment update with no instance replacement. [`#404`](https://github.com/seqeralabs/cx-field-tools-installer/issues/404)
            - Added `make check_upgrade` — a read-only pre-upgrade sanity check. Compares `terraform.tfvars` against `variables.tf` and flags missing/extra variables, verifies the configured backend (local state file or S3 bucket) is reachable, and probes AWS auth via `aws sts get-caller-identity`. Missing-variable output includes the comment context and the full ready-to-paste assignment harvested from `templates/TEMPLATE_terraform.tfvars`. Run from the project root: `make check_upgrade`.
            - Removed `default` values from four variables in `variables.tf` — `flag_enable_data_lineage`, `data_lineage_allowed_workspaces`, `tower_audit_log_v2`, and `tower_compute_env_cleanup` — so they now align with the rest of the project's convention that every variable is set explicitly in `terraform.tfvars` (see `proj:variable_default_values.md`). Deployers upgrading from 1.8.0 who relied on the previous defaults must add explicit values for these four keys; `make check_upgrade` will surface them as REQUIRED-missing with copy-paste-ready blocks. A future release will revisit the broader use of `default` values across the project to lessen the tfvars-update burden — this entry just normalises the four outliers for now.

    - Security
        - Restricted Studios SSH (port 2222) ingress so the EC2 SG only accepts traffic from the NLB's own security group instead of from `var.sg_ingress_cidrs` directly. Previously, deployers using `sg_ingress_cidrs = ["0.0.0.0/0"]` for general HTTP traffic were also exposing SSH to the world. New `sg_studio_ssh_cidrs` tfvars variable is the source-of-truth for "who can reach Studios SSH" and governs the NLB's security group. `check_configuration.py` fails at plan time if `flag_enable_data_studio_ssh = true` and `sg_studio_ssh_cidrs` is empty. **Existing sites with Studios SSH enabled will see the affected security groups replaced on next apply** (the underlying rules change shape from CIDR-based to source-SG-based).
        - **Breaking change.** Studios SSH is now NLB-only. Removed the previously-undocumented direct-to-EC2 path (`module.sg_ec2_noalb_ssh`). No documented or tested deployments used this combo, so impact is expected to be zero, but flagging as breaking for honesty's sake.

    - Documentation
        - Fixed `pipeline_versioning_eligible_workspaces` default value in `TEMPLATE_terraform.tfvars` from `null` to `""`. [`#401`](https://github.com/seqeralabs/cx-field-tools-installer/issues/401)

### Configuration File Changes
#### `terraform.tfvars`
| Status | Component | Parameter Name | Description |
| ------ | --------- | -------------- | ----------- |
| New | Studios SSH | `sg_studio_ssh_cidrs` | List of CIDRs allowed to reach Studios SSH on TCP 2222. Required (non-empty) when `flag_enable_data_studio_ssh = true`. Governs the NLB's security group. Validated at plan time by `check_configuration.py`. |
| Modified | Platform | `pipeline_versioning_eligible_workspaces` | Corrected default value from `null` to `""`. Deployers with `null` set should update to `""` to avoid unexpected behaviour in template rendering. [`#401`](https://github.com/seqeralabs/cx-field-tools-installer/issues/401) |
| Modified | Data Lineage | `flag_enable_data_lineage` | `default` removed from `variables.tf`. Must now be set explicitly in `terraform.tfvars` (e.g. `flag_enable_data_lineage = false`). Aligns with the project convention that every variable is declared in tfvars. |
| Modified | Data Lineage | `data_lineage_allowed_workspaces` | `default` removed from `variables.tf`. Must now be set explicitly in `terraform.tfvars` (e.g. `data_lineage_allowed_workspaces = ""` for all workspaces). |
| Modified | Audit Log v2 | `tower_audit_log_v2` | `default` removed from `variables.tf`. Must now be set explicitly in `terraform.tfvars` — see `templates/TEMPLATE_terraform.tfvars` for the full nested object shape with sensible defaults. |
| Modified | Compute Env Cleanup | `tower_compute_env_cleanup` | `default` removed from `variables.tf`. Must now be set explicitly in `terraform.tfvars` — see `templates/TEMPLATE_terraform.tfvars` for the full nested object shape with sensible defaults. |


## 1.8.0 (June 2026)
- **Forward Roadmap Guidance**

    - **MySQL 8.0 → 8.4 upgrade pathway.**

        MySQL 8.0 is approaching end-of-life and existing customer deployments using the RDS-backed 8.0 engine will need to migrate. Given the operational sensitivity of database migrations — and the matrix of deployment topologies this installer supports — the upgrade pathway will ship as a **dedicated out-of-band release with its own runbook and tooling** rather than being bundled into the 1.8 Release.

        Existing deployments should continue to use `db_engine_version = "8.0"`. ([`#271`](https://github.com/seqeralabs/cx-field-tools-installer/issues/271))

    2. **Upgrade Terraform AWS provider to version 6.** [`#158`](https://github.com/seqeralabs/cx-field-tools-installer/issues/158)

        Update deferred for same reasons as MySQL 8.4 delay.

- **Notable Changes**
    - **CX Installer**
        - General
            - Added Studios SSH support. Requires Platform >= v25.3.3 and connect-proxy >= 0.10.0. [`#313`](https://github.com/seqeralabs/cx-field-tools-installer/issues/313)
            - Updated Platform Connect containers version to 0.11.0.
            - Updated Studios recommended base images.
            - Raised wave-lite nginx `client_max_body_size` from 1m to 10m to prevent HTTP 413 errors when Fusion uploads large bin/ bundles. [`#315`](https://github.com/seqeralabs/cx-field-tools-installer/issues/315)
            - Refactored `connection_strings` module to v2.0.0. Callers now resolve user-facing flags into mode strings (`platform_security_mode`, `platform_db_deployment`, `platform_redis_deployment`, `studio_mode`, `wave_mode`) before invoking the module. Value generation is split into dispatch tables → mode resolution → final URL composition. v1.0.0 removed.
            - Removed the `data "external"` Python script for the DB connection-string suffix; logic now lives as a pure-HCL local conditional on engine version.
            - Migrated 12 single-variable validation checks from `check_configuration.py` to native Terraform `validation` blocks in `variables.tf`. Errors now fire at plan time and are co-located with each variable's declaration. Cross-variable and warning-only checks remain in Python.
            - Added the Platform `workflow-cleanup` feature to `tower.yml` via new `tower_workflow_cleanup_enabled` flag (renders `tower.workflow-cleanup.enabled: true|false` unconditionally). Requires Platform >= v25.1.0 when set to `true`; enforcement remains in `scripts/installer/validation/check_configuration.py` because the check requires a cross-variable comparison with `tower_container_version` (not expressible as a single-variable `validation` block on Terraform 1.1.0).
            - Added project-root `locals.tf` for the six resource-dependent outputs (`aws_account_id`, `aws_caller_arn`, `aws_caller_user`, `ec2_ssh_key`, `aws_ec2_private_ip`, `aws_ec2_public_ip`), each using a `var.use_mocks ? <mock> : try(<production>, <fallback>)` shape. `012_outputs.tf` blocks are now thin passthroughs. Production behaviour unchanged; the locals let `terraform console` evaluate every output without real AWS state, which the test framework consumes for per-scenario `outputs.json`.
            - Added `check_configuration.py` warning for Platform v26.1+ deployments: alerts deployers that new enterprise Harbor credentials are required for `cr.seqera.io/enterprise/platform/` and that credentials for `cr.seqera.io/private/nf-tower-enterprise/` will not grant access to v26.1+ images. [`#378`](https://github.com/seqeralabs/cx-field-tools-installer/issues/378)
            - Migrated container image paths in `docker-compose.yml.tpl` from `cr.seqera.io/private/nf-tower-enterprise/*` to `cr.seqera.io/enterprise/*`. Same manifest digests — image content unchanged. Affects Platform (migrate-db, backend, frontend), Studios (proxy, server), Wave-Lite (server), and Groundswell (server). Deployers logged into `cr.seqera.io` need read access on the new `enterprise/*` projects. **Links:** [`#378`](https://github.com/seqeralabs/cx-field-tools-installer/issues/378)
            - Bumped container image tags in `TEMPLATE_terraform.tfvars` for the v26.1.x release set: `tower_container_version` → `v26.1.3`, `swell_container_version` → `0.4.15`, `data_studio_container_version` → `0.11.0`, `wave_lite_container_version` → `v1.33.0`. `data_studio_options` refreshed: `0.9.0` removed, `0.11.0` marked `deprecated`, `0.12.2` added as `recommended` for VSCode/Jupyter/RIDE/Xpra. The Xpra `0.12.2` qualifier is `XPRA-6-2-0-R2-1-0-12-2` (full hyphenization, distinct from the `0.11.0` form); deployers consuming `TOWER_DATA_STUDIO_TEMPLATES_<qualifier>_*` keys should update accordingly. **Links:** [`#332`](https://github.com/seqeralabs/cx-field-tools-installer/issues/332)
            - Added optional Data Lineage support. New tfvars: `flag_enable_data_lineage` (master gate) and `data_lineage_allowed_workspaces` (CSV; empty = all workspaces). When enabled, the installer renders `TOWER_LINEAGE_ALLOWED_WORKSPACES` in `tower.env` and attaches a new IAM policy granting S3 + SQS actions scoped to `seqera-lineage-*` ARNs. `check_configuration.py` enforces a Platform v26.1.0+ floor and warns when lineage is enabled alongside `flag_iam_use_prexisting_role_arn = true`. Per [Design Decision #19](documentation/design_decisions.md), Platform — not the installer — provisions the SQS queue and S3 bucket when a workspace enables lineage via the UI. **Links:** [`#378`](https://github.com/seqeralabs/cx-field-tools-installer/issues/378)
            - Added Compute Environment Cleanup support as a single `tower_compute_env_cleanup` object with seven `optional()` sub-fields — see the tfvars table below for defaults. Duration-shaped fields are regex-validated. When `enabled = true`, `tower.env` renders the seven `TOWER_COMPUTE_ENV_CLEANUP_*` env vars; the Platform cron service uses them to delete environments stuck in `CREATING`/`DELETING`. Requires Platform v26.1.0+; `check_configuration.py` warns when opted in on an older deployment. **Links:** [`#378`](https://github.com/seqeralabs/cx-field-tools-installer/issues/378), [PR #387](https://github.com/seqeralabs/cx-field-tools-installer/pull/387)
            - Added Audit Log v2 and cron cleanup as a single nested `tower_audit_log_v2` object — three top-level fields plus a nested `cleanup` sub-object. Defaults documented in the tfvars table below. All sub-fields `optional()` so deployers can override one field without restating the rest. Validation enforces `write_mode ∈ {v1, v2, dual}` and a duration regex on `cleanup.interval`/`cleanup.delay`. Disabling cleanup emits `TOWER_CRON_AUDIT_LOG_CLEAN_UP_ENABLED=false` and skips the interval/delay/chunk_size lines. Requires Platform v26.1.0+; `check_configuration.py` warns on older deployments. **Links:** [`#378`](https://github.com/seqeralabs/cx-field-tools-installer/issues/378), [PR #389](https://github.com/seqeralabs/cx-field-tools-installer/pull/389)
            - Added Connect proxy environment variable coverage to `data-studios.env` ([`#378`](https://github.com/seqeralabs/cx-field-tools-installer/issues/378)). 3 new `terraform.tfvars` variables cover the installer-supported subset of the [connect environment variables reference](https://docs.seqera.io/platform-enterprise/enterprise/install-studios#connect-environment-variables): `connect_management_port` (enables management/metrics API; off by default), `connect_management_auth_key` (protects management API), `connect_log_level` (default `debug`; was previously hardcoded). Variables without practical value for standard deployments are intentionally omitted — see [Design Decision #20](documentation/design_decisions.md). Optional vars without a set value render a commented `_NOT_SET=DO_NOT_UNCOMMENT` marker.
            - Announced **seqerakit deprecation**. The `seqerakit_*` tfvars, the post-deployment seqerakit step, and the `seqerakit.yml` template remain in the repo but are **no longer actively maintained**. They will be replaced by the upcoming [Seqera Terraform provider](https://registry.terraform.io/providers/seqeralabs/seqera/latest/docs). The `secrets_bootstrap_seqerakit` SSM path is still required at plan time but may hold placeholder values when `flag_run_seqerakit = false` — except for the `TOWER_AWS_ROLE` key, which `flag_allow_aws_instance_credentials` continues to consume.
            - Replaced the `get-pip.py` network bootstrap in `launch_template_ec2.tpl` with `yum install -y python3-pip`. Upstream `get-pip.py` now requires Python ≥ 3.10, but Amazon Linux 2023 ships Python 3.9 by default — the bootstrap was aborting. The replacement drops the curl/retry loop and pulls pip from the signature-verified AL2023 repo. Drive-by hardening on the same script: added `set -euo pipefail` and changed `yum update` to `yum update -y`.
            - TBD
        <br /><br />

        - Security
            - TBD
        <br/><br/>

        - Documentation
            - Added Studios SSH design decision to `design_decisions.md`. [`#313`](https://github.com/seqeralabs/cx-field-tools-installer/issues/313)
            - Updated `TEMPLATE_terraform.tfvars` with Studios SSH variables and configuration guidance. [`#313`](https://github.com/seqeralabs/cx-field-tools-installer/issues/313)
            - Added explicit Tower user auto-creation flags (`flag_tower_enable_participant_auto_create_user`, `flag_tower_enable_member_auto_create_user`) to `TEMPLATE_terraform.tfvars`. [`#312`](https://github.com/seqeralabs/cx-field-tools-installer/issues/312)
            - Added Data Lineage setup guide at `documentation/setup/optional_data_lineage.md` (linked from `README.md` Configuration Steps section). Added Design Decision #19 to `design_decisions.md` documenting the SQS/S3 lifecycle boundary (Platform's responsibility, not the installer's). [`#378`](https://github.com/seqeralabs/cx-field-tools-installer/issues/378)
            - Added 4 Connect proxy variables to `TEMPLATE_terraform.tfvars` with inline comments and a section-level link to the [connect environment variables reference](https://docs.seqera.io/platform-enterprise/enterprise/install-studios#connect-environment-variables). Added Design Decision #20 to `design_decisions.md` documenting which Connect variables were intentionally omitted and why (table format). [`#378`](https://github.com/seqeralabs/cx-field-tools-installer/issues/378)
            - Restructured `README.md` — renamed `## Supported Seqera Platform Versions` to `## Supported Versions & Components` and broke its content into two bullets: the existing Platform v25+ floor + a new seqerakit deprecation notice (see General changes above). Propagated short deprecation banners across the affected setup docs: `templates/TEMPLATE_terraform.tfvars` (section docstring), `documentation/setup/prepare_secrets.md`, `prepare_ssm.md`, `prepare_tfvars.md`, `configuration_files.md`, `optional_allow_instance_credentials.md` (with the `TOWER_AWS_ROLE` exception noted inline), and `documentation/deficiencies_and_gotchas.md` (closure update on the existing `tw cli` limitations gotcha).
            - TBD
        <br /><br />

        - Testing
            - Updated baseline tests for new Studios 0.11.0 connect-proxy version.
            - Added parametrized round-based regression test for the 12 migrated single-variable validations (`tests/unit/variable_validation/`); new Makefile recipes (`run_tests_all`, `run_tests_core_only`, `run_tests_containers_only`, `run_tests_variables_only`, `run_tests_core_and_containers`, `run_tests_core_and_variables`) for marker-based test slicing.
            - Split the AWS SSO preflight out of the universal `session_setup` fixture into a dedicated opt-in `aws_preflight` fixture. Tests that interact with real AWS list `aws_preflight` as a fixture parameter; `tests/unit/` no longer requires the `aws` CLI. Closes [`#351`](https://github.com/seqeralabs/cx-field-tools-installer/issues/351).
            - Phase 1 of the `hcl2json` Docker-overhead removal (linux/amd64): added `extract_hcl2json` Makefile recipe that pulls the Go binary out of the vendored container once at setup time and places it at `/tmp/cx-installer/hcl2json` (project-namespaced so bwrap-style sandboxes can mount the directory into the jail); wired the recipe as a prerequisite on `verify` and every `run_tests_*` target. `scripts/installer/utils/extractors.py` now dispatches to the extracted binary (~10-50 ms/call instead of ~1-2 s) on supported hosts, fails fast with an instructional message when the binary is missing on a supported host, and keeps the per-call `docker run` fallback for unsupported hosts (Darwin until Phase 3). `tests/conftest.py` uses the shared helper instead of an inline `docker run`. Net effect: `tests/unit/` is runnable in sandboxed environments where Docker is blocked at runtime, provided extraction happened outside the sandbox (or `/tmp/cx-installer/` is mounted into it). [`#352`](https://github.com/seqeralabs/cx-field-tools-installer/issues/352)
            - Templatefile test path no longer requires `terraform plan`. `module.connection_strings.*` outputs now resolve via a single `terraform console` call (~1–2 s vs ~30+ s for plan). The plan path stays opt-in for tests that need plan-derived state; templatefile-only tests migrated to the new `stage_tfvars(...)` + `generate_tc_files(None, ...)` shape. New regression test `test_console_locals_resolvability.py` walks every `local.<name>` in `009_define_file_templates.tf` and asserts each resolves via console — catching the silent-corruption case where a future local mixes tfvars-known and resource-attribute branches. Two-layer defense pattern documented above the `module "connection_strings"` invocation in [`000_main.tf`](000_main.tf). **Links:** [`#353`](https://github.com/seqeralabs/cx-field-tools-installer/issues/353)
            - Phase 2 of the `hcl2json` Docker-overhead removal: arm64 support. Platform detection accepts `aarch64`/`arm64`; the `--platform linux/amd64` flag is no longer pinned on the docker fallback (which would silently emulate). Republished the vendored container as a multi-arch manifest at `ghcr.io/seqeralabs/cx-field-tools-installer/hcl2json:0.6-vendored-multiarch`; the original `:vendored` tag stays put for reverse compatibility. `extract_hcl2json` now probes `docker info` first — if the daemon is unreachable but `HCL2JSON_BIN` already exists (e.g. a sandbox that mounts the binary but blocks Docker), it reuses the existing binary; otherwise it fails fast with an actionable message. **Links:** [`#352`](https://github.com/seqeralabs/cx-field-tools-installer/issues/352)
            - Batched per-template `terraform console` renders into a single call per scenario. Cache-miss templatefile payloads now render via one `jsonencode({...})` map, saving the ~1.85 s startup previously paid per template. Cold-cache `make run_tests_core_only` drops from ~155 s to ~87 s (~44 %). The single-template helper is retained for unit-level rendering and blame-narrowing. Tradeoff: a batch failure points the pytest traceback at the batched renderer, but the offending expression is identifiable from `terraform console`'s native error. **Links:** [`#361`](https://github.com/seqeralabs/cx-field-tools-installer/issues/361)
            - Added Data Lineage test coverage ([`#378`](https://github.com/seqeralabs/cx-field-tools-installer/issues/378)): `test_data_lineage_active` (master flag on, no workspace restriction → empty allowlist = all workspaces) and `test_data_lineage_workspace_restriction_active` (allowlist flips to the configured CSV). New `data_lineage` marker registered in `tests/pytest.ini`. `BASELINE_ASSERTIONS` extended with a `# TOWER_LINEAGE_NOT_ENABLED` off-state marker and a `TOWER_LINEAGE_ALLOWED_WORKSPACES` omitted-guard so a buggy template that renders the env var unconditionally fails strict-mode.
            - Added Compute Environment Cleanup test coverage ([`#378`](https://github.com/seqeralabs/cx-field-tools-installer/issues/378)): `test_compute_env_cleanup_active` asserts all 7 `TOWER_COMPUTE_ENV_CLEANUP_*` vars surface in `tower.env` with their defaults when `tower_compute_env_cleanup_enabled = true`. New `compute_env_cleanup` marker registered in `tests/pytest.ini`. `BASELINE_ASSERTIONS` extended with a `# TOWER_COMPUTE_ENV_CLEANUP_NOT_ENABLED` off-state marker and 7 omitted-guards.
            - TBD


### Configuration File Changes
#### `terraform.tfvars`
| Status | Component | Parameter Name | Description |
| ------ | --------- | -------------- | ----------- |
| New | Studios SSH | [`flag_enable_data_studio_ssh`](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.8.0/templates/TEMPLATE_terraform.tfvars#L449) | Master toggle to enable SSH access into running Studio sessions. Requires `flag_enable_data_studio = true` and Platform >= v25.3.3. When enabled, a dedicated NLB is provisioned (if `flag_create_load_balancer = true`) and a `connect-ssh.<tower_server_url>` DNS record is created. |
| New | Studios SSH | [`flag_limit_data_studio_ssh_to_some_workspaces`](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.8.0/templates/TEMPLATE_terraform.tfvars#L450) | When `true`, restricts SSH access to the workspace IDs listed in `data_studio_ssh_eligible_workspaces`. When `false`, SSH is available to all workspaces. |
| New | Studios SSH | [`data_studio_ssh_eligible_workspaces`](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.8.0/templates/TEMPLATE_terraform.tfvars#L451) | Comma-separated list of numeric workspace IDs that are permitted to use Studios SSH. Only evaluated when `flag_limit_data_studio_ssh_to_some_workspaces = true`. |
||||
| New | Studios | [`data_studio_default_lifespan`](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.8.0/templates/TEMPLATE_terraform.tfvars#L460) | Sets the default lifespan (in hours) for Studio sessions before auto-stop. Increase for long-running analysis workflows; decrease to reclaim idle compute. Instance-global — no per-workspace override. Default `"8"`. Requires Platform v26.1.0+. [`#378`](https://github.com/seqeralabs/cx-field-tools-installer/issues/378) |
| New | Studios | [`flag_studio_private_by_default`](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.8.0/templates/TEMPLATE_terraform.tfvars#L461) | When `true`, newly created Studio sessions are visible only to their creator until explicitly shared. Default `false` makes Studios workspace-visible on creation. Organizations handling sensitive data should set this to `true`. Requires Platform v26.1.0+. [`#378`](https://github.com/seqeralabs/cx-field-tools-installer/issues/378) |
||||
| New | Studios Metrics | [`data_studio_metrics_eligible_workspaces`](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.8.0/templates/TEMPLATE_terraform.tfvars#L464) | Comma-separated list of numeric workspace IDs where Studio usage metrics (CPU, memory, session duration) are collected. Empty string = all workspaces. Useful for cost-allocation reporting or phased rollouts. Requires Platform v26.1.0+. [`#378`](https://github.com/seqeralabs/cx-field-tools-installer/issues/378) |
||||
| New | Studios Wave | [`data_studio_wave_disallowed_registries`](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.8.0/templates/TEMPLATE_terraform.tfvars#L468) | Comma-separated list of container registries blocked as Wave build destinations for custom Studio images. Default blocks `community.wave.seqera.io`. Organizations mandating use of a private registry should extend this list. Requires `flag_use_wave = true` and Platform v26.1.0+. [`#378`](https://github.com/seqeralabs/cx-field-tools-installer/issues/378) |
| New | Studios Wave | [`data_studio_wave_custom_image_registry`](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.8.0/templates/TEMPLATE_terraform.tfvars#L469) | Overrides the registry Wave uses when pushing custom-built Studio images. Leave empty to use Wave's default. Set this when org policy requires all container builds to land in a specific private registry. Requires `flag_use_wave = true` and Platform v26.1.0+. [`#378`](https://github.com/seqeralabs/cx-field-tools-installer/issues/378) |
| New | Studios Wave | [`data_studio_wave_custom_image_repository`](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.8.0/templates/TEMPLATE_terraform.tfvars#L470) | Overrides the repository path for Wave-built Studio images. Built-in default follows the `data-studios/<tool>` pattern. Set this to match your org's registry namespace conventions. Requires `flag_use_wave = true` and Platform v26.1.0+. [`#378`](https://github.com/seqeralabs/cx-field-tools-installer/issues/378) |
||||
| New | Tower Auth | [`flag_tower_enable_participant_auto_create_user`](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.8.0/templates/TEMPLATE_terraform.tfvars#L858) | Controls Tower's `tower.participant.auto-create-user`. When `true`, allows a workspace participant to be auto-created when added by email. Defaults to `false`. [`#312`](https://github.com/seqeralabs/cx-field-tools-installer/issues/312) |
| New | Tower Auth | [`flag_tower_enable_member_auto_create_user`](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.8.0/templates/TEMPLATE_terraform.tfvars#L859) | Controls Tower's `tower.member.auto-create-user`. When `true`, allows the underlying User entity to be auto-created when an email is added as an Org Member. Defaults to `false`. [`#312`](https://github.com/seqeralabs/cx-field-tools-installer/issues/312) |
||||
| New | Tower | [`tower_workflow_cleanup_enabled`](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.8.0/templates/TEMPLATE_terraform.tfvars#L881) | Toggles Platform's `tower.workflow-cleanup.enabled`. When `true`, AWS Batch workflow cleanup runs after job completion. Requires Platform >= v25.1.0; the value renders to `tower.yml` regardless of state. |
||||
| New | Data Lineage | [`flag_enable_data_lineage`](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.8.0/templates/TEMPLATE_terraform.tfvars#L577) | Master gate for Nextflow Data Lineage (Platform v26.1.0+). When `true`, `tower.env` renders `TOWER_LINEAGE_ALLOWED_WORKSPACES` and the installer attaches an IAM policy granting S3/SQS actions scoped to `seqera-lineage-*` resource ARNs. Defaults to `false`. [`#378`](https://github.com/seqeralabs/cx-field-tools-installer/issues/378) |
| New | Data Lineage | [`data_lineage_allowed_workspaces`](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.8.0/templates/TEMPLATE_terraform.tfvars#L578) | Comma-separated list of numeric workspace IDs allowed to use Data Lineage. Empty string = all workspaces (when `flag_enable_data_lineage = true`). Ignored when the master gate is off. [`#378`](https://github.com/seqeralabs/cx-field-tools-installer/issues/378) |
||||
| New | Compute Env Cleanup | [`tower_compute_env_cleanup`](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.8.0/templates/TEMPLATE_terraform.tfvars#L898) | Bundled object (Platform v26.1.0+) configuring the scheduled cleanup job for compute environments stuck in CREATING/DELETING states. Sub-fields: `enabled` (bool, default `false`), `delay`/`interval`/`time_offset`/`stuck_creating_timeout`/`stuck_deleting_timeout` (durations matching `^[0-9]+(ms|s|m|h|d)$`), `batch_size` (number, default `10`). All sub-fields `optional()` — deployers flipping `enabled = true` get sensible defaults for everything else. [`#378`](https://github.com/seqeralabs/cx-field-tools-installer/issues/378) |
| New | Audit Log v2 | [`tower_audit_log_v2`](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.8.0/templates/TEMPLATE_terraform.tfvars#L869) | Bundled object (Platform v26.1.0+) configuring audit-log-v2 write semantics and the cron-based purge job. Top-level fields: `write_mode` (`"v1"`/`"v2"`/`"dual"`, default `"dual"`), `csv_export_max_logs` (number, default `500000`), `pre_post_change_enabled` (bool, default `false`). Nested `cleanup` sub-object: `enabled` (bool, default `true`), `interval` (duration, default `"5m"`), `delay` (duration, default `"10s"`), `chunk_size` (number, default `1000`). All sub-fields `optional()` — deployers can omit the block or override individual fields without restating the rest. [`#378`](https://github.com/seqeralabs/cx-field-tools-installer/issues/378) |
| New | Redis | [`platform_redis_elasticache`](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.8.0/templates/TEMPLATE_terraform.tfvars#L679) | Configuration block (`node_type`, `num_cache_nodes`, `engine_version`, `port`) for the standalone Seqera Platform ElastiCache (Redis) cluster. Required when `flag_create_external_redis = true`. |
| New | Connect proxy | [`connect_management_port`](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.8.0/templates/TEMPLATE_terraform.tfvars#L473) | Port for metrics, readiness, and shutdown endpoints. Leave empty to disable. [`#378`](https://github.com/seqeralabs/cx-field-tools-installer/issues/378) |
| New | Connect proxy | [`connect_management_auth_key`](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.8.0/templates/TEMPLATE_terraform.tfvars#L474) | Authentication key protecting management service endpoints. Leave empty if not using the management port. [`#378`](https://github.com/seqeralabs/cx-field-tools-installer/issues/378) |
| New | Connect proxy | [`connect_log_level`](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.8.0/templates/TEMPLATE_terraform.tfvars#L475) | Logging verbosity (`debug`, `info`, `warn`, `error`). Default `debug`. Previously hardcoded to `debug` in `data-studios.env`. [`#378`](https://github.com/seqeralabs/cx-field-tools-installer/issues/378) |
||||
| Modified | Platform | [`tower_container_version`](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.8.0/templates/TEMPLATE_terraform.tfvars#L43) | Updated from v25.3.0 to v26.1.3 (v26.1.x release set). [`#332`](https://github.com/seqeralabs/cx-field-tools-installer/issues/332) |
| Modified | Groundswell | [`swell_container_version`](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.8.0/templates/TEMPLATE_terraform.tfvars#L393) | Updated from 0.4.6 to 0.4.15 (v26.1.x release set). [`#332`](https://github.com/seqeralabs/cx-field-tools-installer/issues/332) |
| Modified | Studios | [`data_studio_container_version`](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.8.0/templates/TEMPLATE_terraform.tfvars#L444) | Updated from 0.9.0 to 0.11.0 Note: Studios SSH requires connect-proxy >= 0.10.0. [`#332`](https://github.com/seqeralabs/cx-field-tools-installer/issues/332) |
| Modified | Studios | [`data_studio_options`](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.8.0/templates/TEMPLATE_terraform.tfvars#L493) | Removed 0.9.0 images. Added 0.11.0 (deprecated) and 0.12.2 (recommended) for Jupyter, RIDE, and Xpra. Xpra 0.12.2 qualifier uses the full `XPRA-6-2-0-R2-1-0-12-2` hyphenization. [`#332`](https://github.com/seqeralabs/cx-field-tools-installer/issues/332). |
| Modified | Wave-Lite | [`wave_lite_container_version`](https://github.com/seqeralabs/cx-field-tools-installer/blob/1.8.0/templates/TEMPLATE_terraform.tfvars#L231) | Updated from v1.29.1 to v1.33.0 (v26.1.x release set). [`#332`](https://github.com/seqeralabs/cx-field-tools-installer/issues/332) |
||||




## 1.7.0
- **Forward Roadmap Guidance**

    To help implementers plan effectively, please be aware of upcoming changes targeted for the next release. Implementation details are not yet finalized, so interested parties are invited to comment on the related GitHub Issues.

    Note these items in particular:

    1. Upgrade AWS RDS MySQL 8.0 to 8.4. [`#271`](https://github.com/seqeralabs/cx-field-tools-installer/issues/271)
    2. Upgrade Terraform AWS provider to version 6. [`#158`](https://github.com/seqeralabs/cx-field-tools-installer/issues/158)

    All in-scope ticket will be tagged with label `v1.8 Release`.

- **Notable Changes**
    - **CX Installer**
        - General
            - Updated Seqera Platform container version from v25.2.2 to v25.3.0. [`264`](https://github.com/seqeralabs/cx-field-tools-installer/issues/264)
            - Updated redis to `7.2.6` for Platform and Wave. [`#251`](https://github.com/seqeralabs/cx-field-tools-installer/issues/251)
            - Updated Seqera Platform frontend container to use non-privileged version. [`#270`](https://github.com/seqeralabs/cx-field-tools-installer/issues/270)
            - Updated Groundswell container version from 0.4.3 to 0.4.6. [`#238`](https://github.com/seqeralabs/cx-field-tools-installer/issues/238)
            - Updated Platform Connect containers version to 0.9.0. [`#273`](https://github.com/seqeralabs/cx-field-tools-installer/issues/273)
            - Updated Studios recommended base images. [`#273`](https://github.com/seqeralabs/cx-field-tools-installer/issues/273)
            - Changed `wave-db` container pin from `postgres:latest` to `postgres:17.6`. This is necessary to due to a change in how the [data directory is managed in postgres containers >= 18](https://hub.docker.com/_/postgres#pgdata). [`#250`](https://github.com/seqeralabs/cx-field-tools-installer/issues/250)
            - Modified `wave-db` and `wave-redis` port configuration to resolve string conversion error. [`298`](https://github.com/seqeralabs/cx-field-tools-installer/issues/298)
            - Added Seqera Platform pipeline versioning feature. [`#284`](https://github.com/seqeralabs/cx-field-tools-installer/issues/284)
            - Removed `FLYWAY_LOCATIONS` as configurable option. [`268`](https://github.com/seqeralabs/cx-field-tools-installer/issues/268)
            - Added [EC2 instance role option](https://docs.seqera.io/platform-enterprise/enterprise/advanced-topics/use-iam-role#configure-seqera). [`#242`](https://github.com/seqeralabs/cx-field-tools-installer/issues/242)
            - Added warning and check for personal workspace disablement. [`#246`](https://github.com/seqeralabs/cx-field-tools-installer/issues/246)
            - Added setting to auto-assign IPv4 addresses to instances in public subnets.
            - Modified docker compose file to use official Seqera Wave image & made image tag configurable. [`#252`](https://github.com/seqeralabs/cx-field-tools-installer/issues/252)
            - Made OpenAPI support configurable.
            - Entra ID (aka Azure AD) changes:
                - Added OAUTH2 configuration snippet in `tower.yml.tpl` for Platform versions < 25.3. [`#267`](https://github.com/seqeralabs/cx-field-tools-installer/issues/267)
                - Added verification check and warning. [`#276`](https://github.com/seqeralabs/cx-field-tools-installer/issues/276)
            - Changed backtick in Seqerakit yml to avoid TF warning message. [`#218`](https://github.com/seqeralabs/cx-field-tools-installer/issues/218)
            - Added `$.tower.runner.phantom-job.interval` value to _tower.yml.tpl_ to make UNKNOWN timeout configurable. [`#160`](https://github.com/seqeralabs/cx-field-tools-installer/issues/160)
        <br /><br />

        - Security
            - Bumped `runc` from 1.3.0 to 1.3.4. [`#272`](https://github.com/seqeralabs/cx-field-tools-installer/issues/272)
            - Bumped `docker` from 28.3.3 to 28.5.2. [`#272`](https://github.com/seqeralabs/cx-field-tools-installer/issues/272)
        <br/><br/>
        - Documentation
            - Updated instance role docs to reflect terraform deployment option. [`#242`](https://github.com/seqeralabs/cx-field-tools-installer/issues/242)
            - Updated templated `terraform.tfvars` with instance role flag and related considerations. [`#242`](https://github.com/seqeralabs/cx-field-tools-installer/issues/242)
            - Fixed hanging hypen in `permissions.md` document.
        <br /><br />

        - Testing
            - Added refactored local testing framework. Validates `tower.env` to ensure correct representation of the EC2 instance role option, `TOWER_ALLOW_INSTANCE_CREDENTIALS`, based on selection set in terraform.tfvars file. [`#242`](https://github.com/seqeralabs/cx-field-tools-installer/issues/242)
            - Added `labels.seqera` entry to each Wave-Lite container to facilatate positive testing (in support of [`#249`](https://github.com/seqeralabs/cx-field-tools-installer/issues/249)).
            - Added `labels.seqera` entry to generic `reverseproxy` container to align with Wave-Lite changes.
            - Updated baseline tests for new studios 0.9.0 version and Platform v25.3.0 feature flags.


### Configuration File Changes
#### `terraform.tfvars`
| Status | Component | Parameter Name | Description |
| ------ | --------- | -------------- | ----------- |
| New | Platform & Seqerakit | `flag_allow_aws_instance_credentials` | Allows activation of EC2 Instance Role for Seqera Platform to use when authenticating to AWS. |
| New | Platform | `flag_map_public_ip_on_launch` | Configure VPC module to enable auto-assignment of IPv4 addresses to instances spun up in public subnets. |
| New | Platform | `tower_enable_openapi` | Control whether your Platform instance enables the OpenAPI console or not. |
| New | Platform | `tower_enable_pipeline_versioning` | Control pipeline version feature. |
| New | Platform | `pipeline_versioning_eligible_workspaces` | Specific Platform Workspaces where pipeline versioning is active. |
| New | Wave | `wave_lite_container_version` | Specify the exact Wave image to be deployed for the Wave-Lite service. |
||||
| Modified | Platform | `tower_container_version` | Updated from v25.2.2 to v25.3.0 |
| Modified | Groundswell | `swell_container_version` | Updated  from 0.4.3 to 0.4.6 |
| Modified | Studios | `data_studio_container_version` | Updated  from 0.8.3 to 0.9.0 |
| Modified | Studios | `data_studio_options` | Removed 0_8_0 images and added 0_9_0 images |
||||
| Deleted | Platform | `flyway_locations` | Classpath configuration. Not necessary in modern deployments. |




## 1.6.1
- **Notable Changes**:
    - **CX Installer**
        - General
            - Patched issues reported in [234 - Release 1.6.0 deployment issues](https://github.com/seqeralabs/cx-field-tools-installer/issues/234)
            - Added explicit call-out in 1.6.0 section that new variable `use_mocks` was added.
        <br /><br />
        - Architecture
            - All Security Group resources from 1.5.0 reintroduced in a deprecation section at bottom of `002_security_groups.tf`. This is to help existing sites transition to the new 1.6.0+ SG model.
                - Commented out ingress rules for deprecated SG `tower_ec2_direct_connect_sg` due to `local.tower_ec2_direct_connect_sg_final` no longer existing.
                - Commented out ingress rules for deprecated SG `tower_ec2_alb_connect_sg` due to `local.tower_ec2_alb_connect_sg_final` no longer existing.
            - Modified `connection_strings` module:
                - `data.external.generate_db_connection_string` to use absolute path from module root rather than relative path.
                - Added `wave_lite_enabled` qualifier to variables associated with Wave Lite external DB and external Redis.
        <br /><br />
        - Documentation
            - Renamed _Changelog_ entry from `2.0.0` to `1.6.0`.
            - Added discrete _Upgrade Steps_ page.
            - Added warning re: EBS volume during multi-version upgrade cycle.
            - Added escape hatch documentation is deployed resource doesn't reflect expected changes.


### Configuration File Changes
#### `terraform.tfvars`
| Status | Component | Parameter Name | Description |
| ------ | --------- | -------------- | ----------- |
| Modified | Platform | `ec2_root_volume_size` | Changed from `8` to `16` to provide more storage buffer. |


## 1.6.0

### Feature Updates & Improvements
- **Breaking Changes**:
    - Private certificates served from deployed EC2 must now be pre-loaded to S3 Bucket prior to deployment.

- **Notable Changes**:
    - **Seqera Ecosytem**
        - Platform
            - Bumped Platform version to `v25.2.0`.
            - Crypto secret rotation added.

        - Studios
            - Bumped Studio version to `0.8.3`.
            - Studios path-based routing supported for ALB & EC2-direct flow.
            - Added `0.8.5` Studios client images.

        - Wave
            - Wave-Lite support introduced.

        - Groundswell
            - Bumped image to `0.4.3`.


    - **CX Installer**
        - General
            - Began experimenting producing code with AI. Efforts are tightly scoped and 100% human supervised thus far.
        <br /><br />
        - Architecture
            - Subnet reconcilation logic centralized in module `subnet_collector`.
            - URL / connection string generation logic centralized in module `connection_strings`.
            - Changed private certificate flow: Certs must now be pre-loaded to S3 bucket & are pulled at run-time.
            - Refactored `assets/src/customcerts/`: Generation script supports multiple domains & removed placeholder files.
            - Merged / broke out EC2 security groups for easier management and better permissions scoping. **This could break ancillary components if you reused the security groups elsewhere!**
            - Refactored when most `assets/target/` files are produced. Rather than waiting for all infrastructure to be created, we now create files as soon as minimal dependencies are met (_to facilitate testing_).
            - Added new variable `use_mocks`to `variables.tf`. This value defaults to `false` since it should only be `true` during testing.
            - Added `... && !var.use_mock` to database and redis assets' `count` property to facilitate testing.
            - Moved conditional Ansible steps from Bash environment logic to `.tpl` inclusion / exclusion.
            - Modified `docker-compose.yml` so that all configuration files are mounted from their respective `target/**` folder.
            - Bumped `seqerakit --> v0.5.5` and `tw --> 0.14.0`.
            - Broke out monolithic step in `011_configure_vm.tf` into smaller chained resources for bettter visibility and reduced blast radius.
        <br /><br />
        - Security
            - Bumped `java-17-amazon-corretto-devel-1:17.0.14+7-1.amzn2023.1` to `java-17-amazon-corretto-devel-1:17.0.16+8-1.amzn2023.1`.
            - Bumped docker version from `28.1.1` --> `28.3.3`.
        <br /><br />
        - Documentation
            - Changed `TEMPLATE_terraform.tfvars` application name from `tower-dev` to `tower-template`.
            - Added Design Decision explaining why Studio subdomain routing is the default over path-based routing.
            - Added Setup guidance re: Platform crypto secret rotation.
            - Added Setup guidance re: how to prepare / pre-loaded Private Certificates.
        <br /><br />
        - Validation
            - Added Studios path-based routing checks & warnings.
        <br /><br />
        - Testing
            - Added preliminary testing framework. Validates outputs of `module.connection_strings` and some files in `assets/target/`.
            - Added preliminary MySQL & Postgres & Docker Compose Testcontainers for local validation.
            - Added test data generation (tfvars & secrets) mechanism.
            - Added test logging facility (via Pytest lifecycle hooks) to facilitate human observability and AI agent resolution.
            - Added Pytest marks to allow for targeted test runs.
            - Added `terraform plan` caching mechanism to speed up n+1 tests.


### Configuration File Changes
#### `terraform.tfvars`
| Status | Component | Parameter Name | Description |
| ------ | --------- | -------------- | ----------- |
| New | Studios | `flag_studio_enable_path_routing` | Enables/Disables Studios path-based routing. |
| New | Studios |  `flag_studio_enable_path_routing` | The URL to use rather than default subdomain approach. |
| New | Wave-Lite | `secrets_bootstrap_wave_lite` | Secrets associated with Wave-Lite configuration. |
| New | Wave-Lite | `flag_use_wave_lite` | Enables/Disables Wave-Lite. |
| New | Wave-Lite | `num_wave_lite_replicas` | Number of Wave-Lite relicas to run. |
| New | Private Certificate | `flag_use_private_cacert` | Single flag replacing `flag_generate_private_cacert` & `flag_use_existing_private_cacert` |
| | | | |
| Modified | Studios | `data_studio_options` | Removed deprecated entries. Added `0.8.4` options. |
| Modified | Private Certificate | `bucket_prefix_for_new_private_ca_cert` | Renamed to `private_cacert_bucket_prefix`. |
| | | | |
| Deleted | Wave-Lite | `wave_lite_server_url` | The URL to use to check the Wave-Lite endpoint. |
| Deleted | Private Certificate | `flag_generate_private_cacert` | Deleted in favour of unified `flag_use_private_cacert` |
| Deleted | Private Certificate | `flag_use_existing_private_cacert` | Deleted in favour of unified `flag_use_private_cacert` |
| Deleted | Private Certificate | `existing_ca_cert_file` | Deleted since not required after S3 Bucket pre-load flow change. |
| Deleted | Private Certificate | `existing_ca_key_file` | Deleted since not required after S3 Bucket pre-load flow change. |
| Deleted | Private Certificate | `flag_use_custom_docker_compose_file` | Deleted since not required after S3 Bucket pre-load flow change. |




#### SSM Secrets
- Added `templates/ssm_sensitivie_values_wave_lite.json`
