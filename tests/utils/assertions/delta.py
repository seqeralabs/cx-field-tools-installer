"""Assertion helpers for the OFF-baseline + delta test pattern.

Three helpers, one per file shape:
  - `assert_kv_delta`   — `.env` files (flat key=value)
  - `assert_yaml_delta` — `.yml` / `.yaml` / `.json` files (nested)
  - `assert_text_delta` — `.sql` / `.sh` / `.conf` files (plain text; substring checks)

All three share the same keyword API:
  - `present`: what the file should contain (key/path → value for kv/yaml; substrings for text)
  - `omitted`: what the file should NOT contain (keys/paths for kv/yaml; substrings for text)

`present` covers both "new" and "modified" cases — it just asserts the post-state of the
file. Whether a key was in the OFF baseline with a different value or absent entirely is
irrelevant to the assertion.

No baseline-dict comparison anywhere. Tests declare the expected post-state by merging
`OFF_BASELINE_ASSERTIONS` with one or more per-feature delta constants via `merge_deltas`,
then call the right helper per template. Broader regression coverage belongs in per-template
lock tests.
"""

from pathlib import Path
import tempfile
from types import SimpleNamespace
from typing import Any
import warnings

from tests.utils.config import all_template_files
from tests.utils.filehandling import FileHelper
import yaml
from yamlpath import Processor, YAMLPath
from yamlpath.common import Parsers
from yamlpath.exceptions import UnmatchedYAMLPathException
from yamlpath.wrappers import ConsolePrinter, NodeCoords


# Shared yamlpath plumbing — lazily initialised once per process.
_logging_args = SimpleNamespace(quiet=True, verbose=False, debug=False)
_logger = ConsolePrinter(_logging_args)
_yaml_parser = Parsers.get_yaml_editor()


def _resolve_inputs(test_file_path, test_file_content, helper_name: str):
    """Mutual-exclusion / presence guard for the dual-input helpers.

    Returns (test_file_path, test_file_content). Raises ValueError if neither set.
    Warns and prefers `test_file_path` if both are set.
    """
    if test_file_path is None and test_file_content is None:
        raise ValueError(f"{helper_name}: must provide either test_file_path or test_file_content.")
    if test_file_path is not None and test_file_content is not None:
        warnings.warn(
            f"{helper_name}: both test_file_path and test_file_content set; using test_file_path.",
            stacklevel=3,
        )
        test_file_content = None
    return test_file_path, test_file_content


## ------------------------------------------------------------------------------------
## .env / key=value files
## ------------------------------------------------------------------------------------
def assert_kv_delta(
    *,
    test_file_path: str | Path | None = None,
    test_file_content: dict | None = None,
    present: dict | None = None,
    omitted: set[str] | None = None,
) -> None:
    """Assert a parsed `.env` file's content satisfies `present` and `omitted`.

    Input (one required):
      - `test_file_path`: path to the rendered `.env` file. Read + parsed via `FileHelper.parse_kv`.
      - `test_file_content`: pre-parsed `.env` content as a dict. Use when no on-disk file exists.
    If both are set, `test_file_path` wins and a warning is issued.

    Assertions:
      - Every key in `present` must be in the parsed content with the specified value.
      - Every key in `omitted` must not be in the parsed content.

    Values are compared via `str(...)` coercion to match how parsed `.env` content arrives
    (every value is a string regardless of what the test author typed).
    """
    test_file_path, test_file_content = _resolve_inputs(test_file_path, test_file_content, "assert_kv_delta")
    parsed = FileHelper.parse_kv(str(test_file_path)) if test_file_path is not None else test_file_content

    present = present or {}
    omitted = omitted or set()

    for key, value in present.items():
        assert str(parsed.get(key)) == str(value), f"{key}: expected {value!r}, got {parsed.get(key)!r}"  # noqa: S101  (assert is the helper's job)
    for key in omitted:
        assert key not in parsed, f"{key} should be absent but is present with value {parsed.get(key)!r}"  # noqa: S101


## ------------------------------------------------------------------------------------
## YAML / JSON files (nested; addressed by YAMLPath)
## ------------------------------------------------------------------------------------
def assert_yaml_delta(
    *,
    test_file_path: str | Path | None = None,
    test_file_content: dict | None = None,
    present: dict[str, Any] | None = None,
    omitted: set[str] | None = None,
) -> None:
    """Assert nested-structure YAML satisfies `present` and `omitted`.

    Input (one required):
      - `test_file_path`: path to the rendered YAML file. Read directly by `yamlpath`.
      - `test_file_content`: pre-parsed YAML content as a dict. Dumped to a tempfile for
        `yamlpath` consumption.
    If both are set, `test_file_path` wins and a warning is issued.

    Assertions:
      - `present` keys are YAMLPaths (e.g. `"services.tower-db.image"`). Each must exist
        with a value equal to (or that stringifies to) the specified value.
      - `omitted` keys are YAMLPaths that must NOT exist.

    No baseline comparison — YAML deltas in this project are always per-path. Broader
    regression coverage belongs in per-template lock tests.
    """
    test_file_path, test_file_content = _resolve_inputs(test_file_path, test_file_content, "assert_yaml_delta")
    present = present or {}
    omitted = omitted or set()

    tmp_path: str | None = None
    try:
        if test_file_path is not None:
            yaml_source = str(test_file_path)
        else:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as tmp:
                yaml.dump(test_file_content, tmp)
                tmp_path = tmp.name
            yaml_source = tmp_path

        yaml_data, document_loaded = Parsers.get_yaml_data(_yaml_parser, _logger, yaml_source)
        if not document_loaded:
            raise AssertionError(f"Could not load YAML from {yaml_source}")
        processor = Processor(_logger, yaml_data)

        for path, expected_value in present.items():
            try:
                nodes = list(processor.get_nodes(YAMLPath(path), mustexist=True))
            except UnmatchedYAMLPathException as e:
                raise AssertionError(f"YAMLPath {path!r} not found in {yaml_source}: {e}") from None
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
            raise AssertionError(f"YAMLPath {path!r} should be absent from {yaml_source} but exists")
    finally:
        if tmp_path is not None:
            Path(tmp_path).unlink(missing_ok=True)


## ------------------------------------------------------------------------------------
## Plain text files (substring checks)
## ------------------------------------------------------------------------------------
def assert_text_delta(
    *,
    test_file_path: str | Path | None = None,
    test_file_content: str | None = None,
    present: set[str] | None = None,
    omitted: set[str] | None = None,
) -> None:
    """Assert substring containment for plain-text rendered files.

    Input (one required):
      - `test_file_path`: path to the rendered text file. Read via `FileHelper.read_file`.
      - `test_file_content`: pre-loaded raw text content.
    If both are set, `test_file_path` wins and a warning is issued.

    Assertions:
      - `present` substrings must appear somewhere in the content.
      - `omitted` substrings must not appear.

    Used for files where structural parsing isn't appropriate (`.sql`, `.sh`, `.conf`) or
    where the existing tests already use substring-based assertions (ansible playbooks).
    """
    test_file_path, test_file_content = _resolve_inputs(test_file_path, test_file_content, "assert_text_delta")
    content = FileHelper.read_file(str(test_file_path)) if test_file_path is not None else test_file_content

    present = present or set()
    omitted = omitted or set()

    for needle in present:
        assert needle in content, f"Expected substring not found:\n  {needle!r}"  # noqa: S101  (assert is the helper's job)
    for needle in omitted:
        assert needle not in content, f"Substring should be absent but was found:\n  {needle!r}"  # noqa: S101


## ------------------------------------------------------------------------------------
## Whole-bundle dispatcher
## ------------------------------------------------------------------------------------
def assert_all_deltas(generated_test_files: dict, expected: dict) -> None:
    """Assert every rendered template in `generated_test_files` against `expected`.

    Strict-mode dispatcher — every template key in `generated_test_files` MUST have a
    matching entry in `expected`, and vice versa. Templates whose entry has empty
    `present` AND empty `omitted` are skipped (the explicit "not in scope" signal).
    Bare-empty (missing entry entirely) is a hard error, so test authors are forced to
    state intent for every generated file.

    Dispatches to `assert_kv_delta` / `assert_yaml_delta` / `assert_text_delta` based on
    each template's `validation_type` in `tests.utils.config.all_template_files`:
      - `"kv"`  → `assert_kv_delta`
      - `"yml"` → `assert_yaml_delta`
      - `"sql"` / `"TBD"` → `assert_text_delta` (substring checks; suitable for shell,
        ansible playbook substring assertions, conf files, SQL).

    Typical use:

        def test_x(generated_test_files):
            expected = merge_deltas(OFF_BASELINE_ASSERTIONS, FEATURE_ON_ASSERTIONS)
            assert_all_deltas(generated_test_files, expected)

    For one-off targeted assertions against a subset of templates, call the per-shape
    helpers directly instead.
    """
    generated_set = set(generated_test_files.keys())
    expected_set = set(expected.keys())

    missing_from_expected = generated_set - expected_set
    if missing_from_expected:
        raise AssertionError(
            f"assert_all_deltas: no expectations declared for templates {sorted(missing_from_expected)}. "
            "Add an entry to OFF_BASELINE_ASSERTIONS (use empty present/omitted for explicit opt-out).",
        )
    missing_from_generated = expected_set - generated_set
    if missing_from_generated:
        raise AssertionError(
            f"assert_all_deltas: expectations declared for templates not in generated_test_files: "
            f"{sorted(missing_from_generated)}. Remove stale entries.",
        )

    for template_name, parts in expected.items():
        present = parts.get("present") or {}
        omitted = parts.get("omitted") or set()
        if not present and not omitted:
            continue  # explicit opt-out

        filepath = generated_test_files[template_name]["filepath"]
        validation_type = all_template_files[template_name]["validation_type"]

        if validation_type == "kv":
            assert_kv_delta(test_file_path=filepath, present=present, omitted=omitted)
        elif validation_type == "yml":
            assert_yaml_delta(test_file_path=filepath, present=present, omitted=omitted)
        elif validation_type in {"sql", "TBD"}:
            assert_text_delta(test_file_path=filepath, present=present, omitted=omitted)
        else:
            raise AssertionError(
                f"assert_all_deltas: unknown validation_type {validation_type!r} for template {template_name!r}.",
            )


## ------------------------------------------------------------------------------------
## Composition helper
## ------------------------------------------------------------------------------------
def _is_dotted_prefix(prefix: str, full: str) -> bool:
    """True if `prefix` equals `full`, or is a dotted-path ancestor of `full`.

    Used to handle YAMLPath transitions: adding `services.wave-lite.image` to `present`
    should clear `services.wave-lite` from `omitted` (the parent path can't be both
    absent and have children present). For flat kv keys (no dots), this degenerates
    to exact-equality, so kv deltas behave identically.
    """
    if prefix == full:
        return True
    pseg = prefix.split(".")
    fseg = full.split(".")
    return len(pseg) < len(fseg) and fseg[: len(pseg)] == pseg


def _apply_present_to_dict_slot(slot: dict, present_in: dict) -> None:
    """Add `present_in` keys to the slot's `present` dict, clearing prefix matches from `omitted`."""
    for pkey in present_in:
        slot["omitted"] -= {okey for okey in slot["omitted"] if _is_dotted_prefix(okey, pkey)}
    slot["present"].update(present_in)


def _apply_omitted_to_dict_slot(slot: dict, omitted_in: set) -> None:
    """Add `omitted_in` to the slot's `omitted` set, clearing prefix matches from `present` dict."""
    for okey in omitted_in:
        slot["present"] = {pkey: v for pkey, v in slot["present"].items() if not _is_dotted_prefix(okey, pkey)}
    slot["omitted"] |= omitted_in


def merge_deltas(*deltas: dict[str, dict]) -> dict[str, dict]:
    """Merge feature-delta constants keyed by template name.

    Each input has the shape `{template: {"present": <dict|set>, "omitted": <set>}}`. Later
    deltas win on collision — both for value overrides (`present`) and for present↔omitted
    transitions:

      - For dict-shaped `present` (kv / yaml templates): adding a key to `present` removes
        it (and any YAMLPath-ancestor entries) from `omitted`. Adding a key to `omitted`
        removes it (and any descendant entries) from `present`.
      - For set-shaped `present` (text templates): adding to one removes exact matches
        from the other.

    The YAMLPath prefix semantics matter for cases like `OFF_BASELINE_ASSERTIONS` declaring
    `services.wave-lite` in `omitted` (parent absent) while `WAVE_LITE_ON_BASE_ASSERTIONS`
    declares `services.wave-lite.labels.seqera` in `present` — the parent must be cleared
    from `omitted` to avoid contradictory assertions.

    Example:
        merge_deltas(OFF_BASELINE_ASSERTIONS, SEQERA_HOSTED_WAVE_ON_ASSERTIONS) → a single
        nested dict whose `tower_env` entry contains both inputs' `present` keys (Wave's
        wins on collision) + the union of their `omitted` keys (with conflicts resolved).
    """
    out: dict[str, dict] = {}
    for delta in deltas:
        for template, parts in delta.items():
            present_in = parts.get("present")
            omitted_in = parts.get("omitted") or set()
            if template not in out:
                if isinstance(present_in, set):
                    out[template] = {"present": set(present_in), "omitted": set(omitted_in)}
                else:
                    out[template] = {"present": dict(present_in or {}), "omitted": set(omitted_in)}
                continue

            slot = out[template]
            if present_in:
                if isinstance(slot["present"], dict):
                    _apply_present_to_dict_slot(slot, present_in)
                else:
                    slot["present"] |= present_in
                    slot["omitted"] -= present_in
            if omitted_in:
                if isinstance(slot["present"], dict):
                    _apply_omitted_to_dict_slot(slot, omitted_in)
                else:
                    slot["present"] -= omitted_in
                    slot["omitted"] |= omitted_in
    return out
