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

## Auto-skip adapters

[`tests/conftest.py`](../../tests/conftest.py) auto-skips two slices when they don't fit the environment or the change scope. Both fire at collection time and are bypassed by positive `-m` selection.

| Slice | Skipped when… | Bypass |
| ----- | -------------- | ------ |
| `@pytest.mark.testcontainer` | No Docker socket is reachable. Detected via `DOCKER_HOST=unix://<path>` (socket-file presence check), other `DOCKER_HOST` schemes (trusted), or `/var/run/docker.sock`. | `-m testcontainer` (e.g. `make run_tests_containers_only`). |
| `@pytest.mark.variable_validation` | `variables.tf` is unchanged on this branch — union of committed-vs-`origin/master`, staged, and unstaged. Failing open: no skip if no base ref can be resolved. | `-m variable_validation` (e.g. `make run_tests_variables_only`). |

Skip reasons are explicit in pytest output so diagnostics stay clear:

- `"No Docker socket reachable; skipped by tests/conftest.py auto-skip."`
- `"variables.tf unchanged on this branch; skipped by tests/conftest.py auto-skip."`

See [Design Decision #18](../../documentation/design_decisions.md) for motivation.

## Templatefile test path: plan-less by default

After [`#353`](https://github.com/seqeralabs/cx-field-tools-installer/issues/353), templatefile-rendering tests no longer require `terraform plan`. `module.connection_strings.*` outputs are resolved via a single `terraform console` call (~1-2 s) instead of a full plan (~30+ s on cold cache). Both call shapes coexist; tests pick what they need.

| Test shape | Setup helper | `generate_tc_files` plan arg | When |
| ---------- | ------------ | ---------------------------- | ---- |
| Templatefile rendering only | `stage_tfvars(tf_modifiers)` | `None` | Default for `test_config_file_content.py`, `test_ansible_files.py`, `test_testcontainer_execution.py`. |
| Plan-derived state validation | `plan = prepare_plan(tf_modifiers)` | `plan` (dict) | Use for tests that inspect plan outputs directly (`test_outputs.py`) or that need plan-time validation errors (`test_variable_validation.py`). |

### Invariants the fast path depends on

The console-based path works because two architectural rules hold across the repo:

1. **Every `local.<name>` referenced from a `templatefile(...)` arg map in [`009_define_file_templates.tf`](../../009_define_file_templates.tf) must be a pure function of vars + module outputs.** No branch of any ternary may reference a resource attribute, even an unselected branch — HCL evaluates both branches eagerly, so a single resource ref in an "if false" branch collapses the whole local to `(known after apply)` under console-without-plan. The regression test at [`tests/unit/framework/test_console_locals_resolvability.py`](../../tests/unit/framework/test_console_locals_resolvability.py) walks every referenced local and asserts each resolves; it catches violations at PR time.
2. **Every resource-attribute input to a module the test framework evaluates via console must use the two-layer defense pattern:** `var.use_mocks ? null : try(<resource_or_module_ref>, null)`. The `use_mocks` gate selects the safe `null` branch in tests; the `try()` wrapper neutralises the unsafe branch by catching the missing-resource evaluation error. Without both, the module's input is unknown → its outputs collapse to `(known after apply)` → the templatefile rendering silently corrupts. The pattern is documented in-line above the `module "connection_strings"` invocation in [`000_main.tf`](../../000_main.tf); apply it to any new module that becomes console-evaluated.

If a new local naturally combines a tfvars-known branch with a resource-attribute branch (and refactoring isn't an option), the offending test can opt back into the plan path by reverting to `prepare_plan(...)` + `generate_tc_files(..., plan=plan)`. The slow path is preserved precisely for this case.

## Running tests

See [`testing_commands.md`](testing_commands.md).
