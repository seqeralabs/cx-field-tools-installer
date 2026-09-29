# (Optional) Data Lineage

Enables Nextflow data lineage on a Seqera Platform deployment. Lineage records the provenance of pipeline runs at workflow, task, and file granularity. Public-preview feature; see [Seqera's Data Lineage docs](https://docs.seqera.io/platform-enterprise/data/data-lineage) for the user-facing concepts and workspace-side setup.

**WARNING**
- Data Lineage is meant to persist over time (for traceability).
- Any infrastructure created by Seqera Platform related to Data Lineage will persist between teardown/recreation of CX Installer deployments. Ensure your SOPs account for destruction of no-longer-necessary SQS queues, SNS topics, and S3 buckets supporting the Lineage feature.

## Requirements

- Seqera Platform **v26.1.0+**.
- Platform **v26.2.0+**: AWS SNS pushes lineage events to Platform, so `tower_server_url` must be reachable from the internet over HTTPS with a publicly trusted certificate. `make verify` fails when lineage is on with a private instance, HTTP, a private CA, or private-only DNS. See [Design Decision 23](../design_decisions.md).
- [Nextflow configuration](https://docs.seqera.io/platform-enterprise/data/data-lineage#advanced-experimenting-with-data-lineage). Out of scope for this installer.

## Activation

Two tfvars (see [`TEMPLATE_terraform.tfvars`](../../templates/TEMPLATE_terraform.tfvars), `Data Lineage` section):

| tfvars | Effect |
|---|---|
| `flag_enable_data_lineage = true` | Master gate. Renders the `data_lineage_options` values to `tower.env` and attaches the lineage IAM policy to the EC2 instance role. |
| `data_lineage_options.allowed_workspaces` | `TOWER_LINEAGE_ALLOWED_WORKSPACES`. Empty = all workspaces. A numeric CSV (`"12,34"`) = only those workspaces. |
| `data_lineage_options.store_prefix` | `TOWER_LINEAGE_STORE_PREFIX` (v26.2.0+). Name prefix of the buckets and SNS topics Platform creates. Also limits the v26.2 IAM statements. |
| `data_lineage_options.sns_max_retries` | `TOWER_LINEAGE_SNS_MAX_RETRIES` (v26.2.0+). |
| `data_lineage_options.sns_max_delay_seconds` | `TOWER_LINEAGE_SNS_MAX_DELAY_SECONDS` (v26.2.0+). |
| `data_lineage_options.migrate_sqs_transport` | `TOWER_LINEAGE_MIGRATE_SQS_TRANSPORT` (v26.2.0+). One-off move of v26.1 SQS workspaces to SNS. |
| `data_lineage_options.global_search_enabled` | `TOWER_GLOBAL_SEARCH_ENABLED` (v26.2.0+). |

With `flag_enable_data_lineage = false`, lineage stays off. On v26.2.0+, an unset `TOWER_LINEAGE_ALLOWED_WORKSPACES` means "all workspaces", so the installer renders `TOWER_LINEAGE_ALLOWED_WORKSPACES=-1` (matches no workspace) instead.

## IAM

When `flag_enable_data_lineage = true` **and** the installer is managing the EC2 instance role (`flag_iam_use_prexisting_role_arn = false`), the installer auto-creates an IAM policy named `${global_prefix}_policy_lineage` and attaches it to the role.

The policy grants S3 + SQS actions on `seqera-lineage-*` resource ARNs. On v26.2.0+ it also grants SNS topic management and S3 read actions on `<store_prefix>-*`, and `sqs:DeleteQueue` for the migration. See the canonical action list and resource scoping in [`assets/src/aws/iam_role_policy_lineage.json.tpl`](../../assets/src/aws/iam_role_policy_lineage.json.tpl).

### Pre-existing role (`flag_iam_use_prexisting_role_arn = true`)

The installer cannot mutate a role it doesn't own. You must attach the lineage policy manually:

1. Use the contents of [`assets/src/aws/iam_role_policy_lineage.json.tpl`](../../assets/src/aws/iam_role_policy_lineage.json.tpl) as your policy document. Substitute `${aws_region}`, `${aws_account}`, and `${lineage_store_prefix}` with literal values for your deployment. Before v26.2.0, delete the statements between `%{ if … }` and `%{ endif }`; from v26.2.0, keep them and delete only the two markers.
2. Create the IAM policy in your AWS account.
3. Attach it to the IAM role identified by `iam_prexisting_instance_role_arn`.

`check_configuration.py` emits a warning at `make verify` reminding you of this when both flags are set.

## Upgrading a v26.1 lineage site to v26.2

1. Keep `migrate_sqs_transport = true` for the first start on v26.2. Platform then moves each Automatic-mode workspace from SQS to SNS and deletes the old queue.
2. In each lineage workspace, open **Settings > Workspace settings > Lineage** and check that **Event delivery** shows **Active**.
3. Move Manual-mode workspaces yourself: create an SNS topic, subscribe the Platform lineage webhook to it, and enter the topic ARN. Platform cannot migrate resources it doesn't own.

## Verifying activation

After `terraform apply`:

```bash
ssh <vm> "grep TOWER_LINEAGE ~/target/tower_config/tower.env"
# expected when enabled with no restriction:
#   TOWER_LINEAGE_ALLOWED_WORKSPACES=
# when restricted:
#   TOWER_LINEAGE_ALLOWED_WORKSPACES=12,34
# when disabled on v26.2.0+:
#   TOWER_LINEAGE_ALLOWED_WORKSPACES=-1
```

Workspace-side activation (per-workspace bucket/topic selection) happens in Platform → Workspace settings → Lineage tab.
