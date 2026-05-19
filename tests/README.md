# Testing Framework

A home-rolled Python + Bash + Terraform stack for validating `terraform.tfvars` → generated config-file behaviour locally, with no AWS resources required for the unit suite.

## Why this stack

The native options were rejected during initial design:

- **Terraform `test`** — heavy and clunky vs. a real programming language.
- **Terratest** — would introduce Go into a Python-shop project.
- **`tftest`** — under-documented; abandoned after sustained frustration.

Terraform's CLI is slow enough that a re-running test loop dominates iteration time. The framework's job is to keep that loop fast (~2s for the core slice) while still covering enough surface to catch config-file regressions before they reach a deployment.

## Layout

| Path | Purpose |
|---|---|
| [`unit/`](./unit/) | Unit tests. Render templatefiles via `terraform console` and assert against deltas. |
| [`unit/config_files/expected_deltas.py`](./unit/config_files/expected_deltas.py) | Paired `<FEATURE>` tfvars strings + `<FEATURE>_ASSERTIONS` delta dicts. |
| [`datafiles/`](./datafiles/) | Generated test tfvars + secrets. Regenerated each session. |
| [`logger/`](./logger/) | Tests for the structured-logging utilities. |
| [`logs/`](./logs/) | JSON-Lines pytest output for LLM analysis. |
| [`utils/`](./utils/) | Test framework internals (precompute, cache, assertions, file helpers). |
| [`remote/`](./remote/) | Forward-looking remote-execution brainstorming (slated for 2026). |
| [`.scenario_cache/`](./.scenario_cache/) | Per-scenario rendered files, keyed by `hash_templatefile_cache_key`. Auto-regenerated. |

Pytest markers: [`tests/pytest.ini`](./pytest.ini) is authoritative.

## How the framework works (short version)

1. `session_setup` (in [`conftest.py`](./conftest.py)) stages test tfvars into the project root, JSONifies `009_define_file_templates.tf` and `012_outputs.tf`, then dispatches `precompute_in_parallel(scenarios)`.
2. Each precompute worker runs **one** `terraform console` call per scenario, with a single mega-`jsonencode` expression that resolves locals, outputs, and all rendered templatefiles at once. Results land in `tests/.scenario_cache/{hash}/`.
3. Tests read those files via the `generated_test_files` and `scenario_outputs` fixtures. No `terraform plan` for the templatefile path; no AWS calls.

Full data-flow walkthrough: [`new_implementation.md`](./new_implementation.md).
Historical context (pre-retrofit pipeline, options-A/B/C exploration): [`docs/`](./docs/).

## Running tests

See [`.claude/guidelines/testing_commands.md`](../.claude/guidelines/testing_commands.md) for the canonical command reference. Quick reminders:

| Command | When |
|---|---|
| `make run_tests_core_only` | Default fast loop (~2s). |
| `make run_tests_containers_only` | Requires Docker / Podman socket. |
| `make run_tests_variables_only` | Exercises `variables.tf` validation blocks (~30s+). |
| `make purge_cache` | Wipes `.scenario_cache` + plan cache. Run when `.tf` logic changes. |

Scope auto-skip behaviour (Docker socket missing, `variables.tf` unchanged) is documented in [`.claude/guidelines/testing_strategy.md`](../.claude/guidelines/testing_strategy.md).

## Troubleshooting

- **`terraform console` fails with exit code 1 during a templatefile test.**
  Most common cause: a missing comma between args inside a `templatefile(...)` call in [`009_define_file_templates.tf`](../009_define_file_templates.tf). `terraform plan` tolerates it; `terraform console` does not.

- **`terraform plan` fails during a plan-based test (e.g. `test_outputs.py`).**
  Copy [`datafiles/terraform.tfvars`](./datafiles/terraform.tfvars) and [`datafiles/base-overrides.auto.tfvars`](./datafiles/base-overrides.auto.tfvars) into the project root and re-run `terraform plan -out=tfplan -refresh=false && terraform show -json tfplan > tfplan.json` manually for a fuller error message.

- **Testcontainer tests fail to pull images.**
  You're not logged into `cr.seqera.io`. Authenticate, or pre-pull the images.

- **VSCode reports two pytest sessions running.**
  The `tests/conftest.py` lifecycle hooks fire in VSCode's background test-collection process as well as the foreground run. Disable `python.testing.pytestEnabled` in `.vscode/settings.json` to silence it. Cost the author several hours; documenting it so it doesn't cost you the same.

- **Stale cache after `.tf` changes.**
  `hash_templatefile_cache_key` hashes tfvars and disk state. Logic changes inside Python utility files or unhashed templates won't invalidate. Run `make purge_cache` when in doubt.

## Rootless Podman setup

`testcontainers` (via `docker-py`) needs a reachable socket. For rootless Podman:

```bash
systemctl --user enable --now podman.socket
export DOCKER_HOST="unix://${XDG_RUNTIME_DIR}/podman/podman.sock"
export TESTCONTAINERS_RYUK_DISABLED=true   # known incompatibility with rootless podman
ls -l "${XDG_RUNTIME_DIR}/podman/podman.sock"
podman version
```

## Structured logging

Tests emit JSON-Lines records to [`logs/pytest_structured.log`](./logs/) on every run. Each entry carries `timestamp`, `test_session_id`, `event_type`, `test_path`, `status`, `duration`, `metadata`, and `failure_reason` (when applicable).

Parser CLI: [`utils/log_parser.py`](./utils/log_parser.py).

```bash
python tests/utils/log_parser.py summarize
python tests/utils/log_parser.py extract-failures
python tests/utils/log_parser.py llm-format --recent 100
python tests/utils/log_parser.py validate
python tests/utils/log_parser.py export-json
tail -f tests/logs/pytest_structured.log
```

Toggles (default-on): `PYTEST_STRUCTURED_LOGGING`, `PYTEST_STRUCTURED_LOGGING_LEVEL`, `PYTEST_LOG_FILE`.

## Setup

Python packages: [`requirements.txt`](./requirements.txt).

Container registry access: must be logged into [cr.seqera.io](https://cr.seqera.io) if you intend to run the `testcontainer` slice.
