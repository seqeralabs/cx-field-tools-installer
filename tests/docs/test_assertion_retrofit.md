# Test Assertion Retrofit — One-Pager

Plan for flattening the test assertion machinery so per-test verifications live close to
the test body, share a single baseline, and cover multiple file types with a uniform API.

## Goals

1. **Flatten the testing structure** — assertions in the test body or one import away,
   not chased through `expected_results.py` + `assertion_modifiers_template` +
   `generate_assertions_all_active` + `verify_all_assertions`.
2. **Single OFF baseline** — every flag/feature off by default. Tests turn things on
   from there. No "all enabled" baseline to juggle.
3. **DRY for shared deltas** — when multiple tests assert the same feature's effect,
   express that effect once as a named constant; tests compose them.
4. **Two delta keywords: `present` and `omitted`** — `present` covers new-or-modified
   keys (whichever way the value got there); `omitted` covers absences.
5. **Cover .env, YAML, and plain-text rendered files** — uniform API per file type.

## Core moves

| Concept | What it is |
|---|---|
| `BASELINE` | A single module-level tfvars string that turns off every default-on flag. Every test stages this + its own activations. |
| `BASELINE` (fixture) | Parsed rendered outputs from the OFF scenario, keyed by template name. Auto-derived from `tests/.scenario_cache/{hash}/`. |
| `assert_kv_delta` | Helper for `.env`-shaped files. Diffs against `BASELINE` using `present` / `omitted`. |
| `assert_yaml_delta` | Helper for `.yml` / `.json` files. Per-path assertions (no full baseline diff — covered by template lock test). |
| `assert_text_delta` | Helper for plain-text files (`.sh`, `.sql`, `.conf`). Substring `present` / `omitted`. |
| Feature-delta constants | Per-feature dicts (one per template the feature touches) capturing what `present` / `omitted` mean when that feature is activated. Tests compose via `{**A, **B}`. |
| One **lock test** per template | Comprehensive hardcoded assertions on the OFF baseline content. Catches framework regressions; the only place "this baseline really should look like X" is enumerated. |

## Helper API

All three accept `present` (what should be in the file with this value/substring) and
`omitted` (what should not be in the file).

```python
def assert_kv_delta(actual: dict, baseline: dict, *,
                    present: dict | None = None,
                    omitted: set | None = None) -> None: ...

def assert_yaml_delta(filepath: str, *,
                      present: dict[str, str] | None = None,  # YAMLPath → expected value
                      omitted: set[str] | None = None) -> None: ...

def assert_text_delta(content: str, *,
                      present: set[str] | None = None,    # substrings that must appear
                      omitted: set[str] | None = None) -> None: ...  # substrings that must NOT appear
```

`assert_kv_delta` diffs against `baseline` (so unchanged keys are still verified).
`assert_yaml_delta` and `assert_text_delta` skip the baseline-diff — broader regression
coverage for those file types lives in their lock tests.

`present` semantics: the key/substring **must be in the actual rendered output with the
specified value**. Whether it was new or modified from baseline is irrelevant — captures
both cases under one keyword.

## Test shape

```python
# tests/unit/config_files/expected_deltas.py

NO_HTTPS_TOWER_ENV = {
    "TOWER_SERVER_URL":   "http://autodc.dev-seqera.net:8000",
    "TOWER_API_ENDPOINT": "http://autodc.dev-seqera.net:8000/api",
}

EXTERNAL_DB_TOWER_ENV = {
    "TOWER_DB_URL": "jdbc:mysql://mock.tower-db.com:3306/tower?…",
}

EXTERNAL_DB_DOCKER_COMPOSE_OMITTED = {
    "services.tower-db",
}
```

```python
# tests/unit/config_files/test_config_file_content.py

@pytest.mark.tfvars(BASELINE + "flag_do_not_use_https = true")
def test_no_https_changes_urls(staged_scenario, BASELINE):
    assert_kv_delta(
        actual=staged_scenario["tower_env"]["content"],
        baseline=BASELINE["tower_env"],
        present=NO_HTTPS_TOWER_ENV,
    )


@pytest.mark.tfvars(BASELINE + """
    flag_create_external_db = true
    flag_use_container_db   = false
""")
def test_external_db_replaces_container(staged_scenario, BASELINE):
    assert_kv_delta(
        actual=staged_scenario["tower_env"]["content"],
        baseline=BASELINE["tower_env"],
        present=EXTERNAL_DB_TOWER_ENV,
    )
    assert_yaml_delta(
        filepath=staged_scenario["docker_compose"]["filepath"],
        omitted=EXTERNAL_DB_DOCKER_COMPOSE_OMITTED,
    )
```

## DRY shape for multi-file deltas

When a feature touches multiple files, nest the constant by template name:

```python
GROUNDSWELL_ON = {
    "tower_env": {
        "TOWER_ENABLE_GROUNDSWELL": "true",
        "GROUNDSWELL_SERVER_URL":   "http://groundswell:8090",
    },
    "docker_compose": {
        "services.groundswell.labels.seqera": "groundswell",
    },
}
```

Tests loop or pick by template:

```python
def test_groundswell_only(staged_scenario, BASELINE):
    for tpl, additions in GROUNDSWELL_ON.items():
        if tpl == "docker_compose":
            assert_yaml_delta(filepath=staged_scenario[tpl]["filepath"], present=additions)
        else:
            assert_kv_delta(actual=staged_scenario[tpl]["content"],
                            baseline=BASELINE[tpl],
                            present=additions)
```

Combining features: `{**A, **B}` for dicts, `A | B` for sets. A tiny `merge_deltas`
helper exists for the nested case where two features both touch `tower_env`.

## What gets deleted in the retrofit

- `tests/datafiles/expected_results/expected_results.py` (586 lines) — replaced by
  per-feature constants colocated with tests.
- `assertion_modifiers_template()` / `generate_assertions_all_active()` /
  `generate_assertions_all_disabled()` — superseded.
- `verify_all_assertions()` dispatch — replaced by direct calls to the three new helpers.
- The `present` / `omitted` dict-of-dicts shape in test bodies — flattened.

`tests/utils/assertions/verify_assertions.py` shrinks dramatically (or splits into the
three new helpers).

## File layout after retrofit

```
tests/utils/assertions/
  kv_delta.py         ← assert_kv_delta
  yaml_delta.py       ← assert_yaml_delta + the YAMLPath glue
  text_delta.py       ← assert_text_delta
  merge.py            ← merge_deltas helper

tests/unit/config_files/
  expected_deltas.py  ← BASELINE constant + feature-delta constants
  test_baseline.py    ← per-template OFF-baseline lock tests
  test_config_file_content.py   ← per-feature tests, granular
  test_ansible_files.py         ← unchanged in shape; uses assert_text_delta
  test_outputs.py               ← unchanged in shape; reads scenario_outputs
  test_testcontainer_execution.py ← unchanged
```

## Migration order

1. Land helpers + `BASELINE` constant + `BASELINE` fixture. Don't touch tests yet.
2. Write the lock test for `tower_env` against `BASELINE`. Sanity-check.
3. Migrate ONE existing test (e.g., `test_studio_path_routing_enabled`) end-to-end.
   Confirm the shape feels right.
4. Sweep the rest of `test_config_file_content.py` (~15 tests). Mechanical.
5. Migrate `test_ansible_files.py` to `assert_text_delta` (already substring-based, low risk).
6. Delete `expected_results.py` once nothing references it.
7. Run full suite, commit.

Step 3 is the decision gate — if the shape doesn't feel right after one real conversion,
back out cheaply.
