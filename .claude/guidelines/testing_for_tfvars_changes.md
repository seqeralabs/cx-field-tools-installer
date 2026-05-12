# Testing for `terraform.tfvars` Variable Changes

## Scope

Applies when a PR adds, modifies, or removes a top-level `terraform.tfvars` variable that drives any generated artefact under [`assets/src/`](../../assets/src/) — `tower.yml`, `tower.env`, `docker-compose.yml`, `tower.sql`, Ansible files, Wave-Lite config, etc.

The framework only catches drift on assertions that exist. Hardcoded values in templates are silent test gaps until they become parameters; this protocol forces the gap to be filled at PR time. Background on the framework: [`testcase_architecture.md`](../../tests/testcase_architecture.md).

## Required steps

### 1. Update both baseline assertions

In [`tests/datafiles/expected_results/expected_results.py`](../../tests/datafiles/expected_results/expected_results.py), add the resulting key/value to BOTH `generate_<file>_entries_all_active` AND `generate_<file>_entries_all_disabled` for every artefact the variable affects.

Use the file-type-appropriate key syntax:

| File type | Key syntax | Example |
| --------- | ---------- | ------- |
| `*.yml` | YAMLPath (dot-separated) | `tower.participant.auto-create-user` |
| `*.env` | Plain key | `TOWER_DB_URL` |
| `*.sql` | Full-page compare via `tests/datafiles/expected_results/expected_sql/<file>.sql` | n/a |

For a binary feature flag, the two baselines should typically assert opposite values (`_all_active` = on, `_all_disabled` = off). For non-flag variables, both baselines may assert the same default.

### 2. Set the `_all_active`-side default in `base-overrides.auto.tfvars`

This is the project's preferred pattern: every test inherits the "all enabled" value by default, and `_all_disabled` tests list the explicit inverse overrides (step 3). The result is that `_all_active`-flavoured tests need minimal `tf_modifiers`, and the inversion is concentrated in `_all_disabled` tests where it's already idiomatic.

Edit the heredoc in [`tests/datafiles/generate_core_data.sh`](../../tests/datafiles/generate_core_data.sh) — add the variable to the appropriate section with its `_all_active` value. The next test run regenerates `tests/datafiles/base-overrides.auto.tfvars`, which is auto-loaded by `terraform plan` for every test.

**Don't conflate test convenience with deployment policy**: this does NOT change [`templates/TEMPLATE_terraform.tfvars`](../../templates/TEMPLATE_terraform.tfvars). The shipped default for new deployers stays untouched. Flipping the TEMPLATE default is a separate decision requiring CHANGELOG amendment per [`changelog_protocol.md`](changelog_protocol.md).

**Cache invalidation note**: changing `base-overrides.auto.tfvars` invalidates all cached terraform plans. The rebuild is automatic but takes minutes on first re-run.

**Exception — when NOT to use this approach**: if the variable is only relevant to one specific scenario (e.g., a private-CA test) rather than the general "all enabled" baseline, set it via per-test `tf_modifiers` in [`test_config_file_content.py`](../../tests/unit/config_files/test_config_file_content.py) instead. Default to base-overrides; fall back to per-test only when the variable is genuinely scenario-local.

### 3. Add inverse overrides to every `_all_disabled`-style test

Every test that calls `generate_assertions_all_disabled` must explicitly override the new flag(s) to the `_all_disabled` value in its `tf_modifiers`. Without this, those tests silently pass in default mode (the new key isn't in their narrow `desired_files`) but **fail under `TEST_FULL=true`**.

Find them with:

```bash
grep -n "generate_assertions_all_disabled" tests/unit/config_files/test_config_file_content.py
```

**Don't rely on test naming alone** — some tests like `test_seqera_hosted_wave_active` call `generate_assertions_all_disabled` despite an "active"-flavoured suffix.

### 4. Verify with `TEST_FULL=true` (required before merge)

Default `make run_tests` only validates files listed in each test's `desired_files`. A test can pass while leaving the new key entirely unvalidated, because the file containing it was never generated. **The PR is not solid until `TEST_FULL=true` passes.**

```bash
TEST_FULL=true pytest tests/unit/config_files
```

If `TEST_FULL` surfaces failures unrelated to your change, surface them to the user — don't silently chase them as part of this PR.

## Don't

- **Don't add a new testcase without explicit user authorization.** The two baselines (`_all_active` and `_all_disabled`) are usually sufficient for boolean flags. If you believe a new scenario test is needed, propose it to the user with justification — explain why the existing baselines can't cover the case (e.g., the flag interacts non-obviously with another flag, or it changes resource topology in a way that needs targeted assertion). Wait for sign-off before writing the test.
- **Don't change `templates/TEMPLATE_terraform.tfvars` defaults to simplify tests.** That's a deployment-policy change requiring CHANGELOG amendment and stakeholder review per [`changelog_protocol.md`](changelog_protocol.md).
- **Don't trust default-mode passing tests as proof of correctness** for assertions on files not in `desired_files`. Confirm with `TEST_FULL=true`.
