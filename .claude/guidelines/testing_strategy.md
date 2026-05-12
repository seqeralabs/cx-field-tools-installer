# Testing Strategy

## Approach

The project uses a hybrid testing approach:

1. **Plan-based tests** — Mock resources using `terraform plan` output. Plan outputs are cached in `tests/.plan_cache` to speed up n+1 test cycles when underlying values are unchanged.
2. **Unit tests** — Test individual modules in isolation.
3. **Integration tests** — Full deployment and validation cycle.
4. **Local value tests** — Validate computed values and data sources.

All tests are designed to run without requiring actual AWS resources for basic validation.

## Layout

| Directory | Purpose |
| --------- | ------- |
| [`tests/unit/`](../../tests/unit/) | Unit tests for modules. |
| [`tests/integration/`](../../tests/integration/) | Integration tests for end-to-end workflows. |
| [`tests/datafiles/`](../../tests/datafiles/) | Generated test data. |
| [`tests/logs/`](../../tests/logs/) | Structured pytest logs for LLM analysis. |
| [`tests/utils/`](../../tests/utils/) | Test utilities including log parsing and formatting. |

Pytest markers are defined in [`tests/pytest.ini`](../../tests/pytest.ini) — that file is authoritative.

## Fixtures

| Fixture | Scope | Purpose |
| ------- | ----- | ------- |
| `session_setup` | session | Stages test tfvars, JSONifies `009_define_file_templates.tf`, sets up plan cache. Used by virtually every test. Does **not** include any AWS preflight — see `aws_preflight` below. |
| `aws_preflight` | session | Opt-in. Confirms a valid AWS SSO token via `aws sts get-caller-identity`. Consume by adding `aws_preflight` to a test's fixture parameters. Tests under `tests/unit/` should not need this (they all use `var.use_mocks = true`); reserved for tests that genuinely interact with real AWS (e.g. future `tests/remote/`). |
| `teardown_tf_state_all` | function | Destroys Terraform state on teardown. Use for tests that create real infrastructure. |
| `config_baseline_settings_default` | session | Runs `terraform plan` on the default test tfvars and returns the cached plan output. |

## Running tests

See [`testing_commands.md`](testing_commands.md).
