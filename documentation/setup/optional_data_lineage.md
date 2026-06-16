# (Optional) Data Lineage

Enables Nextflow data lineage on a Seqera Platform deployment. Lineage records the provenance of pipeline runs at workflow, task, and file granularity. Public-preview feature; see [Seqera's Data Lineage docs](https://docs.seqera.io/platform-cloud/data/data-lineage) for the user-facing concepts and workspace-side setup.

## Requirements

- Seqera Platform **v26.1.0+**.
- [Nextflow configuration](https://docs.seqera.io/platform-cloud/data/data-lineage#advanced-experimenting-with-data-lineage). Out of scope for this installer.

## Activation

Two tfvars (see [`TEMPLATE_terraform.tfvars`](../../templates/TEMPLATE_terraform.tfvars), `Data Lineage` section):

| tfvars | Effect |
|---|---|
| `flag_enable_data_lineage = true` | Master gate. Emits `TOWER_LINEAGE_ALLOWED_WORKSPACES` to `tower.env`; attaches the lineage IAM policy to the EC2 instance role. |
| `data_lineage_allowed_workspaces = ""` | Empty = all workspaces. Populated as a numeric CSV (`"12,34"`) = restricted to those workspaces. |

Both default to off / empty, so existing deployments aren't affected on upgrade.

## IAM

When `flag_enable_data_lineage = true` **and** the installer is managing the EC2 instance role (`flag_iam_use_prexisting_role_arn = false`), the installer auto-creates an IAM policy named `${global_prefix}_policy_lineage` and attaches it to the role.

The policy grants S3 + SQS actions scoped to `seqera-lineage-*` resource ARNs only (Platform creates queues and buckets under that prefix). See the canonical action list and resource scoping in [`assets/src/aws/iam_role_policy_lineage.json.tpl`](../../assets/src/aws/iam_role_policy_lineage.json.tpl).

### Pre-existing role (`flag_iam_use_prexisting_role_arn = true`)

The installer cannot mutate a role it doesn't own. You must attach the lineage policy manually:

1. Use the contents of [`assets/src/aws/iam_role_policy_lineage.json.tpl`](../../assets/src/aws/iam_role_policy_lineage.json.tpl) as your policy document. Substitute `${aws_region}` and `${aws_account}` with literal values for your deployment.
2. Create the IAM policy in your AWS account.
3. Attach it to the IAM role identified by `iam_prexisting_instance_role_arn`.

`check_configuration.py` emits a warning at `make verify` reminding you of this when both flags are set.

## Verifying activation

After `terraform apply`:

```bash
ssh <vm> "grep TOWER_LINEAGE /etc/tower/tower.env"
# expected when enabled with no restriction:
#   TOWER_LINEAGE_ALLOWED_WORKSPACES=
# when restricted:
#   TOWER_LINEAGE_ALLOWED_WORKSPACES=12,34
```

Workspace-side activation (per-workspace bucket/queue selection) happens in Platform → Workspace settings → Lineage tab.
