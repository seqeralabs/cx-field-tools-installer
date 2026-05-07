# Testing Commands

## Quick reference

| Command | Purpose |
| ------- | ------- |
| `make run_tests` | Run all tests under [`tests/`](../../tests/). |
| `make run_tests_no_containers` | Run all tests except those marked `@pytest.mark.testcontainer`. |
| `make generate_test_data` | Copy `TEMPLATE_terraform.tfvars` into `tests/datafiles/` and seed core data. |
| `make generate_json_plan` | Produce `tfplan.json` from a fresh `terraform plan` for plan-based tests. |
| `make purge_cache` | Clear cached plans and templatefiles under `tests/`. |
| `make test_cleanse` | Remove generated `tests/datafiles/` artefacts. |

## Running specific test subsets

Pytest markers are defined in [`tests/pytest.ini`](../../tests/pytest.ini) — that file is authoritative; do not duplicate the marker list elsewhere.

```bash
# Plan-based tests only (no containers, no AWS)
pytest -m "local" -v

# Database tests
pytest -m "db" -v

# Redis tests
pytest -m "redis" -v

# Single test file or directory
pytest tests/unit/test_module_connection_strings/ -v -s -x
```

## Structured logging

Tests emit structured logs to `tests/logs/pytest_structured.log`. Parser tooling lives at [`tests/utils/log_parser.py`](../../tests/utils/log_parser.py):

```bash
# Summarise the most recent run
python tests/utils/log_parser.py summarize

# Extract failures
python tests/utils/log_parser.py extract-failures

# Format recent entries for LLM consumption
python tests/utils/log_parser.py llm-format --recent 100

# Validate log format
python tests/utils/log_parser.py validate

# Export as JSON
python tests/utils/log_parser.py export-json

# Tail in real-time during a run
tail -f tests/logs/pytest_structured.log
```
