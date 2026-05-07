# Terraform Style Guide (Project Overrides)

## Project status

**Legacy compatibility mode.** This code is in production with real clients. It was written before the house Terraform style guide (`<PATH>`) was adopted. A V2 will refactor to current standards; until then, minimize churn.

<!-- TODO(#325): replace `<PATH>` above with the actual location of the house Terraform style guide once it is published. -->

## Style-guide applicability (overrides global)

The Terraform style guide applies to:

- **New files** being added.
- **Bug fixes** — keep the fix minimal. Do not bundle stylistic cleanup.
- **Security findings** from checkov / trivy / terrascan — fix or consciously suppress with reason.

The style guide does NOT apply to:

- **Renaming existing resources** (requires `moved {}` blocks or `terraform state mv` — both blast-radius).
- **Restructuring existing files** to match the strict module layout.
- **Converting `count` → `for_each`** on existing resources (causes destroy/recreate).
- **Backfilling `description` / `type` / `sensitive`** on pre-existing variables/outputs unless the user explicitly asks.
- **Argument ordering changes** inside existing resource/variable/output blocks.

## When a linter flags existing code

1. **Do NOT auto-fix.** Surface the finding with `file:line`.
2. Propose **suppression first** (inline `# tflint-ignore:<rule>` / `# checkov:skip=<id>: <reason>`), refactor second — and only on explicit user request.
3. Accumulated suppressions = breadcrumbs for the V2 migration.

## Blast radius — additional rules for this repo

Beyond the global rails:

- `terraform state mv` / `rm` / `import` are **forbidden without a written migration plan in the PR description**.
- Resource renames require a `moved {}` block AND explicit user confirmation of `terraform plan` output before apply.
- Any refactor that changes resource addresses (module extraction, renaming, loop-style changes) is a V2 concern and should be flagged, not attempted.
