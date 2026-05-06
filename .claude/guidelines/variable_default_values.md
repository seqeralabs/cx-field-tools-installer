# Variable Default Values

## Scope

This guideline applies to the **top-level project** only — i.e. the [`variables.tf`](../../variables.tf) at the repository root and the corresponding [`templates/TEMPLATE_terraform.tfvars`](../../templates/TEMPLATE_terraform.tfvars).

Sub-modules under [`modules/`](../../modules/) are out of scope and may follow standard Terraform conventions (defaults permitted).

## Rules

1. **No default values in the top-level `variables.tf`.** Every `variable` block must omit the `default = ...` clause.

2. **Every variable declared in the top-level `variables.tf` must be set in [`templates/TEMPLATE_terraform.tfvars`](../../templates/TEMPLATE_terraform.tfvars).** That file is the single source of truth for what a deployer must provide.

3. **Any addition, modification, or removal of a variable in `TEMPLATE_terraform.tfvars` must be recorded in [`CHANGELOG.md`](../../CHANGELOG.md)** under `Configuration File Changes` → `` `terraform.tfvars` `` for the in-progress release.

## Why

Defaults in the top-level `variables.tf` silently fill in values the deployer never reviewed — masking misconfiguration until a deployment fails or, worse, succeeds with the wrong setup. Forcing explicit values in `TEMPLATE_terraform.tfvars` makes every decision visible at the moment a customer copies the template and gives Support a single file to diff when reproducing customer environments.

The CHANGELOG entry serves the same audience: deployers upgrading from a previous release need to know exactly what to add, change, or remove in their existing `terraform.tfvars`.

## CHANGELOG entry format

Add one row per variable to the table under the in-progress release's `Configuration File Changes` → `` `terraform.tfvars` `` section:

| Status | Component | Parameter Name | Description |
| ------ | --------- | -------------- | ----------- |
| New | `<component>` | `<variable_name>` | What it controls and what value the deployer should pick. |
| Modified | `<component>` | `<variable_name>` | What changed (rename, type change, new acceptable values) and the migration step. |
| Deleted | `<component>` | `<variable_name>` | Why it was removed and what replaces it (if anything). |

One row per variable. If a single change touches multiple variables, write multiple rows — do not collapse.
