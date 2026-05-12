# CHANGELOG Update Protocol

## Scope

Every PR that changes deployer-visible behaviour requires a corresponding entry in [`CHANGELOG.md`](../../CHANGELOG.md), recorded in the same PR. Behaviour changes include:

- Adding, modifying, or removing a `terraform.tfvars` variable
- Modifying the configuration of an existing component (container env var, nginx directive, image version, etc.)
- Adding or removing a component (container, module, service)
- Security fixes affecting the deployed system

Pure refactors with identical observable behaviour, internal-only test changes, and comment-only changes do not require an entry.

## Rules

1. **Same-PR.** The entry lands in the same PR as the change. [`documentation/upgrade_steps.md`](../../documentation/upgrade_steps.md) step 5 routes upgraders to `CHANGELOG.md` for `terraform.tfvars` migration guidance, and reviewers rely on `Notable Changes` to understand release content — a missing entry silently breaks both audiences.

2. **Pick the right `Notable Changes` subsection** under the in-progress release:
    - **General** — component additions/removals, config changes, version bumps, behaviour changes (default for most entries)
    - **Security** — security-relevant fixes
    - **Documentation** — documentation additions/changes (including `TEMPLATE_terraform.tfvars` updates)
    - **Testing** — test surface changes

3. **`terraform.tfvars` variable changes need an additional entry.** Beyond the `Notable Changes` bullet (typically `Documentation` for variable additions), a variable add/modify/delete also requires a row under `### Configuration File Changes → #### terraform.tfvars`. Row format is defined in [`variable_default_values.md`](variable_default_values.md#changelog-entry-format).

## Bullet format

```
- <Concise change description>. [`#<issue>`](https://github.com/seqeralabs/cx-field-tools-installer/issues/<issue>)
```

Link a tracking issue when one exists.
