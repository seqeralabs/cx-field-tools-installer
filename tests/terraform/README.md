# `terraform test` suite

Native Terraform tests (`.tftest.hcl`) covering variable validations defined in
`variables.tf`. Complements the pytest suite under `tests/unit/` and `tests/integration/`,
which still owns rendered-template-content assertions and Python validator coverage.

## What's here today

| File | Asserts |
| --- | --- |
| `version_validation.tftest.hcl` | `tower_container_version` floor (v26.1.0+) and tag-shape regex. |
| `string_shape_validation.tftest.hcl` | `tower_server_url`, `tower_root_users`, `alb_certificate_arn`, `private_cacert_bucket_prefix`, MySQL 8.x floor on both DB engine version variables. |
| `workspace_id_validation.tftest.hcl` | Comma-separated-integer rule on `data_studio_eligible_workspaces`, `data_studio_ssh_eligible_workspaces`, `pipeline_versioning_eligible_workspaces`. |

Each test uses `command = plan` and `expect_failures = [var.foo]` to assert a specific
variable validation trips. Other variables are sourced from a baseline tfvars file.

## How to run

`terraform test` requires a complete tfvars baseline so all required variables resolve.
The same fixture used by pytest works here:

```sh
make generate_test_data    # produces tests/datafiles/terraform.tfvars
make terraform_test        # runs `terraform test` against tests/terraform/
```

Or directly:

```sh
terraform init
terraform test \
  -test-directory=tests/terraform \
  -var-file=tests/datafiles/terraform.tfvars
```

## What does NOT live here (yet)

- **Plan-shape assertions** beyond variable validation (e.g. "this combination of flags
  produces N security groups"). Those will land as a follow-up under #334 once the shape
  of resource-level assertions is settled.
- **Rendered-template-content tests** (e.g. asserting a particular line appears in the
  rendered `tower.yml`). Stays in pytest — `terraform test` is awkward for string content.
- **CI**. A workflow that runs both `terraform test` and `pytest` on every PR is a
  separate slice under #334.

Refs #334.
