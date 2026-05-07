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

## Running tests

See [`testing_commands.md`](testing_commands.md).
