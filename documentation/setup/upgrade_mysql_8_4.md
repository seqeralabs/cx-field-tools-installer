# Upgrade the Platform database from MySQL 8.0 to 8.4

Platform v26.1 and later officially support only MySQL 8.4. This runbook upgrades an existing deployment in place: the RDS instance or container database keeps its data, name, and endpoint.

See Design Decision 25 in [design_decisions.md](../design_decisions.md) for why the upgrade works this way.

## What changes

- The engine version moves from 8.0 to 8.4. The RDS parameter group moves to the `mysql8.4` family, and the instance moves to the AWS default option group `default:mysql-8-4`.
- With `db_enforce_tls = true` (the template default), Platform connects with TLS, and the database refuses plaintext connections. On RDS, Platform and Groundswell verify the server certificate against the Amazon RDS CA bundle, which Ansible downloads to the instance. The instance needs outbound HTTPS to `truststore.pki.rds.amazonaws.com`.
- The upgrade can't be reversed. RDS rolls back only if the upgrade itself fails.

## Before you start

- Plan a maintenance window. An RDS upgrade typically takes about 10 minutes, and Platform can't reach the database during it.
- Confirm that you run installer 1.9.0 or later, and that `make check_upgrade` reports no missing variables.

## Upgrade prerequisites

Do these steps once, on your first apply with installer 1.9.0, if the installer created your RDS instance (`flag_create_external_db = true`). Do them even if you stay on MySQL 8.0. They don't apply to the container database or to a database the installer doesn't manage.

From 1.9.0, the installer no longer creates its own option group for the RDS instance. It attaches the AWS default group for the MySQL version instead: `default:mysql-8-0`, then `default:mysql-8-4` after the upgrade. The old group was always empty, and RDS can't delete it while any snapshot refers to it, so Terraform must forget it instead of deleting it.

1. Back up the Terraform state, then remove the old option group from it:

   ```bash
   terraform state pull > tfstate-backup.json
   terraform state rm 'module.rds[0].module.db_option_group.aws_db_option_group.this[0]'
   ```

   This changes only the state. The option group stays in AWS. `tfstate-backup.json` contains secrets: delete it after step 3 succeeds, and don't commit it.

2. In `terraform.tfvars`, keep your current `db_engine_version`, and set `db_apply_immediately = true`. Without it, RDS waits for the maintenance window to switch the option group while Terraform records the switch as done, and the 8.4 upgrade later fails with `Current Option Group … is non-default`.
3. Run `make check_db_replacement`, then `make apply`. The plan must show the RDS instance updated in place, with `option_group_name` changing to `default:mysql-8-0`, and no `aws_db_option_group` created or destroyed.
4. Optional: after the old option group's snapshots expire (`db_backup_retention_period`, 7 days by default), delete it:

   ```bash
   aws rds delete-option-group --option-group-name OLD_OPTION_GROUP_NAME
   ```

   Replace `OLD_OPTION_GROUP_NAME` with the old group's name: `<global_prefix>-db-` followed by a timestamp.

If an earlier apply is stuck at `Still destroying… aws_db_option_group`, step 1 also fixes it: `terraform state rm` removes the stuck entry too.

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

## Why the database setup scripts changed for MySQL 8.4

On every `terraform apply`, the installer runs two short SQL scripts against the database: `tower.sql` for Platform and `groundswell.sql` for Groundswell. Each script makes sure that the application's database and user exist, sets the user's password to the value in SSM, and gives the user access to its database. Installer 1.9.0 changes how the scripts create the user, because the old way fails on RDS for MySQL 8.4.

**The problem.** After an RDS database is upgraded to 8.4, the old scripts stop the apply at the `Populate RDS` step with this error:

```
ERROR 4006 (HY000) at line 3: Operation CREATE USER failed for 'tower'@'%' as it is referenced as a definer account in a view.
```

- Platform creates views in its database. A view is a saved query that behaves like a table. Each view records the user that owns it, called its *definer*. Platform's views are owned by the `tower` user.
- The old scripts created the user with `CREATE USER IF NOT EXISTS`, which should do nothing when the user already exists. But before it checks whether the user exists, MySQL 8.4 checks whether the user owns any views. If it does, MySQL refuses the command unless the account that runs it has the `ALLOW_NONEXISTENT_DEFINER` privilege.
- On RDS for MySQL 8.4, the master user that runs the scripts doesn't have that privilege, and you can't grant it. On 8.0, an older privilege (`SET_USER_ID`) covered the same check, so the scripts worked.
- The container database isn't affected, because its `root` user has every privilege.

**The fix.** The scripts now create the user only when it is missing:

1. The script looks up the user in MySQL's list of accounts (`mysql.user`).
2. If the user is missing, the script creates it locked and without a password (`ACCOUNT LOCK`), so nobody can log in with it yet. If the user exists, the script does nothing at this step, and MySQL never runs the view check. SQL has no plain "if" command for this, so the script builds the right command as text and then runs that text (`PREPARE` and `EXECUTE`).
3. The script sets the user's password to the SSM value and unlocks the account (`ALTER USER … ACCOUNT UNLOCK`). This runs on every apply, as before. MySQL doesn't run the view check for this command, and it hides the password in its logs.
4. The script gives the user access to its database (`GRANT`), unchanged from before.

You don't need to do anything: the new scripts run on every apply from installer 1.9.0. Two cases behave differently from before:

- If you locked the `tower` or `swell` user by hand, the next apply unlocks it.
- If the user was deleted outside the installer but its views still exist, the apply still stops with the same error. Re-creating the user would make it the owner of those views again, which MySQL allows only with the missing privilege. Contact Seqera support before you continue.
