# (Optional) Workload Identity Federation

From Seqera Platform **v26.2.0**, AWS and Google Cloud credentials can use workload identity federation (WIF) instead of long-lived keys. The credential stores only an IAM role ARN (AWS) or a service account email and workload identity provider path (Google). Platform signs a short-lived OIDC token, and AWS or Google STS exchange it for temporary cloud credentials. WIF covers compute environments, Data Explorer, Forge, and Studios (Studio images need Connect client 0.14.0 or later).

See [Design Decision 24](../design_decisions.md) for why the installer handles WIF this way.

## Requirements

- Seqera Platform **v26.2.0+**. `make verify` fails if WIF is enabled on an older version.
- AWS or Google STS must reach Platform's issuer over **public HTTPS with a publicly trusted certificate**:
  - Issuer: `${tower_server_url}/api`
  - Discovery: `${tower_server_url}/api/.well-known/openid-configuration`
  - Keys: `${tower_server_url}/api/.well-known/jwks.json`

  A private instance, HTTP-only, a private CA, or a private-only DNS name prevents this. `make verify` warns when WIF is enabled with any of them.
- Keep `tower_server_url` stable. Every trust policy and workload identity provider names the issuer URL, so changing the domain breaks them all.

## Activation

Two tfvars (see [`TEMPLATE_terraform.tfvars`](../../templates/TEMPLATE_terraform.tfvars)):

| tfvars | Effect |
|---|---|
| `tower_identity_federation_enabled = false` (default) | WIF is off in every workspace: `tower.env` has `TOWER_IDENTITY_FEDERATION_ALLOWED_WORKSPACES=-1`. |
| `tower_identity_federation_enabled = true` | Configures Platform's OIDC provider (`TOWER_OIDC_PEM_PATH`, key mounted into `backend` and `cron`) and writes `tower_identity_federation_allowed_workspaces`. |
| `tower_identity_federation_allowed_workspaces = ""` | With WIF on: all workspaces. A numeric CSV (`"12,34"`) limits WIF to those workspaces. |

The OIDC signing key is the same one Studios uses (`data-studios-rsa.pem`). Sites with Studios on already have it; enabling WIF only adds the allow-list.

## Cloud-side setup (not done by the installer)

- **AWS:** create an IAM OIDC identity provider for the issuer URL, and a role whose trust policy allows `sts:AssumeRoleWithWebIdentity` **and** `sts:TagSession` from that provider. AWS rejects the exchange if `sts:TagSession` is missing. Enter the role ARN in the Platform credential. GovCloud and China role ARNs are rejected by the Platform UI.
- **Google Cloud:** create a workload identity pool and an OIDC provider with the issuer URL, map `google.subject=assertion.sub`, and grant `roles/iam.workloadIdentityUser` on the service account. Enter the service account email and provider path in the Platform credential. For Data Explorer, also grant the service account `roles/iam.serviceAccountTokenCreator` on itself.

Follow the Platform documentation for the full trust-policy and pool setup.

Seqerakit cannot create WIF credentials (CLI and Terraform support is deferred past v26.2). Create them in the Platform UI.

## Upgrading: existing Google Cloud WIF credentials

Before v26.2, Google WIF tokens always carried the `workflow` subject. In a workspace where WIF is enabled, they now carry `platform`, `data`, `studio`, or `workflow`, depending on the request. A binding that admits only the `workflow` subject (or an `attribute.workload` value) stops matching, and the workspace loses access.

Before you set `tower_identity_federation_enabled = true`, update those bindings to admit every subject, or leave the workspace out of `tower_identity_federation_allowed_workspaces`.

## Verifying activation

After `terraform apply`:

```bash
ssh <vm> "grep -E 'TOWER_OIDC_PEM_PATH|TOWER_IDENTITY_FEDERATION' ~/target/tower_config/tower.env"
# WIF off:
#   TOWER_IDENTITY_FEDERATION_ALLOWED_WORKSPACES=-1
# WIF on, all workspaces:
#   TOWER_OIDC_PEM_PATH=/data-studios-rsa.pem
#   TOWER_IDENTITY_FEDERATION_ALLOWED_WORKSPACES=

curl -s https://<tower_server_url>/api/.well-known/jwks.json   # returns the signing key
```
