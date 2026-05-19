# Test Assertion Retrofit (historical)

> **Complete.** This was the planning doc that drove the migration off `expected_results.py`.
> Canonical architecture: [`tests/new_implementation.md`](../new_implementation.md).

## What changed

| Before | After |
|---|---|
| Centralised `tests/datafiles/expected_results/expected_results.py` (586 lines) of `generate_*_all_active` / `_all_disabled` generators. | Per-feature paired constants in [`tests/unit/config_files/expected_deltas.py`](../unit/config_files/expected_deltas.py): `<FEATURE>` (tfvars string) and `<FEATURE>_ASSERTIONS` (delta dict). |
| `assertion_modifiers_template()` + `generate_assertions_all_active(tc_files, mods)`. | `merge_deltas(BASELINE_ASSERTIONS, FEATURE_ASSERTIONS, ...)` composes the expected post-state inline at the test site. |
| `verify_all_assertions()` dispatch over a `present`/`omitted` dict-of-dicts. | `assert_all_deltas(generated_test_files, expected)` strict-mode iterator, plus three per-shape helpers: `assert_kv_delta`, `assert_yaml_delta`, `assert_text_delta`. |
| `_all_enabled` / `_all_disabled` baselines maintained as twin code paths. | Single OFF baseline (`BASELINE_ASSERTIONS`). Every test composes upward from there. |

## Notable as-built differences vs. the original plan

- `BASELINE` became a declarative Python constant, not a session-scoped fixture reading rendered OFF state from disk. No cache dependency, drift is explicit.
- All three delta helpers share one signature (`test_file_path` / `test_file_content` + `present` / `omitted`). Baseline-diff coverage moved into `assert_all_deltas` instead of being baked into `assert_kv_delta`.
- `assert_all_deltas` strict-mode dispatcher emerged once `BASELINE_ASSERTIONS` was comprehensive; every generated template must have an entry, missing-on-either-side raises.
- `merge_deltas` is YAMLPath-prefix-aware so `services.wave-lite` (parent omitted) + `services.wave-lite.image` (child present) compose cleanly.
- Cross-feature interactions stay inline at test sites rather than being extracted into cross-product constants.
- "All-on + feature" scenarios got split into focused feature-pair tests (e.g. `test_db_new_with_groundswell`, `test_db_new_with_wave_lite`) instead of an `ALL_ON_BASELINE` mega-constant.

## What got deleted

- `tests/datafiles/expected_results/expected_results.py` (586 lines).
- `tests/utils/assertions/verify_assertions.py` (133 lines).
- `assertion_modifiers_template()`, `generate_assertions_all_active()`, `generate_assertions_all_disabled()`, `verify_all_assertions()`.

`tests/datafiles/expected_results/expected_sql/*.sql` survives — still used for full-file SQL lock comparison.

## Outstanding

- `test_ansible_files.py` was not migrated in this round; pending.
