# Live testing items for the v26.2.0 update (release 1.9.0)

**NOTE: This is a rough dump of testing scenarios, generated during creation of features. Needs human review for accuracy. (circa Sept 30/26)**

These items need a real AWS deployment. The unit and testcontainer suites don't cover them.
Each item lists the check and the expected result. Tick an item when it passes.

Tracking epic: [#435](https://github.com/seqeralabs/cx-field-tools-installer/issues/435).

## Before you start: update your `terraform.tfvars`

A 1.8.x `terraform.tfvars` fails `terraform plan` on 1.9.0 until you make these changes. They follow the CHANGELOG `terraform.tfvars` table. Run `make check_upgrade` before and after to confirm nothing is missing.

**Add** these variables. The values below are the template defaults, which keep each feature off or at Platform's default:

```hcl
flag_enable_standard_telemetry  = "standard"
flag_enable_preflight_checks    = true
tower_aws_secrets_kms_key_id    = ""
flag_run_studios_via_private_ca = false

tower_identity_federation_enabled            = false
tower_identity_federation_allowed_workspaces = ""

db_enforce_tls                 = true
db_allow_major_version_upgrade = false
db_apply_immediately           = false

tower_actions = {
  bucket_trigger_allowed_workspaces   = ""
  cron_trigger_allowed_workspaces     = ""
  pipeline_trigger_allowed_workspaces = ""
  trigger_rate_max_per_window         = 20
  trigger_rate_window                 = "1h"
}

data_lineage_options = {
  allowed_workspaces    = ""   # move your old data_lineage_allowed_workspaces value here
  store_prefix          = "seqera-lineage"
  sns_max_retries       = 17
  sns_max_delay_seconds = 300
  migrate_sqs_transport = true
  global_search_enabled = true
}
```

**Change** these values:

| Variable | From (1.8.x) | To (1.9.0) |
|---|---|---|
| `tower_container_version` | `"v26.1.3"` | `"v26.2.0-RC16"` (use `"v26.2.0"` once it's published) |
| `data_studio_container_version` | `"0.11.0"` | `"0.14.0"` |
| `wave_lite_container_version` | `"v1.33.0"` | `"v1.38.0"` |
| `data_studio_options` | 1.8.x block | Copy the whole block from `TEMPLATE_terraform.tfvars` (adds the 0.14.0 templates, marks 0.12.2 deprecated, removes 0.11.0) |
| `tower_audit_log_v2.write_mode` | `"v1"` (if you set it) | `"dual"` or `"v2"`. `"v1"` now fails `terraform plan`. |
| `db_engine_version` / `db_param_group` | `"8.0"` / `"mysql8.0"` | Leave them for the first upgrade test, then change to `"8.4"` / `"mysql8.4"` by following `documentation/setup/upgrade_mysql_8_4.md`. A fresh deployment uses `"8.4"` / `"mysql8.4"`. |
| `db_container_engine_version` | `"8.0"` | Same as above: `"8.4"` for a fresh deployment; back up `~/.tower/db/mysql` before changing an existing one. |

**Delete** these lines:

| Variable | Why |
|---|---|
| `tower_server_port` | Unused since 1.6.0. Leaving it in only prints a "Value for undeclared variable" warning. |
| `data_lineage_allowed_workspaces` | Replaced by `data_lineage_options.allowed_workspaces`. Move the value first. |

**Values that now mean "off":** `-1` switches off lineage (`flag_enable_data_lineage = false` writes it for you), WIF (`tower_identity_federation_enabled = false` writes it for you), and each Actions trigger (set `*_allowed_workspaces = "-1"` yourself).

## Fresh deployment (run once, covers most items)

Deploy a new stack with Studios, Groundswell, and Wave-Lite on.

### VM pipeline (#418 follow-up fixes)

- [ ] **cloud-init wait.** During `terraform apply`, the `ssh_probe` stage waits for `cloud-init status --wait`, then prints `==== STAGE OK:    ssh_probe ====`.
- [ ] **Docker group.** On the host, `id ec2-user` lists `docker`. No Ansible step fails with `permission denied … /var/run/docker.sock`.
- [ ] **ControlMaster socket.** `<project_root>/.ssh-control/` exists with mode `700` and holds a `cm-*` socket during the apply.
- [ ] **Stage markers.** The apply output shows `STAGE START` / `STAGE OK` for `ssh_probe`, `file_transfer`, and `remote_orchestrator`. The on-host log `/home/ec2-user/tower-installer-logs/apply-<UTC>.log` shows the same markers for each Ansible stage.
- [ ] **`STAGE FAILED` on error.** Break one playbook on purpose (for example, a bad task in `03`). The on-host log prints `==== STAGE FAILED: <stage> (exit=<n>) ====` and the apply fails.
- [ ] **VM pipeline gate.** With `flag_vm_copy_files_to_instance = false`, `terraform plan` shows neither `null_resource.allow_file_copy_to_start` nor `null_resource.configure_vm`.
- [ ] **Seqerakit gate.** With `flag_run_seqerakit = false`, `assets/target/seqerakit/setup.yml` has no `compute-envs:` block.

### SSM Session Manager (add-ssm-to-ec2-boot-script)

- [ ] **Boot log.** `/var/log/tower-forge.log` shows `amazon-ssm-agent` installed with no errors, and the script continues to the `python3-pip` step.
- [ ] **Agent running.** On the host, `systemctl is-active amazon-ssm-agent` prints `active`.
- [ ] **Instance registered.** The instance shows as `Online` in Systems Manager → Fleet Manager.
- [ ] **Session works.** `aws ssm start-session --target <instance-id>` opens a shell as `ssm-user`.
- [ ] **Five actions are enough.** The role has only `AllowSSMSessionManagerAgent` (no `ec2messages:*`), and the agent still registers. If it doesn't, check `/var/log/amazon/ssm/amazon-ssm-agent.log` for `AccessDenied`.
- [ ] **No account-wide parameter read.** From an SSM session, `aws ssm get-parameter --name <a parameter outside /seqera/<app_name>/ and /config/<app_name>>` fails with `AccessDenied`.
- [ ] **Installer secrets still readable.** From the same session, `aws ssm get-parameter --name /seqera/<app_name>/db-master-user --with-decryption` succeeds. The new statement didn't break the existing scoped access.
- [ ] **Access is controlled by the account.** A principal without `ssm:StartSession` gets `AccessDeniedException` from `aws ssm start-session`. A principal with it gets a shell.
- [ ] **`ssm-user` has `sudo`.** In a session, `sudo -n true` succeeds. This confirms the root-equivalent access documented in Design Decision 22.
- [ ] **Port forwarding.** `aws ssm start-session --target <instance-id> --document-name AWS-StartPortForwardingSession --parameters portNumber=8000,localPortNumber=8000` reaches the Platform frontend at `http://localhost:8000`.

### Images (update-platform-and-studio-images)

- [ ] **All images pull.** `docker compose pull` on the host succeeds for `backend`, `cron`, `migrate-db` (`v26.2.0-RC16`), `frontend` (`v26.2.0-RC16`, no `-unprivileged` suffix), `connect-proxy` / `connect-server` (`0.14.0`), `wave-lite` (`v1.38.0`), and `groundswell` (`pipeline-optimization:0.4.15`).
- [ ] **Frontend without the suffix.** The v26.2 default `frontend` image serves the UI on port `8000` (compose maps `8000:8000`), and the Platform UI loads through the ALB.
- [ ] **New Studio templates.** Each 0.14.0 template (VSCode 1.105.1, Jupyter 4.6.0, RStudio 2026.01.2, Xpra 6.3.6) shows as `recommended` and starts a session.
- [ ] **Deprecated Studio templates.** Each 0.12.2 template shows as `deprecated` and still starts a session.
- [ ] **Studios SSH with Connect 0.14.0.** With `flag_enable_data_studio_ssh = true`, an SSH connection to a running Studio works.
- [ ] **Random OIDC registration token.** `grep -h REGISTRATION ~/target/tower_config/{tower,data-studios}.env` shows the same 32-character value in both files, not `ipsemlorem`, and Studios open. After a second `terraform apply`, the value is unchanged.
- [ ] **Path routing with Connect 0.14.0.** With `flag_studio_enable_path_routing = true`, `make verify` passes (the `0.8.2` string-comparison bug is fixed), and VSCode, Jupyter, and RStudio sessions open.
- [ ] **Wave-Lite v1.38.0.** `curl http://localhost:9099/service-info` on the host returns a `serviceInfo.version` of `1.38.0`. Also check whether v1.38.0 needs new settings such as `wave.capabilities` (open question in #435).
- [ ] **Pre-v26.2 frontend suffix.** With `tower_container_version = "v26.1.3"`, the rendered `docker-compose.yml` uses `frontend:v26.1.3-unprivileged`, and that tag pulls.
- [ ] **Groundswell 0.4.15 on Platform v26.2.** Groundswell starts, and pipeline optimization shows in the Platform UI for a workspace.
- [ ] **`make verify` with template defaults.** With `TEMPLATE_terraform.tfvars` defaults filled in, `make verify` passes. Version checks in `check_configuration.py` now compare numerically, and `v26.2.0-RC16` counts as v26.2.0.

### Telemetry (enable-augmented-telemetry)

The fresh stack uses the default (`standard`). For the `air-gapped` checks, set `flag_enable_standard_telemetry = "air-gapped"` and apply again. That also covers the mode-switch checks below.

- [x] **Variable names.** The `TOWER_TELEMETRY_*` and `TOWER_CRON_USAGE_METRICS_FILE_COLLECTOR_FILE_COLLECTOR_*` names match the v26.2 release notes, including the doubled `FILE_COLLECTOR_FILE_COLLECTOR`. Confirmed 2026-09-29.
- [ ] **`standard` (default).** `tower.env` has `TOWER_TELEMETRY_STANDARD_ENABLED=true` and `TOWER_TELEMETRY_BASIC_ENABLED=true`, Platform starts, and Seqera receives standard telemetry for the instance.
- [ ] **`basic`.** `TOWER_TELEMETRY_STANDARD_ENABLED=false`. Platform starts, and only basic telemetry arrives.
- [ ] **`air-gapped`: host folder.** After apply, `/home/ec2-user/.tower/usage-metrics` exists with mode `777`, and `docker inspect ec2-user-cron-1` shows it mounted at `/usage-metrics`.
- [ ] **`air-gapped`: files written.** After the first collection run (up to 24h, or sooner if Platform runs it at startup), usage-metric files appear in `/home/ec2-user/.tower/usage-metrics` on the host.
- [ ] **`air-gapped`: files survive an apply.** A second `terraform apply` (which replaces `~/target`) leaves the files in place.
- [ ] **`air-gapped`: 90-day history.** Files older than 90 days are pruned. This is long-running; confirm by setting the host clock or by checking Platform's collector logs.
- [ ] **`air-gapped` with Studios on.** `docker inspect ec2-user-cron-1` shows both the `data-studios-rsa.pem` mount and the `/usage-metrics` mount, and `cron` starts.
- [ ] **`air-gapped` with no route to Seqera.** Both telemetry flags stay `true` in this mode (by design). With outbound traffic to Seqera blocked (security group or NACL), Platform and `cron` keep running, telemetry failures only appear as log lines, and usage-metric files are still written.
- [ ] **Switch `standard` → `air-gapped` on a running stack.** The next apply creates the host folder, recreates `cron` with the new mount, and the collector starts writing files.
- [ ] **Switch `air-gapped` → `standard`.** The next apply recreates `cron` without the mount. `/home/ec2-user/.tower/usage-metrics` and its files stay on the host (nothing deletes them), and the collector is off (`…FILE_COLLECTOR_ENABLED=false`).

### Preflight checks (add-preflight-check-flag)

- [ ] **`true` (default).** `tower.env` has `TOWER_PREFLIGHT_CHECK_ENABLED=true` and `TOWER_CREDENTIALS_VALIDATION_ENABLED=true`. Launching a pipeline with deliberately bad credentials fails at launch with a credential-validation error, not later in the run.
- [ ] **`false`.** Both variables are `false`, and the same bad-credential launch is no longer blocked at launch.
- [ ] **Credential validation on save.** With the flag `true`, adding a credential with bad keys in the Platform UI is rejected. With `false`, the same credential is accepted.
- [ ] **Switch on a running stack.** Flip the flag and apply. `docker exec ec2-user-backend-1 env | grep -E 'PREFLIGHT|CREDENTIALS_VALIDATION'` shows the new values in both `backend` and `cron`, so the containers were recreated with the new `tower.env`.
- [ ] **Seqerakit with validation on.** With `flag_run_seqerakit = true` and the flag `true`, the `seqerakit` stage of the apply still succeeds. The credentials it creates pass validation, or the stage fails with a clear credential error, not a silent partial setup.

### Pipeline secrets KMS key (schaluva/26-2-customer-managed-key, PR #444)

Needs an AWS Batch compute environment and a pipeline that uses pipeline secrets. Create a customer-managed key in the compute environment's account and region. Give the compute environment credentials `kms:GenerateDataKey` and `kms:Decrypt` on it, and the execution role `kms:Decrypt`.

- [ ] **Empty (default).** `tower.env` has `# TOWER_AWS_SECRETS_KMS_KEY_ID_NOT_SET=DO_NOT_UNCOMMENT`. A pipeline run's temporary Secrets Manager secret uses the AWS-managed key (`aws secretsmanager describe-secret` shows no customer `KmsKeyId`).
- [ ] **Key ARN.** With `tower_aws_secrets_kms_key_id = "arn:aws:kms:<region>:<account>:key/<id>"`, Platform starts, the run succeeds, and the temporary secret's `KmsKeyId` is that key.
- [ ] **Key ID and multi-Region key.** A bare key ID (lowercase UUID) and an `mrk-…` ID are both accepted by `terraform plan`. Platform starts with each of them, confirming that the `variables.tf` regex matches Platform's own pattern.
- [ ] **Existing compute environments.** A compute environment created before the key was set picks up the installation-wide key on its next run, as the CHANGELOG states.
- [ ] **Compute-environment key wins.** A compute environment with its own key (Advanced options > Pipeline secrets KMS key) uses its own key, not the installation-wide one.
- [ ] **Missing KMS permissions.** With `kms:Decrypt` removed from the execution role, the run fails with a clear KMS `AccessDenied` error, not a silent hang.
- [ ] **Compute environment in another account or region.** With the installation-wide key set, a compute environment in a different account or region (and no key of its own) fails its run with a clear KMS error. This confirms the template advice to set the key only when every such compute environment shares the key's account and region.
- [ ] **Version gate.** With a key set, `make verify` passes on `v26.2.0-RC16` and fails on `v26.1.3` with "can only be set on Platform v26.2.0+". The pre-release tag counts as v26.2.0.

### Studios via private CA (support-private-certs-in-studio-images)

Needs `flag_use_private_cacert = true` (private CA set up per `documentation/setup/optional_private_certificates.md`), `flag_run_studios_via_private_ca = true`, and Studios on.

- [ ] **Containers start with the CA.** `backend` and `cron` start. `docker exec ec2-user-backend-1 head -1 /private-ca/rootCA.crt` prints `-----BEGIN CERTIFICATE-----`, and `docker exec ec2-user-backend-1 env | grep TOWER_SSL_CUSTOM_CA_CERT_FILE` shows `/private-ca/rootCA.crt`. Same in `cron`.
- [ ] **Studio trusts the CA.** In a 0.14.0 Studio session, `curl https://<a host with a private-CA-signed cert>` succeeds without `-k` or TLS errors.
- [ ] **Old Studio image doesn't trust the CA.** A 0.12.2 Studio session fails TLS to the same host. This matches the `make verify` warning for images below Connect 0.13.0.
- [ ] **DER `rootCA.crt` is rejected.** With a DER-encoded `rootCA.crt` (fresh host, or the anchors copy removed), the apply fails at "Check the private root CA is PEM-encoded." with the `openssl x509 -inform der …` hint, before any container starts.
- [ ] **`make verify` errors.** With the flag on, `make verify` exits with an error in each case: `flag_use_private_cacert = false`, `tower_container_version = "v26.1.3"`, and `data_studio_container_version = "0.12.1"`.
- [ ] **`make verify` warnings.** With the template's Studio templates, `make verify` warns once for each `*-0-12-2` template (below Connect 0.13.0) and not for the 0.14.0 ones. A custom image tag without a Connect suffix gets the "cannot read a Connect version" warning.
- [ ] **Flag on without the private CA.** With `flag_run_studios_via_private_ca = true` and `flag_use_private_cacert = false` (skipping `make verify`), the backend still starts: neither the mount nor `TOWER_SSL_CUSTOM_CA_CERT_FILE` is written.

### Wave-Lite configuration (update-wave-configuration)

Needs `flag_use_wave_lite = true`. `wave-lite.yml.tpl` sets `anonymous-access: false`. The other three capability toggles stay `true`.

- [ ] **Starts with the 1.38 config.** With the new `wave.capabilities`, `micronaut.executors` / `stream-pool`, and `logger` blocks, `wave-lite` starts with no config errors in `docker logs`, and `service-info` responds. `test_wave_containers` (`make run_tests_containers_only`) covers the same start-up locally, and passed on 2026-09-30 after two fixes: a retry bug that had hidden every failure, and `wait=False` (see the podman note below).
- **Podman users (`DOCKER_HOST` pointing at the podman socket):** run the container tests with `PODMAN_COMPOSE_PROVIDER=/usr/local/bin/podman-compose` (or set `compose_providers` in `~/.config/containers/containers.conf`). Without it, `docker compose` falls through to the old `docker-compose` 1.29.2, which starts nothing, and the test fails with `Connection refused` on port 9099. A shell function that maps `docker compose` to podman-compose doesn't help, because `testcontainers` doesn't run through your shell.
- [ ] **Anonymous calls rejected.** A request to Wave-Lite without a Platform token is refused. For example, a Nextflow run outside Platform with `wave.enabled = true`, `wave.endpoint` set to Wave-Lite, and no `tower.accessToken` fails with an authentication error, not a pull.
- [ ] **Platform-launched pipelines still work.** A pipeline launched from Platform with Wave on pulls its containers through Wave-Lite, because Platform presents its token.
- [ ] **Nextflow with a Platform token works.** The same run from outside Platform, with `tower.accessToken` set, succeeds.
- [ ] **Studios with Wave-Lite.** With Studios and Wave-Lite on, a Studio that uses a Wave-built or augmented image still starts, so the token is passed on that path too.
- [ ] **Trace noise gone.** `docker logs` for `wave-lite` shows no `Slow method detected` DEBUG lines.
- [ ] **Large pulls through the stream pool.** A pipeline that pulls a large image through Wave-Lite completes, and layer downloads don't time out.
- [ ] **Seqera-hosted Wave unaffected.** With `flag_use_wave = true` (Seqera-hosted Wave, not Wave-Lite), nothing changes. `wave-lite.yml` isn't used.

### Data lineage (lineage-updates)

Needs a public HTTPS deployment (ALB with a public certificate). See Design Decision 23.

- [ ] **`-1` keeps lineage off.** With `flag_enable_data_lineage = false` on v26.2, `tower.env` has `TOWER_LINEAGE_ALLOWED_WORKSPACES=-1`, Platform starts, and no workspace can turn lineage on. If Platform rejects `-1`, record the error: `-1` is not a documented value.
- [ ] **All workspaces.** With lineage on and `allowed_workspaces = ""`, a workspace in Automatic mode creates a `<store_prefix>-*` bucket and SNS topic, **Event delivery** shows **Active**, and run records appear.
- [ ] **Restricted.** With `allowed_workspaces = "<id>"`, only that workspace offers lineage.
- [ ] **IAM by version.** The `<global_prefix>_policy_lineage` policy has 5 statements on v26.2 and 2 on `v26.1.3`.
- [ ] **Custom `store_prefix`.** With a prefix other than `seqera-lineage`, Platform creates the bucket and topic under the new prefix with no `AccessDenied`.
- [ ] **SNS retries.** Stop `backend` for about 2 minutes during a run. Events sent in that time arrive after the restart.
- [ ] **`global_search_enabled = false`.** Global search is hidden in the UI.
- [ ] **Verify failures.** With lineage on, each setting in `LINEAGE_SNS_BLOCKERS` (`check_configuration.py`) fails `make verify` on v26.2 and passes on `v26.1.3`.
- [ ] **Restricted ingress.** With `sg_ingress_cidrs` narrowed, `make verify` warns. Record whether SNS delivery still works.
- [ ] **Off-state warning.** With lineage off, `make verify` prints the `-1` warning on v26.2 and not on `v26.1.3`. On `v26.1.3`, `tower.env` has `# TOWER_LINEAGE_NOT_ENABLED=DO_NOT_UNCOMMENT` instead of `-1`.

### Actions triggers (`tower_actions`)

Bucket-event checks need a public HTTPS deployment (ALB with a public certificate), `flag_data_explorer_enabled = true`, and an S3 data link whose credential has `s3:Get/PutBucketNotificationConfiguration` and `sns:CreateTopic/SetTopicAttributes/Subscribe/DeleteTopic`.

- [ ] **Defaults.** With the template values, `tower.env` has the three `# TOWER_ACTIONS_*_TRIGGER_ALL_WORKSPACES=DO_NOT_UNCOMMENT` markers, `TOWER_ACTIONS_TRIGGER_RATE_MAX_PER_WINDOW=20`, and `TOWER_ACTIONS_TRIGGER_RATE_WINDOW=1h`. The bucket, schedule, and pipeline-run triggers are offered in every workspace, including a personal workspace.
- [ ] **`"-1"` turns a trigger off.** With each `*_allowed_workspaces = "-1"` in turn, that trigger is no longer offered in any workspace, and the other two still are. The installer uses `-1` to match lineage and WIF. Platform documents `0` for Actions, not `-1`, so if Platform rejects `-1` or treats it as "all workspaces", record it.
- [ ] **Old `"0"` value.** With `bucket_trigger_allowed_workspaces = "0"` (a value from pre-release branches), `terraform plan` passes, the bucket trigger is off (Platform documents `0`), and `make verify` still prints the bucket-trigger warnings, because only `"-1"` skips them.
- [ ] **Restricted list.** With `cron_trigger_allowed_workspaces = "<id>"`, only that workspace offers the schedule trigger.
- [ ] **Restricting pauses existing Actions.** Create a schedule Action in workspace A, then restrict the schedule trigger to workspace B and apply. The Action in A shows as paused, and it resumes when A is allowed again.
- [ ] **Other Action types unaffected.** With all three triggers set to `"-1"`, GitHub webhook and Tower launch hook Actions still work.
- [ ] **Rate limit.** With `trigger_rate_max_per_window = 2` and `trigger_rate_window = "1h"`, a schedule Action that fires every minute is paused after its second launch, and resuming it in the UI works.
- [ ] **Bucket event fires.** Creating the marker file (for example `*.done`) in the watched data repository launches the pipeline. Platform creates the bucket notification and SNS topic, and deleting the Action removes them.
- [ ] **Pipeline-run event fires.** An Action watching a Launchpad pipeline launches its target when the watched run succeeds, fails, or is cancelled, as configured.
- [ ] **`make verify` warnings.** With the bucket trigger on, `make verify` warns for each of `flag_do_not_use_https`, `flag_private_tower_without_eice`, `flag_make_instance_private`, and `flag_use_private_cacert`, and when `flag_data_explorer_enabled = false`. There are no warnings with `bucket_trigger_allowed_workspaces = "-1"` or on `v26.1.3`.
- [ ] **Bucket trigger over HTTP.** On an HTTP-only site (skipping `make verify`), a new bucket-event Action moves to **Error** because AWS rejects the SNS subscription, as the Platform docs describe.
- [ ] **Pre-v26.2 Platform.** On `v26.1.3`, the `TOWER_ACTIONS_TRIGGER_RATE_*` lines are still written (they aren't version-gated), and Platform starts and ignores them.

### Audit log (update-audit-configuration)

- [ ] **Write-mode marker.** On v26.2, `tower.env` has `# TOWER_AUDIT_LOG_V2_WRITE_MODE=NOT_AVAILABLE_DO_NOT_UNCOMMENT` and no active `TOWER_AUDIT_LOG_V2_WRITE_MODE` line. On `v26.1.3`, it has `TOWER_AUDIT_LOG_V2_WRITE_MODE=dual`.
- [ ] **v2 only.** After a few audited actions (sign in, create a pipeline), the events appear in the Admin panel **Audit logs** v2 view and in `/admin/audit-logs-v2`, and no new rows appear in `tw_audit_log` (`SELECT MAX(id) FROM tw_audit_log` doesn't change).
- [ ] **CSV export.** The v2 CSV export (`/admin/audit-logs-v2/export-csv`) works, and `csv_export_max_logs` caps the row count.
- [ ] **`make verify` warning.** On v26.2, `write_mode = "dual"` (the template default) prints the "is ignored" warning, and `"v2"` prints nothing. There is no warning on `v26.1.3`.
- [ ] **`"v1"` rejected.** With `write_mode = "v1"`, `terraform plan` fails with `tower_audit_log_v2.write_mode must be one of: "v2", "dual".`
- [ ] **Cleanup still covers both tables.** With a short retention period (for example `tower_audit_retention_days = 1` on a test site), the cleanup cron deletes old rows from both `tw_audit_log` and the v2 table.
- [ ] **Service-account actor.** An action taken with a service account token shows a `service_account` actor in the v2 log. Record whether the service-accounts feature flag is needed.

### Workload identity federation (add-workload-federation-feature)

Needs a public HTTPS deployment (ALB with a public certificate). For AWS, an IAM OIDC provider for `https://<tower_server_url>/api` and a role that trusts it (`sts:AssumeRoleWithWebIdentity` and `sts:TagSession`). For Google, a workload identity pool and provider. See `documentation/setup/optional_workload_identity_federation.md` and Design Decision 24.

**Facts to record for Design Decision 24.** These are undocumented, so write down what you observe:

- [ ] **Token audience.** Record the `aud` claim Platform puts in AWS WIF tokens (CloudTrail `AssumeRoleWithWebIdentity` event, or the value the IAM OIDC provider's client ID must match). Needed before the installer could ever create the OIDC provider.
- [ ] **Token subjects.** Record the exact `sub` values seen for each workload (`platform`, `data`, `studio`, `workflow`), and the session tags (`seqera:org`, `seqera:workspace`, `seqera:user`, `seqera:workload`).
- [ ] **Issuer string.** `curl https://<tower_server_url>/api/.well-known/openid-configuration` returns an `issuer` of exactly `https://<tower_server_url>/api` (no trailing slash), and a `jwks_uri` under `/api/.well-known/`. STS compares the issuer as an exact string.

**Installer configuration (switches and the OIDC key):**

- [ ] **`-1` keeps WIF off.** With `tower_identity_federation_enabled = false`, `tower.env` has `TOWER_IDENTITY_FEDERATION_ALLOWED_WORKSPACES=-1`, Platform starts, and the WIF option isn't offered when creating an AWS or Google credential. If Platform rejects `-1`, record the error: `-1` is not a documented value.
- [ ] **Studios off, WIF off.** `tower.env` has `# TOWER_OIDC_PEM_PATH_NOT_SET=DO_NOT_UNCOMMENT`, `backend` and `cron` have no `/data-studios-rsa.pem` mount, and Platform starts. Record the "pem path unconfigured" startup warning, which is expected and harmless here.
- [ ] **Studios on, WIF off.** Studios still works (the key is still set), and WIF stays unavailable. This is the upgrade case the explicit `-1` protects.
- [ ] **Studios off, WIF on.** `backend` and `cron` mount `/data-studios-rsa.pem`, `TOWER_OIDC_PEM_PATH` is set, there's no "pem path unconfigured" startup warning, and `curl https://<tower_server_url>/api/.well-known/jwks.json` returns an RSA key. That confirms Platform derives the public key from the private-only PEM the installer writes.
- [ ] **Empty allow-list means all workspaces.** With `tower_identity_federation_allowed_workspaces = ""`, every organization workspace offers WIF. If none do, record it: the engineering brief says an unset value disables WIF.
- [ ] **Restricted.** With `"<id>"`, only that workspace offers WIF. Personal workspaces don't.
- [ ] **Switch on a running stack.** Flip `tower_identity_federation_enabled` from `false` to `true` with Studios off and apply. `backend` and `cron` are recreated with the key mount, and WIF becomes available without any other step.
- [ ] **Switch off with WIF credentials in use.** Flip it back to `false` and apply. Record what happens to existing WIF credentials and their compute environments (rejected at launch, marked `INVALID` by preflight, or still working), and whether turning WIF on again restores them.
- [ ] **Workspace removed from the allow-list.** Create a WIF credential in workspace A, then restrict the allow-list to workspace B and apply. Record whether A's credential stops working, and what error its runs show.
- [ ] **Key recreated.** After `terraform taint tls_private_key.connect_pem && terraform apply`, new WIF exchanges and Studio sessions work without changing any trust policy or pool provider.
- [ ] **Pre-v26.2 with the flag on.** On `v26.1.3` with `tower_identity_federation_enabled = true` (skipping `make verify`), `tower.env` has no `TOWER_IDENTITY_FEDERATION_ALLOWED_WORKSPACES` line, and, with Studios off, no `TOWER_OIDC_PEM_PATH`. Platform starts.

**AWS credentials:**

- [ ] **Role ARN only.** An AWS credential with only a role ARN validates, runs a pipeline on an existing AWS Batch compute environment, and browses the work bucket in Data Explorer. CloudTrail shows `AssumeRoleWithWebIdentity` with the session named `o<org>-w<wsp>-u<user>-<workload>`.
- [ ] **Batch Forge.** Creating a new AWS Batch compute environment with Forge and a WIF credential succeeds (`TOWER_WIF_FORGE_LEGACY_MODE_ENABLED` isn't set, so Platform's default `true` applies). Record whether Forge's `TowerForge-*` roles are created as usual.
- [ ] **Trust policy scoped to one workspace.** With the trust policy's `sub` condition set to `org:<orgId>:wsp:<wspA>:*`, a credential in workspace A works and the same role ARN in workspace B fails validation with `AccessDenied`.
- [ ] **Missing `sts:TagSession`.** Without it in the trust policy, credential validation fails with a message naming `sts:TagSession`.
- [ ] **Inaccessible bucket in Data Explorer.** With a role that can't read one of the workspace's S3 data links, that bucket is left out of the Data Explorer list, and the others still show.
- [ ] **Revocation.** Remove the trust relationship from the role. The next validation fails, and runs lose access within about an hour (the credential cache ceiling). Record how long it actually takes.
- [ ] **Preflight catches a broken trust.** With preflight checks on, the scheduled validation (every 12 hours) or the **Validate** button marks the credential `INVALID` with a `Pre-flight:` message after the trust is removed.

**Google Cloud credentials:**

- [ ] **Service account and provider.** A Google WIF credential runs a pipeline on Google Cloud Batch, and Data Explorer can view and download file contents (needs `roles/iam.serviceAccountTokenCreator` on the service account). Without that role, file contents fail with a signing error and runs still work.
- [ ] **Existing Google WIF binding.** A v26.1 Google WIF credential whose binding admits only the `workflow` subject stops working once its workspace is enabled, and works again after the binding admits all subjects. Leaving the workspace out of the allow-list keeps the old `workflow` subject and the old binding working.

**Studios:**

- [ ] **Studio with WIF.** A Studio (0.14.0 image) on a WIF compute environment mounts its data using its own federated identity (CloudTrail or GCP audit logs show the `studio` subject).
- [ ] **Older Studio image.** A 0.12.2 Studio on the same compute environment: record whether it fails to mount data or falls back to the compute environment's identity. Connect client 0.14.0 is required for Studio WIF.

**Reachability and `make verify`:**

- [ ] **`make verify` errors and warnings.** WIF on fails on `v26.1.3`. On v26.2, each setting in `LINEAGE_SNS_BLOCKERS` prints the WIF warning, and WIF off prints nothing.
- [ ] **Issuer not reachable.** With `sg_ingress_cidrs` narrowed so AWS STS can't reach the ALB (`make verify` doesn't warn for this), credential validation fails. Record the error Platform shows, so the setup guide can name it.
- [ ] **Private CA site.** With `flag_use_private_cacert = true` and WIF on (skipping `make verify`), the STS exchange fails because the certificate isn't publicly trusted. Record the error.
- [ ] **Seqerakit unaffected.** With `flag_run_seqerakit = true` and WIF on, the `seqerakit` stage still succeeds with its key-based credentials. It creates no WIF credential (not supported).
- [ ] **GovCloud / China ARN.** Record whether the credential form rejects an `arn:aws-us-gov:` or `arn:aws-cn:` role ARN, as the engineering brief says.

### Version checks in `make verify` (minor-cleanup-of-extraneous-items)

`check_configuration.py` now compares versions numerically (`_is_before`). String comparison had sorted `0.14.0` before `0.8.2`. Unit tests in `tests/unit/validation/test_version_checks.py` cover the ordering; these checks confirm the real `make verify` run.

- [ ] **Studios path routing with Connect 0.14.0.** With `flag_studio_enable_path_routing = true` and `data_studio_container_version = "0.14.0"`, `make verify` passes. Before the fix, it failed with "must be at least '0.8.2'".
- [ ] **Path routing floor still enforced.** With `data_studio_container_version = "0.8.1"`, `make verify` fails with the 0.8.2 message.
- [ ] **Studios SSH warning.** With `flag_enable_data_studio_ssh = true` and `data_studio_container_version = "0.9.0"`, `make verify` warns that Connect is older than 0.10.0 (the string comparison missed this). With `"0.14.0"`, there's no warning.
- [ ] **Unreadable version.** With `data_studio_container_version = "latest"` and path routing on, `make verify` stops with "Cannot read version 'latest'", not a Python traceback.
- [ ] **Pre-release tag.** With `tower_container_version = "v26.2.0-RC16"`, the v26.2-only settings (KMS key, WIF, private-CA Studios) pass `make verify`, and the pre-v26.1 warnings (compute-environment cleanup, audit log v2) don't print.
- [ ] **v26.1.3 site.** With `tower_container_version = "v26.1.3"`, `make verify` still gives the v26.1 results: the Nextflow 26.04 parser advisory and Harbor warning print, and each v26.2-only setting set on fails.

### MySQL 8.4 and database TLS (update-database)

See Design Decision 25 and `documentation/setup/upgrade_mysql_8_4.md`. Cover both a new RDS instance and the container DB.

**Pre-merge: container DB with `--require-secure-transport=ON` (local, Docker or podman).** No automated test starts the container DB with this flag. The check confirms that MySQL generates its own certificate and that socket clients are unaffected. If any step fails, make the container flag opt-in (RDS only) before merging.

```bash
docker run -d --name tlscheck -e MYSQL_ALLOW_EMPTY_PASSWORD=yes mysql:8.4 --require-secure-transport=ON
sleep 30
docker exec tlscheck ls /var/lib/mysql/ | grep pem
docker exec tlscheck mysqladmin ping -h localhost
docker exec tlscheck mysql -uroot -h 127.0.0.1 --ssl-mode=DISABLED -e 'select 1'
docker exec tlscheck mysql -uroot -h 127.0.0.1 --ssl-mode=REQUIRED -e "show status like 'Ssl_cipher'"
docker rm -f tlscheck
```

- [ ] **Certificate generated.** The `ls` lists `ca.pem`, `server-cert.pem`, and `server-key.pem`.
- [ ] **Socket clients unaffected.** `mysqladmin ping -h localhost` prints `mysqld is alive`. The compose healthcheck, the Groundswell SQL step, and `get_access_token.py` (container case) all connect this way.
- [ ] **Plaintext TCP refused.** The `--ssl-mode=DISABLED` query fails with `Connections using insecure transport are prohibited while --require_secure_transport=ON`.
- [ ] **TLS over TCP works.** The `--ssl-mode=REQUIRED` query prints a non-empty `Ssl_cipher`. This is the path Platform uses (`useSSL=true&trustServerCertificate=true` accepts the self-signed certificate).

**Facts to record:**

- [ ] **Authentication plugin.** On a fresh RDS 8.4 instance and on an instance upgraded from 8.0, record the output of `SELECT user, plugin FROM mysql.user;` and `SHOW VARIABLES LIKE 'authentication_policy';`. The Platform and Groundswell users must be able to log in with whichever plugin they have.

**Fresh deployment (8.4, `db_enforce_tls = true`):**

- [ ] **Platform connects with TLS.** `tower.env` has `TOWER_DB_URL=…?useSSL=true&trustServerCertificate=true&permitMysqlScheme=true`, Platform starts, and `SELECT * FROM performance_schema.status_by_thread WHERE VARIABLE_NAME = 'Ssl_version';` (or `SHOW STATUS LIKE 'Ssl_cipher'` from a Platform-user session) shows TLS on Platform's connections.
- [ ] **Plaintext refused (RDS).** `mysql --ssl-mode=DISABLED -h <rds-endpoint> -u <user> -p` fails with `Connections using insecure transport are prohibited while --require_secure_transport=ON`. The RDS parameter group has `require_secure_transport = 1`.
- [ ] **Plaintext refused (container DB).** `docker exec ec2-user-db-1 mysql --ssl-mode=DISABLED -u root -e 'select 1'` fails with the same error, and `docker inspect ec2-user-db-1` shows `--require-secure-transport=ON`.
- [ ] **DB population works with TLS.** On a new RDS instance, the "Populate RDS" and "Populate Groundswell" steps succeed with the `mysql:8.4` client.
- [ ] **Groundswell with TLS.** With Groundswell on, it starts and connects. If it can't, record the error: `make verify` already warns about this, and the workaround is `db_enforce_tls = false`.
- [ ] **Access token helper.** With `flag_run_seqerakit = true`, the step that runs `get_access_token.py` reads the token successfully from an RDS 8.4 instance that refuses plaintext. It still uses a `mysql:8.0` client, which negotiates TLS by default.
- [ ] **TLS off.** With `db_enforce_tls = false`, `TOWER_DB_URL` has `useSSL=false`, the parameter group has no `require_secure_transport`, and plaintext connections succeed.

**Upgrade an existing 8.0 deployment (the runbook):**

- [ ] **RDS: replacement guard.** With the runbook's step 3 values, `make check_db_replacement` prints `update` for `module.rds[0].module.db_instance.aws_db_instance.this[0]` and ends with `OK`. Also confirm it fails if you change something that forces a replacement (for example, `db_enable_storage_encrypted`) — then revert.
- [ ] **RDS: in-place upgrade.** `make apply` upgrades the instance in about 10 minutes. The instance identifier and endpoint are unchanged, `describe-db-instances` reports an 8.4 version, new `mysql8.4` parameter and option groups are attached, and the old 8.0 groups are deleted.
- [ ] **RDS: data intact.** After the upgrade, Platform shows the same workspaces, pipelines, and run history.
- [ ] **RDS: failed precheck.** Record what happens if the prechecks fail (for example, on a copy with an incompatible object): the upgrade is cancelled, the instance stays on 8.0, and `PrePatchCompatibility.log` names the problem.
- [ ] **RDS: switches back off.** After setting both upgrade switches to `false`, the next `terraform plan` shows no RDS changes.
- [ ] **Container DB upgrade.** After backing up `~/.tower/db/mysql` and setting `db_container_engine_version = "8.4"`, the `db` container starts on 8.4, converts the data files, and Platform shows existing data. Restoring the backup onto `mysql:8.0` brings the old state back.
- [ ] **Container DB certificate after the upgrade.** On that upgraded container, `ls ~/.tower/db/mysql/*.pem` on the host shows the certificate files (created by 8.0 at first start, or by 8.4 if missing), `docker compose ps` shows `db` as `healthy`, and Platform connects with TLS.
- [ ] **8.0 site untouched.** A 1.8.x site that keeps `db_engine_version = "8.0"` gets no database changes from the 1.9.0 apply, keeps the plaintext `TOWER_DB_URL`, and `make verify` warns that 8.0 is unsupported on Platform v26.1+.
- [ ] **Mismatched parameter group.** `db_engine_version = "8.4"` with `db_param_group = "mysql8.0"` fails `make verify`.

### Databases (#434)

- [ ] **New external RDS, first apply.** `tower` and `swell` databases and users exist. Tower and Groundswell start.
- [ ] **New external RDS, second apply.** The "Populate RDS" and "Populate Groundswell" steps succeed with no MySQL errors (the `|| true` suffixes are gone, so an error would fail the apply).
- [ ] **Container DB with Groundswell.** On every apply, the `05` step `docker exec ec2-user-db-1 … < init.sql` succeeds. This confirms the container is still named `ec2-user-db-1`.
- [ ] **Groundswell turned on after the first deploy.** Deploy with `flag_enable_groundswell = false`, then set it to `true` and apply. The `swell` database and user get created, and Groundswell starts.
- [ ] **Wave-Lite RDS re-run.** The second apply runs "Populate Wave Lite Postgres" without errors, and Wave-Lite still connects.

## Password sync (#434)

- [ ] **Tower.** Change `TOWER_DB_PASSWORD` in the tower SSM secret, then apply. Tower connects to the DB with the new password.
- [ ] **Groundswell.** Same test with `SWELL_DB_PASSWORD`.
- [ ] **Wave-Lite.** Same test with `WAVE_LITE_DB_LIMITED_PASSWORD` (RDS). The `ALTER ROLE` line resets the password.
- [ ] **Password changed in the DB.** Change the Tower DB user's password directly in MySQL, then apply. The next apply resets it to the SSM value, and Tower connects.

## Existing deployment upgrade (1.8.x → 1.9.0)

- [ ] **HIGH PRIORITY: active Studio across the registration-token change.** The first 1.9.0 apply replaces the hard-coded `ipsemlorem` OIDC registration token with a random value. Before the apply, start a Studio session and keep it open. After the apply:
  - `tower.env` and `data-studios.env` hold the same new token (`grep -h REGISTRATION ~/target/tower_config/{tower,data-studios}.env`).
  - `connect-proxy` logs show a successful OIDC client registration, with no `401` or `invalid_token`.
  - The already-running Studio still opens in the browser. If it doesn't, check whether stopping and starting it fixes it, and record which.
  - A new Studio starts and opens.
  - Studios SSH (if on) still connects to the running session.
  - Record whether the old client registration is left in Platform's database, and whether that causes any error.

- [ ] **Module path moved (`connection_strings` v2.0.0 → v2.1.0).** On an existing checkout, `terraform plan` before `terraform init` stops with "Module not installed" (no changes made). After `terraform init`, the plan shows no resource changes from the move.
- [ ] **Provider pins.** On an existing site with its own `.terraform.lock.hcl`, `terraform plan` works without `terraform init -upgrade`.
- [ ] **Fresh checkout.** `terraform init` on a clean clone resolves `null` 3.x, `random` 3.x, and `tls` 4.x.
- [ ] **New `flag_enable_standard_telemetry`.** A 1.8.x `terraform.tfvars` without it fails `terraform plan` with "No value for required variable", and `make check_upgrade` lists it as required-missing with the template value `"standard"`.
- [ ] **New `flag_enable_preflight_checks`.** A 1.8.x `terraform.tfvars` without it fails `terraform plan` with "No value for required variable", and `make check_upgrade` lists it.
- [ ] **New `tower_aws_secrets_kms_key_id`.** A 1.8.x `terraform.tfvars` without it fails `terraform plan` with "No value for required variable". `make check_upgrade` lists it with the template value `""`, and adding `""` keeps the AWS-managed key.
- [ ] **New `tower_actions`.** A 1.8.x `terraform.tfvars` without it fails `terraform plan` with "No value for required variable", and `make check_upgrade` lists it as required-missing. Adding the template block keeps Platform's defaults.
- [ ] **Actions on after the upgrade.** With the template `tower_actions` block, all three new triggers are offered in every workspace after the upgrade to v26.2, including personal workspaces. Existing GitHub webhook and Tower launch hook Actions still work.
- [ ] **New `flag_run_studios_via_private_ca`.** A 1.8.x `terraform.tfvars` without it fails `terraform plan` with "No value for required variable", and `make check_upgrade` lists it with the template value `false`.
- [ ] **Removed `data_lineage_allowed_workspaces`.** A 1.8.x `terraform.tfvars` fails `terraform plan` until `data_lineage_options` is added. `make check_upgrade` lists `data_lineage_options` as required-missing and `data_lineage_allowed_workspaces` as an extra variable.
- [ ] **Lineage off, 1.8.x → 1.9.0 on v26.2.** Lineage stays off in every workspace after the upgrade.
- [ ] **Lineage on, v26.1 → v26.2 with `migrate_sqs_transport = true`.** The migration converts each Automatic-mode workspace, the old SQS queue is deleted, and each lineage settings page shows no errors.
- [ ] **`migrate_sqs_transport = false`.** No migration runs, and each v26.1 lineage workspace is flagged for manual conversion.
- [ ] **Removed `tower_server_port`.** With the old line still in `terraform.tfvars`, `terraform plan` prints only the non-fatal "Value for undeclared variable" warning. `make check_upgrade` reports it as an extra variable.
- [ ] **No-op refactors.** After the tflint clean-up (removed locals, duplicate map keys, `timestamp()` without interpolation), `terraform plan` shows no infrastructure changes except the new SSM IAM statement.
- [ ] **SSM IAM plan diff.** `terraform plan` shows an in-place update to the EC2 role's main policy (`aws_iam_policy.main_policy`) that adds `AllowSSMSessionManagerAgent`, and no instance replacement.
- [ ] **SSM IAM in place.** The IAM change applies on the next `terraform apply`. On the running instance, `sudo dnf install -y amazon-ssm-agent && sudo systemctl enable --now amazon-ssm-agent`, then start a session.
- [ ] **Platform v26.1.3 → v26.2.0-RC16.** The `migrate-db` container completes the DB migration, and `backend` and `cron` start. Existing workspaces, pipelines, and run history are intact.
- [ ] **Frontend tag switch.** The upgrade replaces `frontend:v26.1.3-unprivileged` with `frontend:v26.2.0-RC16`, and the UI still loads on port `8000`.
- [ ] **Connect 0.11.0 → 0.14.0.** After the upgrade, `connect-proxy` and `connect-server` run `0.14.0`, and Studios still open through the proxy.
- [ ] **Wave-Lite v1.33.0 → v1.38.0.** Wave-Lite starts against its existing database (container or RDS) without schema errors, and `service-info` reports `1.38.0`.
- [ ] **Wave-Lite anonymous access turned off.** On an upgraded site, Nextflow clients that used Wave-Lite without a Platform token stop working after the upgrade. Record the error they see, so the CHANGELOG can tell upgraders what to expect.
- [ ] **Old `data_studio_options` block kept.** A site that upgrades but keeps its 1.8.x `data_studio_options` block still renders, starts, and lists its old templates. Copying the new block is recommended, not required.
- [ ] **Removed 0.11.0 Studio templates.** On a site upgraded from 1.8.x, existing Studios created from the removed `*-0-11-0` templates still show in the UI and can be stopped and deleted. Record whether they can still start.
- [ ] **New WIF variables.** A 1.8.x `terraform.tfvars` without `tower_identity_federation_enabled` and `tower_identity_federation_allowed_workspaces` fails `terraform plan`, and `make check_upgrade` lists both.
- [ ] **Audit log v1 history after the upgrade.** On a v26.1 site in `dual` mode, upgrade to v26.2. Pre-upgrade events stay visible in the Admin panel's legacy table view, and post-upgrade events appear only in the v2 view. The upgrade doesn't fail on the old `write_mode` value.
- [ ] **Docker group on an old instance.** `id ec2-user` still lists `docker`. The group came from earlier Ansible runs; the Ansible tasks that added it were removed in 1.9.0.

## Other topologies

- [ ] **Existing external DB with valid master credentials.** Re-runs succeed, and passwords sync.
- [ ] **Existing external DB with placeholder master credentials.** The apply now fails at "Populate RDS". Check that the error makes the cause clear. This is the expected behaviour change.
- [ ] **Private instance behind a NAT.** Session Manager works with no VPC endpoints.
- [ ] **Private instance without a NAT.** With `ssm` and `ssmmessages` in `vpc_interface_endpoints_tower`, Session Manager works.
- [ ] **Private instance without the SSM endpoints.** Where the instance has package-repo access (S3 gateway endpoint) but no NAT and no `ssm` / `ssmmessages` endpoints, the agent installs but stays offline in Fleet Manager. This confirms the documented endpoint requirement. `pip install ansible-core` also needs egress to PyPI, so a site like this needs its own egress path.
- [ ] **Pre-existing IAM role** (`flag_iam_use_prexisting_role_arn = true`). Without the five SSM actions, the agent doesn't register. After you add them to the role, it registers.
- [ ] **Custom launch template** (client vendoring branch). A copy of `launch_template_ec2.tpl` that lacks the `groupadd` / `usermod` lines leaves `ec2-user` without the `docker` group, and Ansible fails. Confirms the CHANGELOG warning.

## After v26.2.0 GA (follow-up to `TODO(#435)`)

- [ ] **GA tag.** With `tower_container_version = "v26.2.0"` (template and `generate_core_data.sh` bumped, baseline frontend image updated), all Platform images pull, `frontend:v26.2.0` has no suffix, and an RC16 site upgrades to GA cleanly.
