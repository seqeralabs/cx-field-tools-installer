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
| **D405** | Section name not properly capitalised (e.g. `note` → `Note`) | Capitalise section headers (Google docstring convention) |
| **D415** | First docstring line doesn't end with `.`, `?`, or `!` | Add the trailing punctuation |
| **DTZ005** | `datetime.datetime.now()` without `tz=` | Pass an explicit timezone (`tz=timezone.utc` for project-internal logs) |
| **E402** | Module-level import not at top of file | If `sys.path` manipulation precedes the import, suppress with `# noqa: E402` and a comment explaining why. Otherwise, move the import to the top. |
| **F401** | Unused import | Delete the import. For placeholder modules where a future import is intended, prefer `# noqa: F401` with a one-line comment. |
| **N806** | Variable in function should be lowercase | Rename to lowercase. (Constants belong at module scope, not inside functions.) |
| **PERF401** | `for ...: result.append(...)` pattern | Convert to a list comprehension |
| **PLW1510** | `subprocess.run` without explicit `check=` argument | Pass `check=False` explicitly to declare that ignoring exit codes is intentional. Use `check=True` only if you want non-zero exits to raise `CalledProcessError` — that's a behaviour change. |
| **RUF013** | Implicit `Optional` (`x: int = None` with no `None` in annotation) | Make `None` explicit: `x: int \| None = None` |
| **UP015** | Unnecessary `'r'` mode argument in `open()` | Drop the `'r'` — read is the default |
| **UP045** | Type annotation uses `Optional[X]` instead of `X \| None` | Convert to `X \| None` syntax (companion of RUF013) |

## Deliberately ignored

These rules are project-deliberate exceptions. Do **not** apply ruff's recommended fix for these; do not silently suppress with `# noqa` either — they're known and tolerated.

| Rule | What it catches | Why ignored | Alternative if needed |
|------|----------------|-------------|----------------------|
| **SIM105** | `try / except E: pass` instead of `contextlib.suppress(E)` | Team prefers the familiarity of try/except for exception suppression. | `from contextlib import suppress; with suppress(KeyError): ...` is the linter-preferred form if you ever want it. |

## TODO / Follow-up

Rules with no final decision yet — revisit when explicitly asked.

| Rule | Notes |
|------|-------|
| **F841** | Unused local variable. 14 occurrences in `tests/`. Three patterns: (A) dead assignments where the call has side effects (drop `var =`); (B) `with ... as <name>` where name is unused inside the block (drop `as <name>`); (C) likely test-coverage gap in [`tests/unit/config_files/test_ansible_files.py`](../../tests/unit/config_files/test_ansible_files.py) — 6 tests build `tc_assertions = generate_assertions_*(...)` but never call `verify_all_assertions`. Pattern C requires per-test decisions on whether to add the missing call or delete the line. |

## How to update this file

When the user makes a decision on a new rule:
- "Fix" decisions go in the **Fix per linter recommendation** table.
- "Don't enforce" decisions go in the **Deliberately ignored** table.
- "Decide later" rules go in the **TODO / Follow-up** table.

Keep all tables sorted by rule code.
