# Python Linter Rule Decisions

Records project-level decisions on how ruff lint rule violations are handled. The active strict hook config is at `~/.config/precommit/ruff.toml`.

**Line length**: 120 characters. Matches the repo's [`ruff.toml`](../../ruff.toml).

**Auto-fixable rules**: any rule resolvable by `ruff check --fix` is accepted. Run the command, verify, commit. The table below covers rules that need a human decision per occurrence.

When you encounter a rule listed below while writing or editing Python, apply the recommended fix proactively — including in surrounding code if it has the same violation. Don't propagate the anti-pattern.

## Fix per linter recommendation

| Rule | What it catches | How to fix |
|------|----------------|------------|
| **B006** | Mutable default argument (`def f(x={})` / `def f(x=[])`) | Convert to `def f(x=None):` and initialise inside the function: `if x is None: x = {}` |
| **D200** | One-line docstring spans multiple lines | Collapse to a single line: `"""One sentence summary."""` |
| **D205** | No blank line between summary and description | Insert a blank line after the summary line |
| **D301** | Backslash in docstring without raw-string prefix | Change `"""..."""` to `r"""..."""` so backslashes (e.g. `\n` references) are literal. |
| **D405** | Section name not properly capitalised (e.g. `note` → `Note`) | Capitalise section headers (Google docstring convention) |
| **D415** | First docstring line doesn't end with `.`, `?`, or `!` | Add the trailing punctuation |
| **D417** | Missing argument descriptions in docstring | Document every parameter under `Args:`. If the docstring is stale, rewrite the Args block to match the current signature. |
| **DTZ005** | `datetime.datetime.now()` without `tz=` | Pass an explicit timezone (`tz=timezone.utc` for project-internal logs) |
| **E402** | Module-level import not at top of file | If `sys.path` manipulation precedes the import, suppress with `# noqa: E402` and a comment explaining why. Otherwise, move the import to the top. |
| **E501** | Line too long (>120 chars) | Wrap the line. For genuinely unwrappable content (long fixed URLs in dict values, single-quoted bash heredocs), suppress with `# noqa: E501  (<reason>)`. **Note**: `# noqa` inside a triple-quoted string literal is NOT honoured by ruff — refactor (e.g. extract to a separate variable) instead. |
| **F401** | Unused import | Delete the import. For placeholder modules where a future import is intended, prefer `# noqa: F401` with a one-line comment. |
| **N806** | Variable in function should be lowercase | Rename to lowercase. (Constants belong at module scope, not inside functions.) |
| **N816** | Mixed-case variable in module scope (e.g. `yamlParser`, `loggingArgs`) | Rename to `snake_case`. Module-scope variables follow Python convention regardless of any third-party library casing the project happens to mirror. |
| **PERF401** | `for ...: result.append(...)` pattern | Convert to a list comprehension |
| **PLR1714** | `value == A or value == B` chain | Use set membership: `value in {A, B}` |
| **PLW0602** | `global` declared without assignment in scope | Remove the `global` line. Variables can still be *read* from module scope without `global` — only assignments need it. |
| **PLW1510** | `subprocess.run` without explicit `check=` argument | Pass `check=False` explicitly to declare that ignoring exit codes is intentional. Use `check=True` only if you want non-zero exits to raise `CalledProcessError` — that's a behaviour change. |
| **PLW2901** | `for x in ...:` loop variable overwritten inside the body | Rename the loop variable so the original is preserved: `for raw_line in lines: line = raw_line.strip()` |
| **RUF013** | Implicit `Optional` (`x: int = None` with no `None` in annotation) | Make `None` explicit: `x: int \| None = None` |
| **S108** | Hardcoded `/tmp/...` path | Use `tempfile.NamedTemporaryFile(mode="w", suffix=".<ext>", delete=False)` with manual cleanup in a `finally` block. Pattern: write inside a `with` block to capture `tmp.name`, do work in a `try`, `os.unlink(tmp.name)` in `finally`. |
| **UP015** | Unnecessary `'r'` mode argument in `open()` | Drop the `'r'` — read is the default |
| **UP022** | `subprocess.run(stdout=PIPE, stderr=PIPE)` | Replace with `capture_output=True`. Drop both `stdout=PIPE` and `stderr=PIPE` lines — `capture_output` covers both. |
| **UP045** | Type annotation uses `Optional[X]` instead of `X \| None` | Convert to `X \| None` syntax (companion of RUF013) |

## Suppress at site (with reason)

When you encounter these rules, add `# noqa: <RULE>  (one-line reason)` at the end of the offending line. **Do not** suppress silently — the inline reason is mandatory. In production code (non-test), the rule should be properly addressed (parameterised query, validated scheme, etc.); escalate to the user before suppressing outside tests.

| Rule | What it catches | Why suppression is acceptable in tests |
|------|----------------|---------------------------------------|
| **PLR0915** | Function has too many statements (default threshold: 50) | Acceptable for one-shot test scaffolding (e.g. SSM secrets generation) where a linear top-to-bottom procedure is more readable than a forced split. Suppress with `# noqa: PLR0915  (test data generation; refactor not in scope)` on the function definition line. In production code, refactor instead. |
| **PT003** | `@pytest.fixture(scope="function")` — `function` is the default scope | Keep the explicit `scope="function"` for documentation value (makes fixture lifetime visible to readers); suppress with `# noqa: PT003  (explicit for documentation)`. |
| **PLW0603** | `global` statement to update module-level state | Pending refactor to class-based registry pattern (see TODO list). Suppress with `# noqa: PLW0603  (...; TODO refactor)` per occurrence in the meantime. |
| **S105** | Hardcoded password string | Test fixtures use literal passwords like `"test_password"` for local containers — never real credentials. Suppress with `# noqa: S105  (test fixture)`. |
| **S310** | `urllib.request.urlopen` accepts any URL scheme (file://, ftp://, custom) | Test URLs are hardcoded localhost endpoints; no scheme variation possible. |
| **S602** | `subprocess.run(..., shell=True)` | Used intentionally for shell features (`&&` chains, heredoc strings, `make` invocations). Inputs are hardcoded test paths/commands — no injection vector. Suppress with `# noqa: S602  (intentional shell features; inputs are hardcoded test ...)`. Co-locate with S607 noqa where both fire (`# noqa: S602, S607`). |
| **S607** | Process started with partial executable path (e.g. `["aws", ...]`, `["terraform", ...]`) | Test scripts rely on `$PATH` having the standard dev tools (`aws`, `terraform`, `make`). For multi-line `subprocess.run` calls, place the noqa on the **args-list line** (where ruff reports the violation), not the `subprocess.run(` line. Suppress with `# noqa: S607  (relies on PATH; standard for test env)`. |
| **S608** | SQL injection via string-based query construction | Test fixtures use hardcoded values; the `run_mysql_query` / `run_postgres_query` helpers shell out to the `mysql` / `psql` CLI rather than using a Python driver, so parameter binding isn't available without a framework refactor. |

## Deliberately ignored

These rules are silenced in the strict hook config (`~/.config/precommit/ruff.toml` `ignore = [...]`) — ruff will not flag them. Listed here so future agents know they're a deliberate project decision, not an oversight. Do **not** apply ruff's recommended fix proactively; if a future need arises, raise the question with the user.

| Rule | What it catches | Why ignored | Alternative if needed |
|------|----------------|-------------|----------------------|
| **SIM105** | `try / except E: pass` instead of `contextlib.suppress(E)` | Team prefers the familiarity of try/except for exception suppression. | `from contextlib import suppress; with suppress(KeyError): ...` is the linter-preferred form if you ever want it. |
| **SIM108** | Use ternary operator instead of `if`/`else` block | Team finds ternaries harder to read than the explicit `if`/`else` form, especially for non-trivial expressions. | `result = a if cond else b` is the linter-preferred form. |
| **TC001** | Move type-only application import behind `TYPE_CHECKING` | The pattern is most valuable in production modules with heavy import graphs or startup-cost concerns. Test files import a class for a single annotation — the `if TYPE_CHECKING:` ceremony costs more than it saves. | `from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from foo import Bar` is the linter-preferred form for production. |

## TODO / Follow-up

Rules with no final decision yet — revisit when explicitly asked.

| Rule | Notes |
|------|-------|
| **F841** | Unused local variable. 14 occurrences in `tests/`. Three patterns: (A) dead assignments where the call has side effects (drop `var =`); (B) `with ... as <name>` where name is unused inside the block (drop `as <name>`); (C) likely test-coverage gap in [`tests/unit/config_files/test_ansible_files.py`](../../tests/unit/config_files/test_ansible_files.py) — 6 tests build `tc_assertions = generate_assertions_*(...)` but never call `verify_all_assertions`. Pattern C requires per-test decisions on whether to add the missing call or delete the line. |
| **PLW0603** | `global` statement for singleton state. 3 occurrences. Currently suppressed per-line with noqa. The proper refactor is to convert [`tests/utils/pytest_logger.py`](../../tests/utils/pytest_logger.py)'s `_logger_instance` singleton (lines ~226, ~249) to a class-based registry (e.g. `_LoggerRegistry.get()` / `.reset()`), eliminating the need for `global`. The [`tests/conftest.py:175`](../../tests/conftest.py#L175) occurrence is a legitimate module-level assignment but flagged because the rule discourages `global` broadly — could be left suppressed even after refactoring the singleton. |

## How to update this file

When the user makes a decision on a new rule:
- "Fix" decisions go in the **Fix per linter recommendation** table.
- "Don't enforce" decisions go in the **Deliberately ignored** table.
- "Decide later" rules go in the **TODO / Follow-up** table.

Keep all tables sorted by rule code.
