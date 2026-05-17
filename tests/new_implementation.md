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
  ├─> staged_scenario fixture  →  generate_tc_files  →  reads {template}.{ext} files
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

## Cheat sheet

If you need to know "where does this value come from at test time":

| Want… | Source | Read it via |
| --- | --- | --- |
| A rendered template file's content | `tests/.scenario_cache/{hash}/{template}.{ext}` | `staged_scenario` fixture |
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
