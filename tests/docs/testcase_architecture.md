# Test Case Architecture (historical)

> **Superseded.** Canonical architecture: [`tests/new_implementation.md`](../new_implementation.md).
> Migration journey: [`test_assertion_retrofit.md`](./test_assertion_retrofit.md).

## What this used to be

The pre-retrofit architecture executed `terraform plan` per scenario, parsed the JSON output, and ran assertions via a three-layer pipeline:

- `prepare_plan(tf_modifiers)` ran and cached the plan.
- `assertion_modifiers_template()` + `generate_assertions_all_active()` produced the expected dict from `tests/datafiles/expected_results/expected_results.py`.
- `verify_all_assertions()` dispatched per-shape comparison.

The `TEST_FULL` env var toggled minimal vs. exhaustive file generation per testcase, and `desired_files` lists in each test selected the templates to render.

## What replaced it

- `terraform console` with a single mega-`jsonencode` expression resolves variables, locals, outputs, and rendered templatefiles in one call per scenario.
- Results land on disk in `tests/.scenario_cache/{hash}/` and are read at test time via the `generated_test_files` and `scenario_outputs` fixtures.
- Assertions live next to tests in `tests/unit/config_files/expected_deltas.py` as paired `<FEATURE>` (tfvars string) + `<FEATURE>_ASSERTIONS` (delta dict) constants. `merge_deltas(BASELINE_ASSERTIONS, ...)` composes the expected post-state. `assert_all_deltas` dispatches per-template.
- `desired_files` and `TEST_FULL` are gone. Every test renders the full set; cost is amortised across the session via per-scenario caching.

Use `git log -- tests/datafiles/expected_results/expected_results.py` to see the deleted helpers if archaeology is required.
