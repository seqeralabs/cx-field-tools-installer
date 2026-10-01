# Upgrade the Platform database from MySQL 8.0 to 8.4

Platform v26.1 and later support only officially support RDS MySQL 8.4. This runbook upgrades an existing deployment in place: the RDS instance or container database keeps its data, name, and endpoint.

See Design Decision 25 in [design_decisions.md](../design_decisions.md) for why the upgrade works this way.

## What changes

- The engine version moves from 8.0 to 8.4, and the RDS parameter and option groups move to their 8.4 families.
- With `db_enforce_tls = true` (the template default), Platform connects with TLS, and the database refuses plaintext connections. On RDS, Platform and Groundswell verify the server certificate against the Amazon RDS CA bundle, which Ansible downloads to the instance. The instance needs outbound HTTPS to `truststore.pki.rds.amazonaws.com`.
- The upgrade can't be reversed. RDS rolls back only if the upgrade itself fails.

## Before you start

- Plan a maintenance window. An RDS upgrade typically takes about 10 minutes, and Platform can't reach the database during it.
- Confirm that you run installer 1.9.0 or later, and that `make check_upgrade` reports no missing variables.

## Upgrade an RDS database

1. Make sure the instance can't be deleted by mistake. In `terraform.tfvars`, set `db_deletion_protection = true`, then run `terraform apply`.
2. Take a manual snapshot:

   ```bash
   aws rds create-db-snapshot \
     --db-instance-identifier DB_INSTANCE_ID \
     --db-snapshot-identifier DB_INSTANCE_ID-before-8-4
   ```

   Replace `DB_INSTANCE_ID` with the instance identifier (`<global_prefix>-db`).

3. In `terraform.tfvars`, set these values:

   ```hcl
   db_engine_version              = "8.4"
   db_param_group                 = "mysql8.4"
   
   db_allow_major_version_upgrade = true
   db_apply_immediately           = true
   ```

4. Run `make check_db_replacement`. The output must end with `OK: no RDS instance is deleted or replaced`. If it reports a delete, don't apply: a setting other than the ones in step 3 forces a replacement.
5. In the maintenance window, run `make apply`.
   - RDS runs mandatory compatibility prechecks before it stops the instance. If a precheck fails, RDS cancels the upgrade, nothing changes, and the reason is in the `PrePatchCompatibility.log` database log.
   - If the upgrade fails after the prechecks, RDS rolls the instance back to 8.0 (event `RDS-EVENT-0188`).
6. Set `db_allow_major_version_upgrade = false` and `db_apply_immediately = false`, then run `make apply` again.
7. Check the result:
   - `aws rds describe-db-instances --db-instance-identifier DB_INSTANCE_ID --query 'DBInstances[0].EngineVersion'` prints an 8.4 version.
   - Platform starts and shows existing workspaces and runs.
   - If Groundswell is on, it connects and stays up. It needs `swell_container_version` 0.4.15 or later.

## Upgrade a container database

**Warning:** MySQL 8.4 converts the 8.0 data files on its first start. There is no way back to 8.0 without your backup.

1. On the instance, stop Platform and back up the data directory:

   ```bash
   cd ~ && docker compose down
   sudo tar -czf ~/mysql-8.0-backup.tar.gz -C ~/.tower/db mysql
   ```

2. In `terraform.tfvars`, set `db_container_engine_version = "8.4"`, then run `make apply`.
3. Check the result: the `db` container runs `mysql:8.4`, and Platform starts and shows existing data.

## Databases the installer doesn't manage

If you use `flag_use_existing_external_db = true`, upgrade that database with your own process, then set `db_engine_version = "8.4"`. With `db_enforce_tls = true`, Platform connects with TLS, so your database must accept TLS connections.
