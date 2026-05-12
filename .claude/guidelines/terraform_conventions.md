# Terraform Conventions

## Conventions

- **No default values** in [`variables.tf`](../../variables.tf) — every value must be explicitly set in `terraform.tfvars`. Rules and rationale in [`variable_default_values.md`](variable_default_values.md).
- Use `null_resource` with `local-exec` provisioners instead of `local_file` resources. Rationale: `local_file` writes during plan-evaluation, which conflicts with the project's "regenerate everything on apply" model.
- State is stored locally by default at `DONTDELETE/terraform.tfstate`.
- Templates live under [`assets/src/`](../../assets/src/) with `.tpl` extension; rendered output goes to `assets/target/` (not source-controlled).
