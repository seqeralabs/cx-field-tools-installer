"""Assertion helpers for the OFF-baseline + delta test pattern.

Three helpers, one per file shape:
  - `assert_kv_delta`   — `.env` files (flat key=value)
  - `assert_yaml_delta` — `.yml` / `.yaml` / `.json` files (nested)
  - `assert_text_delta` — `.sql` / `.sh` / `.conf` files (plain text; substring checks)

All three share the same keyword API:
  - `present`: what the file should contain (key/path → value for kv/yaml; substrings for text)
  - `omitted`: what the file should NOT contain (keys/paths for kv/yaml; substrings for text)

`present` covers both "new" and "modified" cases — it just asserts the post-state of the
file. Whether a key was in the baseline with a different value or absent entirely is
irrelevant to the assertion.

`assert_kv_delta` is the only helper that takes a `baseline` parameter. It asserts every
baseline key (minus those in `omitted`) is still present with its baseline value, plus
everything in `present`. YAML and text helpers don't compare against a baseline —
broader regression coverage for those file types belongs in per-template lock tests.
"""

from types import SimpleNamespace
from typing import Any

from yamlpath import Processor, YAMLPath
from yamlpath.common import Parsers
from yamlpath.exceptions import UnmatchedYAMLPathException
from yamlpath.wrappers import ConsolePrinter, NodeCoords


# Shared yamlpath plumbing — lazily initialised once per process.
_logging_args = SimpleNamespace(quiet=True, verbose=False, debug=False)
_logger = ConsolePrinter(_logging_args)
_yaml_parser = Parsers.get_yaml_editor()


## ------------------------------------------------------------------------------------
## .env / key=value files
## ------------------------------------------------------------------------------------
def assert_kv_delta(
    actual: dict,
    baseline: dict,
    *,
    present: dict | None = None,
    omitted: set[str] | None = None,
) -> None:
    """Assert `actual` matches `baseline` modulo `present` and `omitted`.

    - Every baseline key that's NOT in `omitted` must be in `actual` with its baseline value.
    - Every key in `present` must be in `actual` with the specified value (overrides baseline
      on collision — covers both "new" and "modified" cases).
    - Every key in `omitted` must not be in `actual`.

    Values are compared via `str(...)` coercion to match how parsed `.env` content arrives
    (every value is a string regardless of what the test author typed).
    """
    present = present or {}
    omitted = omitted or set()

    expected = {k: v for k, v in baseline.items() if k not in omitted}
    expected.update(present)

    for key, value in expected.items():
        assert str(actual.get(key)) == str(value), f"{key}: expected {value!r}, got {actual.get(key)!r}"  # noqa: S101  (assert is the helper's job)
    for key in omitted:
        assert key not in actual, f"{key} should be absent but is present with value {actual.get(key)!r}"  # noqa: S101


## ------------------------------------------------------------------------------------
## YAML / JSON files (nested; addressed by YAMLPath)
## ------------------------------------------------------------------------------------
def assert_yaml_delta(
    filepath: str,
    *,
    present: dict[str, Any] | None = None,
    omitted: set[str] | None = None,
) -> None:
    """Assert nested-structure file at `filepath` satisfies `present` and `omitted`.

    `present` keys are YAMLPaths (e.g. `"services.tower-db.image"`). Each one must exist
    in the file with a value equal to (or that stringifies to) the specified value.

    `omitted` keys are YAMLPaths that must NOT exist in the file.

    No baseline comparison — YAML deltas in this project are always per-path. Broader
    regression coverage belongs in per-template lock tests.
    """
    present = present or {}
    omitted = omitted or set()

    yaml_data, document_loaded = Parsers.get_yaml_data(_yaml_parser, _logger, filepath)
    if not document_loaded:
        raise AssertionError(f"Could not load YAML from {filepath}")
    processor = Processor(_logger, yaml_data)

    for path, expected_value in present.items():
        try:
            nodes = list(processor.get_nodes(YAMLPath(path), mustexist=True))
        except UnmatchedYAMLPathException as e:
            raise AssertionError(f"YAMLPath {path!r} not found in {filepath}: {e}") from None
        for node_coord in nodes:
            actual_value = NodeCoords.unwrap_node_coords(node_coord)
            assert str(actual_value) == str(expected_value), (  # noqa: S101  (assert is the helper's job)
                f"{path}: expected {expected_value!r}, got {actual_value!r}"
            )

    for path in omitted:
        try:
            list(processor.get_nodes(YAMLPath(path), mustexist=True))
        except UnmatchedYAMLPathException:
            continue  # absent as required
        raise AssertionError(f"YAMLPath {path!r} should be absent from {filepath} but exists")


## ------------------------------------------------------------------------------------
## Plain text files (substring checks)
## ------------------------------------------------------------------------------------
def assert_text_delta(
    content: str,
    *,
    present: set[str] | None = None,
    omitted: set[str] | None = None,
) -> None:
    """Assert substring containment for plain-text rendered files.

    `present` substrings must appear somewhere in `content`. `omitted` substrings must not.

    Used for files where structural parsing isn't appropriate (`.sql`, `.sh`, `.conf`) or
    where the existing tests already use substring-based assertions (ansible playbooks).
    """
    present = present or set()
    omitted = omitted or set()

    for needle in present:
        assert needle in content, f"Expected substring not found:\n  {needle!r}"  # noqa: S101  (assert is the helper's job)
    for needle in omitted:
        assert needle not in content, f"Substring should be absent but was found:\n  {needle!r}"  # noqa: S101


## ------------------------------------------------------------------------------------
## Composition helper
## ------------------------------------------------------------------------------------
def merge_deltas(*deltas: dict[str, dict]) -> dict[str, dict]:
    """Deep-merge feature-delta dicts keyed by template name.

    Each input is `{template_name: {key_or_path: value, ...}}`. Output is the same shape,
    with the per-template inner dicts merged (later inputs override earlier ones on key
    collision within the same template).

    For combining the `omitted` halves of multiple features, set-union is simpler — use
    `A | B` directly rather than calling this helper.
    """
    out: dict[str, dict] = {}
    for delta in deltas:
        for template, keys in delta.items():
            out.setdefault(template, {}).update(keys)
    return out
