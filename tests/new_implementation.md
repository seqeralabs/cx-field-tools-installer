# New Test Case Architecture — Variables, Secrets, Outputs

How the test framework sources the three classes of input data that the previous
`parser.py:extract_config_values` used to bundle into a `TCValues` object.

After the precompute refactor, none of these flow through Python-side aggregation
during the test run. They're either resolved upfront by `terraform console` (and
landed on disk as JSON) or substituted into payloads by a single helper inside
the precompute worker.

---

## Data flow at a glance

```
Session start
  │
  └─> session_setup fixture (tests/conftest.py)
       │
       ├─ writes test tfvars files to the project root
       ├─ JSONifies 009_define_file_templates.tf  → 009_define_file_templates.json
       ├─ JSONifies 012_outputs.tf                → 012_outputs.json
       │
       └─> precompute_in_parallel(scenarios)  (tests/utils/terraform/precompute.py)
            │
            └─ Per scenario, in parallel (ProcessPoolExecutor):
                 ┌────────────────────────────────────────────────────────────────┐
                 │  _precompute_scenario(scenario_hash, tf_modifiers)             │
                 │                                                                │
                 │  1. Write tf_modifiers to /tmp/precompute-{hash}-XXXX.tfvars   │
                 │  2. Load secrets from JSON fixtures via _load_secrets()        │
                 │  3. For each template in 009.json:                             │
                 │       payload = `templatefile("path", {…})` HCL expression    │
                 │       _replace_refs(payload, secrets, ...)  ← Python sub      │
                 │  4. Build mega-jsonencode:                                     │
                 │       jsonencode({                                             │
                 │         locals    = { name = try(local.name, null), … },     │
                 │         outputs   = { name = <output_value_expr>, … },       │
                 │         templates = { tower_env = templatefile(…), … }       │
                 │       })                                                       │
                 │  5. terraform console -var-file=<tempfile> -state=<unique>    │
                 │     (pipes the mega-expression as stdin)                       │
                 │  6. Parse double-JSON response                                 │
                 │  7. Write to tests/.scenario_cache/{cache_key}/:               │
                 │       locals.json                                              │
                 │       outputs.json                                             │
                 │       tower_env.env, docker_compose.yml, …                    │
                 │  8. wave_lite_rds.sql via sedalternative.py (separate path)   │
                 └────────────────────────────────────────────────────────────────┘

Test runtime
  │
  ├─> generated_test_files fixture →  generate_tc_files  →  reads {template}.{ext} files
  └─> scenario_outputs fixture →  reads outputs.json
```

---

## Variables (`var.X`)

**Never extracted into Python at all.**

Each precompute worker writes its scenario's `tf_modifiers` to a tempfile and passes
`-var-file=<tempfile>` to `terraform console`. Terraform itself reads the tfvars when
resolving `var.X` references inside the mega-expression (it auto-loads the project's
`terraform.tfvars` and `base-overrides.auto.tfvars` from the project root too).

Tests don't see variable values directly — when an assertion needs to verify behaviour
that depends on a variable, it compares the **rendered** template output against the
expected literal value (e.g., `assert tower_env["TOWER_ROOT_USERS"] == "alice@example.com"`).

**Why this works:** the test framework intentionally has no Python-side knowledge of
"the current variable values" because terraform owns that resolution. The only thing
Python needs to know is which tfvars to stage — and that's captured at collection
time via `@pytest.mark.tfvars(...)`.

**Where:** [tests/utils/terraform/precompute.py](utils/terraform/precompute.py),
inside `_precompute_scenario`:

```python
with tempfile.NamedTemporaryFile(mode="w", suffix=".tfvars", …) as tf:
    tf.write(tf_modifiers)
    tfvars_path = Path(tf.name)
…
cmd = ["terraform", "console", f"-var-file={tfvars_path}", f"-state={state_path}"]
```

---

## Module outputs (`module.connection_strings.*`) and all 012_outputs.tf outputs

**Resolved by `terraform console` during precompute. Written to
`tests/.scenario_cache/{hash}/outputs.json`. Read at test time by the
`scenario_outputs` fixture.**

The precompute worker enumerates every output declared in `012_outputs.tf` (parsed
from `012_outputs.json`) and embeds each one's value expression directly into the
mega-jsonencode:

```python
output_expressions = discover_output_expressions()
# {"aws_account_id": "local.aws_account_id",
#  "tower_db_url":   "module.connection_strings.tower_db_url",
#  …}
outputs_body = ", ".join(f"{name} = {value_expr}" for name, value_expr in sorted(output_expressions.items()))
expr = f"jsonencode({{ … outputs = {{ {outputs_body} }}, … }})"
```

Console evaluates each expression naturally:
- Outputs that passthrough `module.connection_strings.X` → resolved by the module.
- Outputs that passthrough `local.X` (the resource-dependent ones — `aws_account_id`,
  `ec2_ssh_key`, etc.) → resolved by the two-layer defense in `locals.tf`.
- Outputs with a pure-ternary on `var.X` (e.g., `route53_record_status`) → resolved
  directly.

Result lands on disk as a flat `{name: value}` map. Test code reads it via the
`scenario_outputs` fixture (no plan, no AWS):

```python
@pytest.mark.tfvars("""…""")
def test_outputs_baseline_all_enabled(scenario_outputs):
    assert scenario_outputs["tower_db_url"] == "jdbc:mysql://db:3306/tower?…"
    assert scenario_outputs["aws_account_id"] == "N/A"
```

**Where:**
- Enumeration: [tests/utils/terraform/precompute.py](utils/terraform/precompute.py) — `discover_output_expressions()`.
- Two-layer defense for resource-dependent outputs: [locals.tf](../locals.tf).
- Output passthroughs: [012_outputs.tf](../012_outputs.tf).
- Test-side reader: `scenario_outputs` fixture in [tests/conftest.py](conftest.py),
  delegating to `read_scenario_outputs(tf_modifiers)`.

---

## Secrets

**Loaded from JSON fixtures by the precompute worker. Substituted textually into
templatefile payloads *before* the payload reaches `terraform console`.**

Secrets live in `tests/datafiles/secrets/*.json` and are read once per worker via
`_load_secrets()`:

```python
def _load_secrets() -> dict[str, dict]:
    raw = {
        "tower":       FP.TOWER_SECRETS,
        "groundswell": FP.GROUNDSWELL_SECRETS,
        "seqerakit":   FP.SEQERAKIT_SECRETS,
        "wave_lite":   FP.WAVE_LITE_SECRETS,
    }
    return {category: {k: v.get("value", v) for k, v in FileHelper.read_json(path).items()}
            for category, path in raw.items()}
```

For each templatefile expression, `_replace_refs` walks the payload string and
substitutes any `local.tower_secrets["KEY"]["value"]` (and the three other secret
flavours) with the literal value:

```python
payload = _replace_refs(payload, secrets["tower"],       "tower_secrets")
payload = _replace_refs(payload, secrets["groundswell"], "groundswell_secrets")
payload = _replace_refs(payload, secrets["seqerakit"],   "seqerakit_secrets")
payload = _replace_refs(payload, secrets["wave_lite"],   "wave_lite_secrets")
```

**Why textual substitution instead of letting console resolve it:** secrets aren't
a real terraform construct here — they're project JSON fixtures referenced via
`local.<X>_secrets[...]` in `009_define_file_templates.tf`. Terraform can resolve
those locals, but only because the production code populates them from
`data "aws_ssm_parameter"` resources that don't exist in test mode. Doing the
substitution in Python sidesteps the missing-resource problem entirely.

After substitution, the payload looks like:

```hcl
templatefile("…/tower.env.tpl", {
  …
  tower_db_user     = "tower_test_user",
  tower_db_password = "tower_test_password",
  …
})
```

Console then sees plain string literals where secret references used to be.

**Where:**
- Loader: [tests/utils/terraform/precompute.py](utils/terraform/precompute.py) — `_load_secrets()`.
- Substitution helper: [tests/utils/terraform/precompute.py](utils/terraform/precompute.py) — `_replace_refs()`.
- Per-template assembly: [tests/utils/terraform/precompute.py](utils/terraform/precompute.py) — `_build_template_payload()`.

---

## Locals (bonus, for completeness)

Locals don't flow into tests directly, but they're part of the same mega-expression:

```python
locals_to_resolve = discover_referenced_locals()  # walks 009.json minus the allowlist
locals_body = ", ".join(f"{n} = try(local.{n}, null)" for n in sorted(locals_to_resolve))
```

Resolved values land in `tests/.scenario_cache/{hash}/locals.json`. The only consumer
is the regression linter at
[tests/unit/framework/test_console_locals_resolvability.py](unit/framework/test_console_locals_resolvability.py),
which asserts every in-scope local resolved to a non-null value across every scenario.

The `try(local.X, null)` wrapper means a local that fails to resolve produces `null`
(rather than collapsing the whole mega-expression). The linter inspects each
`locals.json` and fails loudly if it sees `null`.

---

## Why no `TCValues` bundle anymore

`parser.py:extract_config_values` used to assemble `vars + outputs + 4 secret maps`
into a single `TCValues` object that was threaded through the rendering pipeline.
After the refactor:

- Variables don't need a Python bundle (terraform owns them).
- Outputs are on disk as JSON, accessed via a fixture.
- Secrets are loaded inside the precompute worker only, not shared with test code.

The `TCValues` class is now vestigial — its fields are still defined in
[tests/utils/config.py](utils/config.py) but nothing constructs or reads from them.
Slated for removal in a follow-up cleanup.

---

## Writing a test (the consumer side)

The sections above describe how data lands in `tests/.scenario_cache/{hash}/` during
session setup. This section walks through how an individual test consumes that data —
using `test_seqera_hosted_wave_active__retrofit` as the worked example.

### The test

```python
@pytest.mark.local
@pytest.mark.wave
@pytest.mark.tfvars(BASELINE + WAVE_SEQERA_HOSTED_ON)
def test_seqera_hosted_wave_active(generated_test_files):
    """Activating Seqera-hosted Wave from OFF baseline: assert every generated file vs OFF + Wave delta."""
    expected = merge_deltas(BASELINE_ASSERTIONS, WAVE_SEQERA_HOSTED_ON_ASSERTIONS)
    assert_all_deltas(generated_test_files, expected)
```

### The marker decorators (input setup)

```python
@pytest.mark.local
@pytest.mark.wave
```

Categorisation markers — let pytest filter via `-m`. Don't affect what the test does.

```python
@pytest.mark.tfvars(BASELINE + WAVE_SEQERA_HOSTED_ON)
```

The `tfvars` marker carries a **string** of terraform variable assignments. That string
is what eventually lands in the per-scenario `.tfvars` file the precompute worker writes
to a tempfile and passes to `terraform console`.

Constants live in [tests/unit/config_files/expected_deltas.py](unit/config_files/expected_deltas.py)
and come in **pairs** — one for each side of a test:

- `BASELINE` (tfvars string) / `BASELINE_ASSERTIONS` (assertion dict)
- `WAVE_SEQERA_HOSTED_ON` (tfvars string) / `WAVE_SEQERA_HOSTED_ON_ASSERTIONS` (assertion dict)

The two halves describe the same scenario from different sides — what to configure
(tfvars) and what should result (rendered file state). The naming convention makes drift
obvious in code review.

Net effect of the marker above: *"everything off, plus turn Wave on with this URL."*

### What happens between marker and test body

At pytest collection time, `tests/conftest.py:pytest_collection_modifyitems` walks every
collected test, reads its `tfvars` marker, hashes it, and registers the scenario in
`_collected_scenarios`. Then `session_setup` kicks off `precompute_in_parallel(...)` —
one worker per unique scenario — which renders the templatefiles, outputs, and locals
into `tests/.scenario_cache/{cache_key}/`.

By the time the test body runs, the files are already on disk.

### The fixture

**`generated_test_files`** (function-scoped) reads the test's own `tfvars` marker, computes
the same `hash_templatefile_cache_key`, looks up `tests/.scenario_cache/{hash}/`, and returns:

```python
{
  "tower_env":      {"content": <parsed .env dict>, "filepath": ".../tower_env.env"},
  "wave_lite_yml":  {"content": <parsed yaml>,      "filepath": ".../wave_lite_yml.yml"},
  ...
}
```

`generated_test_files["tower_env"]["content"]` is the rendered `.env` content for THIS
scenario, already parsed into `{key: value}`.

There is intentionally NO `BASELINE` fixture. The expected post-state for the OFF
scenario lives as a declarative constant — `BASELINE_ASSERTIONS` in
[tests/unit/config_files/expected_deltas.py](unit/config_files/expected_deltas.py) — and
is overlaid with per-feature delta constants via `merge_deltas(...)`.

### `merge_deltas` — composing the expected state

```python
expected = merge_deltas(BASELINE_ASSERTIONS, WAVE_SEQERA_HOSTED_ON_ASSERTIONS)
```

`BASELINE_ASSERTIONS` declares the expected `present` / `omitted` for every template
when only `BASELINE` is applied. `WAVE_SEQERA_HOSTED_ON_ASSERTIONS` declares the
per-feature deltas (paired with the tfvars-side `WAVE_SEQERA_HOSTED_ON` used in the
marker). `merge_deltas` walks both, per-template:

- `present` dicts are merged via `dict.update` — later wins on collision (`TOWER_ENABLE_WAVE`
  flips from `"false"` to `"true"`).
- `omitted` sets are merged via union.

Accepts any number of arguments — for tests that activate N features at once, pass them
all and later args win on key collision. The result is the expected post-state for
"OFF baseline + these features on" — fed to the assertion helpers via `**dict` spread.

**Convention for `<FEATURE>_ON_ASSERTIONS` constants.** Each captures the feature's
effects **assuming containerised defaults for every other knob** (container DB,
container Redis, etc.). Cross-feature interactions — e.g. external Redis flipping
Studios's `CONNECT_REDIS_ADDRESS`, or Wave-Lite + external Redis removing the
`wave-redis` container — are NOT baked into individual feature constants. Declare
them inline at the test site as an additional dict passed to `merge_deltas(...)`:

```python
expected = merge_deltas(
    BASELINE_ASSERTIONS,
    STUDIOS_ON_ASSERTIONS,
    REDIS_EXTERNAL_ON_ASSERTIONS,
    # Cross-feature: external Redis flips Studios's redis endpoint
    {"data_studios_env": {"present": {"CONNECT_REDIS_ADDRESS": "mock.tower-redis.com:6379"}}},
)
```

This keeps each feature constant composable — it produces the same effects whether
stacked with one feature or three.

### `assert_all_deltas` — the standard dispatcher

```python
assert_all_deltas(generated_test_files, expected)
```

Iterates every template in `expected`, looks up its `validation_type` from
`tests.utils.config.all_template_files`, and dispatches to the right per-shape helper
(`assert_kv_delta` / `assert_yaml_delta` / `assert_text_delta`).

**Strict mode.** Every template generated must have a matching entry in `expected`,
and vice versa. Missing on either side raises — test authors are forced to state
intent for every generated file. Templates whose entry has empty `present` AND empty
`omitted` are skipped (the explicit "not in scope" signal).

This is what almost every test should use — it catches drift in every generated file,
not just the ones the test author thought to check.

### Targeted assertions — direct per-shape helper calls

For the rare scenario where you genuinely want to check only specific templates
(narrow regression test, edge case where most files aren't meaningfully in scope),
call the per-shape helpers directly instead of going through `assert_all_deltas`:

```python
@pytest.mark.local
@pytest.mark.wave
@pytest.mark.tfvars(BASELINE + WAVE_SEQERA_HOSTED_ON)
def test_seqera_hosted_wave_active__targeted(generated_test_files):
    """Activating Seqera-hosted Wave: targeted checks on tower_env and wave_lite_yml only."""
    expected = merge_deltas(BASELINE_ASSERTIONS, WAVE_SEQERA_HOSTED_ON_ASSERTIONS)
    assert_kv_delta(
        test_file_path=generated_test_files["tower_env"]["filepath"],
        **expected["tower_env"],
    )
    assert_yaml_delta(
        test_file_path=generated_test_files["wave_lite_yml"]["filepath"],
        **expected["wave_lite_yml"],
    )
```

All three per-shape helpers ([tests/utils/assertions/delta.py](utils/assertions/delta.py))
share the same input contract:

- `test_file_path` — path to the rendered file on disk (the **standard** way to call them).
- `test_file_content` — pre-loaded content (parsed dict for kv/yaml; raw string for text).
  An escape hatch for tests that already have content in hand.

Exactly one of the two must be provided. If both are set, `test_file_path` wins and a
warning is issued.

| Helper | Content shape | `present` is… | `omitted` is… |
|---|---|---|---|
| `assert_kv_delta` | parsed `.env` dict | `{key: value}` to match | `{key1, key2, …}` to be absent |
| `assert_yaml_delta` | parsed YAML dict | `{yamlpath: value}` to match | `{yamlpath1, yamlpath2, …}` to be absent |
| `assert_text_delta` | raw text string | `{substring1, substring2, …}` that must appear | `{substring1, substring2, …}` that must not |

`expected["tower_env"]` is `{"present": {...}, "omitted": {...}}` — Python's `**dict`
expands that into keyword args alongside `test_file_path`.

No baseline-dict comparison anywhere. Tests assert against the explicit merged expectation.
"Everything else stayed the same" coverage comes from `BASELINE_ASSERTIONS` declaring
the expected post-state for every key the project cares about. Broader regression coverage
belongs in per-template **lock tests**.

### Test pattern data flow

```
@pytest.mark.tfvars(BASELINE + <FEATURE>_ON)        # input side  (paired)
                      │
                      ▼  collection time
              pytest_collection_modifyitems
                      │  builds {hash: tfvars} from every test's marker
                      ▼  session_setup
              precompute_in_parallel
                      │  one worker per unique scenario → terraform console → cache files
                      ▼  test runtime
              ┌──────────────────────┬─────────────────────────────────────────┐
              │                      │                                         │
       generated_test_files    BASELINE_ASSERTIONS    <FEATURE>_ON_ASSERTIONS  (output side, paired)
       (this scenario's       (declared expected         (the expected feature delta)
        rendered files)        OFF state)
              │                      │                                         │
              │                      └─────────────── merge_deltas ────────────┘
              │                                  │
              │                                  ▼
              │                          expected = {template: {present, omitted}}
              │                                  │
              └──────────────┬───────────────────┘
                             ▼
              assert_kv_delta / assert_yaml_delta / assert_text_delta
                             │
                             ▼ pass / fail
```

### Minimum vocabulary

To write a new test on this pattern you need:

1. **`BASELINE`** / **`BASELINE_ASSERTIONS`** — paired tfvars-string + assertion dict for "everything off"
2. **`<FEATURE>_ON`** / **`<FEATURE>_ON_ASSERTIONS`** — paired tfvars-string + assertion dict per feature
3. **`generated_test_files`** — fixture giving you THIS scenario's rendered files (parsed)
4. **`merge_deltas(BASELINE_ASSERTIONS, <FEATURE>_ON_ASSERTIONS, ...)`** — compose expected state
5. **`assert_kv_delta(actual, present, omitted)`** — for `.env` files
6. **`assert_yaml_delta(filepath, present, omitted)`** — for YAML files
7. **`assert_text_delta(content, present, omitted)`** — for plain-text rendered files (substring checks)

All paired constants live in
[tests/unit/config_files/expected_deltas.py](unit/config_files/expected_deltas.py).
That's the whole framework on the consumer side.

---

## Cheat sheet

If you need to know "where does this value come from at test time":

| Want… | Source | Read it via |
| --- | --- | --- |
| A rendered template file's content | `tests/.scenario_cache/{hash}/{template}.{ext}` | `generated_test_files` fixture |
| A `module.connection_strings.*` output | `tests/.scenario_cache/{hash}/outputs.json` | `scenario_outputs` fixture |
| Any output declared in `012_outputs.tf` | same `outputs.json` | same fixture |
| A resolved local (debugging only) | `tests/.scenario_cache/{hash}/locals.json` | open the JSON manually |
| A specific variable's current test value | check the `@pytest.mark.tfvars(…)` on the test, or `terraform.tfvars` + `base-overrides.auto.tfvars` at the project root | inspect the test source |

If you need to know "how did this value get there":

| For… | Producer |
| --- | --- |
| Templates + outputs + locals.json | [`tests/utils/terraform/precompute.py:_precompute_scenario`](utils/terraform/precompute.py) |
| `outputs.json` schema (which keys are present) | [`012_outputs.tf`](../012_outputs.tf) (every declared output is emitted) |
| `locals.json` schema (which keys are present) | references to `local.*` from [`009_define_file_templates.tf`](../009_define_file_templates.tf), minus the allowlist in [`tests/unit/framework/test_console_locals_resolvability.py`](unit/framework/test_console_locals_resolvability.py) |
| Per-scenario folder name (the `{hash}`) | [`tests/utils/cache/cache.py:hash_templatefile_cache_key`](utils/cache/cache.py) |
| The `{hash}` → test name mapping | [`tests/.scenario_cache/INDEX.md`](../tests/.scenario_cache/INDEX.md) (regenerated every session) |

---

## TODO: Test rename sweep (post-migration)

The Wave port set a naming precedent: when a test follows the pattern
`BASELINE + <FEATURE>_ON`, the test name should be `test_<feature>_active`
(verb "active" matches the per-feature semantic — Wave / Studios / Redis are *on*).

We deliberately kept the legacy test names during the migration to keep each port
change tightly scoped (one test = one port = one constant pair). Once all legacy
tests have been ported, do a single rename sweep using this table.

**Already renamed / restructured:**

| Old name | New name(s) | Status |
|---|---|---|
| `test_seqera_hosted_wave_active__retrofit` → `test_seqera_hosted_wave_active` | (replaced legacy `test_seqera_hosted_wave_active`) | ✅ Done |
| `test_redis_external_active` | `test_redis_external_active` *(pending rename)* | Ported to delta pattern; name still legacy |
| `test_new_redis_all_enabled` | `test_redis_external_with_studios` + `test_redis_external_with_wave_lite` | ✅ Split into two feature-pair tests (legacy deleted) |
| `test_existing_db_all_disabled` → `test_db_existing_active` | (renamed inline during port) | ✅ Done |
| `test_existing_db_all_enabled` | `test_db_existing_with_groundswell` + `test_db_existing_with_wave_lite` | ✅ Split into one feature-pair test + one documented non-interaction guard (legacy deleted) |
| `test_new_db_all_disabled` → `test_db_new_active` | (renamed inline during port) | ✅ Done |
| `test_new_db_all_enabled` | `test_db_new_with_groundswell` + `test_db_new_with_wave_lite` | ✅ Split into two feature-pair tests (legacy deleted) — note the asymmetry: new-DB × Wave-Lite IS a real interaction (RDS replaces container wave-db), unlike existing-DB × Wave-Lite which is documented as a non-interaction |
| `test_studio_path_routing_enabled` → `test_studios_path_routing_active` | (renamed inline during port) | ✅ Done. Modelled as a Studios sub-feature: `STUDIOS_ON + STUDIOS_PATH_ROUTING_ON`. Basic "Studios on with default URL" stays implicit in `test_baseline_alb_all_enabled`. |

**To rename when their legacy versions are ported:**

| Current name | Proposed new name | Notes |
|---|---|---|
| `test_studio_ssh_enabled` | `test_studios_ssh_active` | Same convention |
| `test_studio_ssh_enabled_workspace_restriction` | `test_studios_ssh_workspace_restriction_active` | Same convention |
| `test_studio_ssh_disabled` | `test_studios_active_ssh_inactive` | **Edge case** — Studios is on, but SSH is explicitly off. The compound name reflects the two-state assertion. Reconsider if a cleaner constant decomposition emerges. |
| ~~`test_new_db_all_disabled`~~ | `test_db_new_active` | ✅ Already ported + renamed |
| ~~`test_existing_db_all_disabled`~~ | `test_db_existing_active` | ✅ Already ported + renamed |
| `test_redis_external_active` | `test_redis_external_active` | Already ported; follows `REDIS_EXTERNAL_ON` constant naming |

**Pending design decision (all-on-baseline tests):**

The `_all_enabled` variants test "all features on baseline + this one feature variant".
There's no `ALL_ON_BASELINE` constant yet. Either we (a) define one and rename to
`test_<feature>_active__on_all_baseline`, or (b) treat the all-on baseline as
`merge_deltas(OFF, FEATURE_ON_1, FEATURE_ON_2, ...)` at the test site. The naming
follows whichever path we pick.

| Current name | Status |
|---|---|
| ~~`test_new_db_all_enabled`~~ | ✅ Split — see "already renamed / restructured" |
| ~~`test_existing_db_all_enabled`~~ | ✅ Split — see "already renamed / restructured" |
| ~~`test_new_redis_all_enabled`~~ | ✅ Split — see "already renamed / restructured" |

**Note on the feature-pair-split precedent:** when porting an `_all_enabled` test, prefer
splitting into focused feature-pair tests (each composing OFF baseline + 2 feature deltas
+ inline cross-feature delta) over defining an `ALL_ON_BASELINE_ASSERTIONS` constant.
The split surfaces feature interactions explicitly and avoids a ~90-entry catch-all
constant. Pattern set by `test_redis_external_with_studios` /
`test_redis_external_with_wave_lite`.

**Keep as-is (not delta-pattern tests):**

| Test | Why it stays |
|---|---|
| `test_baseline_alb_all_enabled` | Baseline regression test — its name describes the baseline itself, not a feature delta |
| `test_baseline_alb_all_disabled` | Same |
| `test_private_ca_reverse_proxy_active` | Already follows the `_active` convention |
| `test_wave_sql_file_content` | Lock-test pattern (full-file equality), not a delta test |
