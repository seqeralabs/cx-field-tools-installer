#!/usr/bin/env python3
"""Schema-driven completeness check for `terraform.tfvars` during upgrades.

Compares the customer's `terraform.tfvars` against the authoritative schema in
`variables.tf` (and the suggested-defaults source `templates/TEMPLATE_terraform.tfvars`)
and reports:

  - MISSING — variables declared in `variables.tf` but absent from the customer's tfvars.
              Required variables (no `default` in `variables.tf`) will block
              `terraform plan`; optional ones won't, but are still flagged so the
              customer can opt in.
  - EXTRA   — assignments in the customer's tfvars for variables no longer declared
              upstream. Terraform will warn or error depending on version.
  - TYPE    — variables present in both but with a value whose top-level shape does
              not match the declared type (e.g. upstream changed `string` to `object`).

The script is **strictly read-only**. It never modifies the customer's tfvars,
TEMPLATE, or any other project file. Output goes to stdout; missing-variable entries
include a copy-paste-ready snippet harvested from TEMPLATE_terraform.tfvars together
with the comment block immediately above each declaration.

Exit codes:
    0 — no required-missing variables and no type issues
    1 — at least one required variable missing or one type-incompatibility
        (optional-missing and extra entries do not affect the exit code)

Usage:
    python scripts/installer/validation/check_upgrade.py
    python scripts/installer/validation/check_upgrade.py --tfvars path/to/customer.tfvars
    python scripts/installer/validation/check_upgrade.py --no-color
"""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


# Locate the project root (..) and inject `scripts/` so we can import `installer.utils.*`.
BASE_IMPORT_DIR = Path(__file__).resolve().parents[2]
if str(BASE_IMPORT_DIR) not in sys.path:
    sys.path.append(str(BASE_IMPORT_DIR))

from installer.utils.extractors import hcl_to_json  # noqa: E402  (sys.path manipulation above)


# Project root — `..` from this file's directory.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
VARIABLES_TF = PROJECT_ROOT / "variables.tf"
TEMPLATE_TFVARS = PROJECT_ROOT / "templates" / "TEMPLATE_terraform.tfvars"
DEFAULT_CUSTOMER_TFVARS = PROJECT_ROOT / "terraform.tfvars"
MAIN_TF = PROJECT_ROOT / "000_main.tf"

# Static list of AWS regions for sanity-checking `aws_region`. Kept here rather than
# fetched dynamically because (a) regions change rarely, (b) we don't want this script
# making API calls before we've verified auth, and (c) the failure mode for a typo is
# obvious enough that the customer can self-correct.
_KNOWN_AWS_REGIONS = frozenset(
    {
        "us-east-1",
        "us-east-2",
        "us-west-1",
        "us-west-2",
        "af-south-1",
        "ap-east-1",
        "ap-northeast-1",
        "ap-northeast-2",
        "ap-northeast-3",
        "ap-south-1",
        "ap-south-2",
        "ap-southeast-1",
        "ap-southeast-2",
        "ap-southeast-3",
        "ap-southeast-4",
        "ca-central-1",
        "ca-west-1",
        "eu-central-1",
        "eu-central-2",
        "eu-north-1",
        "eu-south-1",
        "eu-south-2",
        "eu-west-1",
        "eu-west-2",
        "eu-west-3",
        "il-central-1",
        "me-central-1",
        "me-south-1",
        "sa-east-1",
    }
)

# `${var.aws_profile}` style interpolation in `provider "aws"` block — used to map
# provider config back to the tfvars var that supplies it.
_VAR_INTERPOLATION_RE = re.compile(r"^\$\{var\.([A-Za-z_][A-Za-z0-9_]*)\}$")


# ANSI colour helpers — neutralised by `--no-color`.
class Colour:
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    @classmethod
    def disable(cls) -> None:
        for attr in ("RED", "GREEN", "YELLOW", "CYAN", "BOLD", "DIM", "RESET"):
            setattr(cls, attr, "")


# -------------------------------------------------------------------------------
# Schema extraction
# -------------------------------------------------------------------------------
_TYPE_EXPR_RE = re.compile(r"^\$\{(.*)\}$", re.DOTALL)
_TYPE_HEAD_RE = re.compile(r"^([A-Za-z_]+)")


def parse_schema(variables_tf_path: Path) -> dict[str, dict]:
    """Parse `variables.tf` and return `{name: {type, type_head, has_default, default}}`.

    `type_head` is the outermost type constructor name (`list`, `object`, `string`, …),
    used for the type-compat check. We deliberately do not recurse into composite type
    arguments — that would require an HCL type-expression parser and the failure modes
    we care about (e.g. `string` → `object`) are caught at the top level.
    """
    parsed = hcl_to_json(str(variables_tf_path))
    raw = parsed.get("variable", {})
    schema: dict[str, dict] = {}
    for name, attrs_list in raw.items():
        # HCL allows multiple `variable "foo" {}` blocks; hcl2json returns a list. In
        # this codebase each name is declared once — take the first entry.
        attrs = attrs_list[0] if isinstance(attrs_list, list) and attrs_list else {}
        type_raw = attrs.get("type", "")
        # Strip the `${...}` Terraform-expression wrapper hcl2json applies to type exprs.
        m = _TYPE_EXPR_RE.match(type_raw)
        type_inner = (m.group(1) if m else type_raw).strip()
        head_match = _TYPE_HEAD_RE.match(type_inner)
        type_head = head_match.group(1) if head_match else type_inner
        schema[name] = {
            "type": type_inner,
            "type_head": type_head,
            "has_default": "default" in attrs,
            "default": attrs.get("default"),
            "description": attrs.get("description", ""),
        }
    return schema


# -------------------------------------------------------------------------------
# Customer / TEMPLATE assignment extraction
# -------------------------------------------------------------------------------
def parse_assignments(tfvars_path: Path) -> dict:
    """Parse a tfvars file and return a flat `{name: value}` dict."""
    return hcl_to_json(str(tfvars_path))


def index_template_lines(template_path: Path) -> dict[str, int]:
    """Index the line number at which each top-level assignment starts in TEMPLATE.

    Detects assignments by `^<identifier>\\s*=` at column 0 (no indentation). Skips
    comment lines and indented assignments (which belong to nested object/map values).
    """
    line_index: dict[str, int] = {}
    pattern = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=")
    text = template_path.read_text()
    for lineno, line in enumerate(text.splitlines(), start=1):
        m = pattern.match(line)
        if m:
            name = m.group(1)
            # If the same name appears twice (shouldn't, in a well-formed template),
            # prefer the first occurrence.
            line_index.setdefault(name, lineno)
    return line_index


def get_template_comment_context(template_path: Path, assignment_line: int) -> list[str]:
    """Walk backwards from an assignment line to collect its leading comment block.

    Stops at:
      - a blank line
      - a non-comment line (including the previous variable's assignment)
      - line 1 (top of file)

    Returns the comment lines in original (top-to-bottom) order, stripped of trailing
    whitespace but with leading `#` intact for caller formatting.
    """
    text = template_path.read_text()
    all_lines = text.splitlines()
    context: list[str] = []
    # `assignment_line` is 1-based; `all_lines` is 0-based; the line directly above
    # the assignment is at index `assignment_line - 2`.
    i = assignment_line - 2
    while i >= 0:
        stripped = all_lines[i].strip()
        if not stripped:
            break
        if not stripped.startswith("#"):
            break
        context.insert(0, all_lines[i].rstrip())
        i -= 1
    return context


# -------------------------------------------------------------------------------
# Type-compatibility check
# -------------------------------------------------------------------------------
def value_top_shape(value) -> str:
    """Return the top-level shape of a (post-hcl2json) value, matching HCL type heads.

    hcl2json maps:
      - HCL string         → Python str   → "string"
      - HCL number         → Python int/float → "number"
      - HCL bool           → Python bool  → "bool"
      - HCL list/tuple     → Python list  → "list"
      - HCL map/object     → Python dict  → "object" (we conflate map and object — both
                                                      look the same post-parse and the
                                                      distinction rarely affects compat)
      - HCL null           → Python None  → "null"
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        # NB: must precede `int` check — booleans are ints in Python.
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "object"
    return "unknown"


# Top-level heads that are interchangeable for the purposes of this check.
_HEAD_ALIASES = {
    "tuple": "list",
    "set": "list",
    "map": "object",
}


def normalise_head(head: str) -> str:
    return _HEAD_ALIASES.get(head, head)


def is_type_compatible(value, declared_type_head: str) -> bool:
    """True if the value's top-level shape matches the declared type's outermost head.

    Treats `any`, `dynamic`, and an empty declared head as wildcards (always compat) —
    these signal the schema is deliberately permissive.
    `null` values are always considered compatible because Terraform allows null for
    any optional variable.
    """
    if declared_type_head in {"", "any", "dynamic"}:
        return True
    if value is None:
        return True
    return normalise_head(value_top_shape(value)) == normalise_head(declared_type_head)


# -------------------------------------------------------------------------------
# Reporting
# -------------------------------------------------------------------------------
def fmt_default(value) -> str:
    """Render a default value in a copy-paste-ready form.

    Strings get quoted with double quotes; bools/numbers as-is; null as `null`; lists
    and objects via a minimal Python `repr` substitute that approximates HCL syntax.
    For complex defaults (objects with nested structure) the rendering won't be
    perfectly HCL-formatted, but the customer can compare against the TEMPLATE source
    line referenced in the report.
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, list):
        return "[" + ", ".join(fmt_default(v) for v in value) + "]"
    if isinstance(value, dict):
        if not value:
            return "{}"
        # Inline rendering for small objects; falls back to multi-line for clarity if any
        # value is itself complex.
        if any(isinstance(v, (list, dict)) for v in value.values()):
            return "{ … see TEMPLATE for full structure … }"
        inner = ", ".join(f"{k} = {fmt_default(v)}" for k, v in value.items())
        return "{ " + inner + " }"
    return repr(value)


def print_section_header(title: str, count: int, colour: str) -> None:
    if count == 0:
        return
    print(f"\n{colour}{Colour.BOLD}━━━ {title} ({count}) ━━━{Colour.RESET}")


def print_missing(
    missing: list[str],
    schema: dict[str, dict],
    template: dict,
    template_lines: dict[str, int],
    template_path: Path,
    required_only: bool,
) -> None:
    selected = [name for name in sorted(missing) if schema[name]["has_default"] is not required_only]
    title_word = "REQUIRED" if required_only else "OPTIONAL"
    title_colour = Colour.RED if required_only else Colour.YELLOW
    print_section_header(f"Missing — {title_word}", len(selected), title_colour)
    if not selected:
        return

    for name in selected:
        info = schema[name]
        template_value = template.get(name)
        template_line = template_lines.get(name)
        line_ref = (
            f"templates/TEMPLATE_terraform.tfvars:{template_line}"
            if template_line is not None
            else "not found in TEMPLATE"
        )
        suggested = fmt_default(template_value) if template_value is not None else "<no template default>"

        marker = (
            f"{Colour.RED}[REQUIRED]{Colour.RESET}" if required_only else f"{Colour.YELLOW}[optional]{Colour.RESET}"
        )
        print(f"\n  {marker} {Colour.BOLD}{name}{Colour.RESET}")
        print(f"      type:        {info['type'] or '<not specified>'}")
        print(f"      template:    {suggested}   {Colour.DIM}({line_ref}){Colour.RESET}")

        # Show the comment block above the template entry, if any.
        if template_line is not None:
            ctx = get_template_comment_context(template_path, template_line)
            if ctx:
                print(f"      {Colour.DIM}context:{Colour.RESET}")
                for ctx_line in ctx:
                    print(f"          {Colour.DIM}{ctx_line}{Colour.RESET}")

        # Copy-paste snippet — only when we have a template value to suggest.
        if template_value is not None:
            print(f"      {Colour.CYAN}copy-paste:{Colour.RESET}")
            print(f"          {name} = {suggested}")


def print_extra(extra: list[str]) -> None:
    print_section_header("Extra — assigned in your tfvars but not declared in variables.tf", len(extra), Colour.YELLOW)
    if not extra:
        return
    for name in sorted(extra):
        print(f"  {Colour.YELLOW}-{Colour.RESET} {name}")
    print(
        f"\n  {Colour.DIM}These variables are no longer declared upstream. Terraform may "
        f"emit warnings or errors; consider removing them.{Colour.RESET}"
    )


def print_type_issues(issues: list[tuple[str, str, str]]) -> None:
    print_section_header("Type mismatches", len(issues), Colour.RED)
    if not issues:
        return
    for name, declared, actual in issues:
        print(f"  {Colour.RED}!{Colour.RESET} {Colour.BOLD}{name}{Colour.RESET}")
        print(f"      declared (variables.tf): {declared}")
        print(f"      actual   (your tfvars):  {actual}")
    print(
        f"\n  {Colour.DIM}A type mismatch will fail `terraform plan` or apply. "
        f"Migrate the value to match the declared type.{Colour.RESET}"
    )


# -------------------------------------------------------------------------------
# Backend + provider extraction (from 000_main.tf)
# -------------------------------------------------------------------------------
def parse_main_tf(main_tf_path: Path) -> dict:
    """Parse 000_main.tf and return its hcl2json-decoded body.

    The shape we care about:
      out["terraform"][0]["backend"]["local" | "s3"][0] → {path, bucket, key, ...}
      out["provider"]["aws"][0] → {profile, region, ...}
    """
    return hcl_to_json(str(main_tf_path))


def extract_backend(main_tf: dict) -> tuple[str, dict]:
    """Return `(backend_type, backend_config)` from the active (uncommented) backend block.

    Returns `("none", {})` if no backend block is declared. Returns the *first* backend
    type found if multiple are declared (shouldn't happen — Terraform forbids it).
    """
    terraform_blocks = main_tf.get("terraform", [])
    if not terraform_blocks:
        return "none", {}
    backend = terraform_blocks[0].get("backend", {})
    for kind, configs in backend.items():
        if isinstance(configs, list) and configs:
            return kind, configs[0]
        if isinstance(configs, dict):
            return kind, configs
    return "none", {}


def extract_provider_var_refs(main_tf: dict) -> dict[str, str]:
    """Return `{provider_attr: tfvars_var_name}` for each `${var.X}`-interpolated value
    in the `provider "aws"` block.

    Lets us figure out *which* tfvars variable supplies `profile`, `region`, etc.,
    rather than hard-coding those names here.
    """
    providers = main_tf.get("provider", {})
    aws_configs = providers.get("aws", [])
    if not aws_configs:
        return {}
    cfg = aws_configs[0] if isinstance(aws_configs, list) else aws_configs
    refs: dict[str, str] = {}
    for attr, value in cfg.items():
        if isinstance(value, str):
            m = _VAR_INTERPOLATION_RE.match(value)
            if m:
                refs[attr] = m.group(1)
    return refs


# -------------------------------------------------------------------------------
# Backend readiness check
# -------------------------------------------------------------------------------
def check_backend(backend_type: str, backend_config: dict, customer_tfvars: dict) -> list[tuple[str, str]]:
    """Return a list of `(level, message)` tuples describing backend readiness.

    `level` is one of `"ok"`, `"warn"`, `"fail"`. Caller decides exit-code impact.
    """
    results: list[tuple[str, str]] = []

    if backend_type == "none":
        results.append(("warn", "No backend block declared in 000_main.tf — Terraform will use ephemeral state."))
        return results

    if backend_type == "local":
        rel_path = backend_config.get("path", "terraform.tfstate")
        abs_path = (PROJECT_ROOT / rel_path).resolve()
        results.append(("ok", f"Backend: local — path={rel_path}"))
        if abs_path.exists():
            size_kb = abs_path.stat().st_size / 1024
            results.append(("ok", f"State file present at {abs_path} ({size_kb:.1f} KB)"))
        else:
            results.append(
                (
                    "warn",
                    f"State file NOT found at {abs_path}. "
                    "Fresh-deploy this is expected; an upgrade copy-over may be incomplete.",
                ),
            )
        return results

    if backend_type == "s3":
        bucket = backend_config.get("bucket")
        key = backend_config.get("key")
        region = backend_config.get("region")
        profile = backend_config.get("profile")
        shared_creds = backend_config.get("shared_credentials_file")
        results.append(("ok", f"Backend: s3 — bucket={bucket} key={key} region={region}"))
        if profile:
            results.append(("ok", f"Backend uses explicit profile: {profile}"))
        if shared_creds:
            results.append(("ok", f"Backend uses explicit shared_credentials_file: {shared_creds}"))
            # Best-effort existence check — `~` expansion handled.
            expanded = Path(os.path.expanduser(shared_creds))
            if not expanded.exists():
                results.append(
                    ("fail", f"shared_credentials_file does not exist on this host: {expanded}"),
                )
        # Verify the bucket itself is reachable. Uses the backend's profile if set,
        # otherwise the customer's tfvars-provided profile.
        effective_profile = profile or customer_tfvars.get("aws_profile")
        results.extend(_check_s3_bucket(bucket, region, effective_profile))
        return results

    results.append(("warn", f"Unrecognised backend type: {backend_type}"))
    return results


def _check_s3_bucket(bucket: str | None, region: str | None, profile: str | None) -> list[tuple[str, str]]:
    """Run `aws s3api head-bucket` to verify the backend bucket is reachable + accessible."""
    if not bucket:
        return [("fail", "S3 backend declared but `bucket` is empty.")]
    cmd = ["aws", "s3api", "head-bucket", "--bucket", bucket]
    if region:
        cmd.extend(["--region", region])
    if profile:
        cmd.extend(["--profile", profile])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15, check=False)  # noqa: S603
    except (FileNotFoundError, PermissionError) as exc:
        return [("warn", f"`aws` CLI unavailable ({exc.__class__.__name__}) — skipping bucket reachability check.")]
    except subprocess.TimeoutExpired:
        return [("fail", f"`aws s3api head-bucket` timed out reaching bucket {bucket}.")]
    if result.returncode == 0:
        return [("ok", f"S3 backend bucket {bucket} is reachable.")]
    err_summary = (result.stderr or result.stdout).strip().splitlines()
    err_first = err_summary[-1] if err_summary else "(no error message)"
    return [("fail", f"Cannot access S3 bucket {bucket}: {err_first}")]


# -------------------------------------------------------------------------------
# AWS auth check
# -------------------------------------------------------------------------------
def detect_env_auth_conflicts(provider_refs: dict[str, str], customer_tfvars: dict) -> list[str]:
    """Return human-readable warnings when env vars override/conflict with tfvars-supplied
    auth config. Returning a string means "show this warning"; empty list means no issues.
    """
    warnings: list[str] = []
    tfvars_profile_var = provider_refs.get("profile")
    tfvars_profile = customer_tfvars.get(tfvars_profile_var) if tfvars_profile_var else None
    env_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    env_profile = os.environ.get("AWS_PROFILE")
    env_region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")

    if env_access_key:
        warnings.append(
            "AWS_ACCESS_KEY_ID is set in your environment. Terraform's AWS provider will "
            "use those env credentials and ignore the profile in your tfvars. The identity "
            "reported below reflects the env credentials, not the profile.",
        )
    if env_profile and tfvars_profile and env_profile != tfvars_profile:
        warnings.append(
            f"AWS_PROFILE env var ({env_profile!r}) differs from tfvars aws_profile "
            f"({tfvars_profile!r}). The tfvars value wins for `terraform apply`, but ad-hoc "
            f"`aws` CLI commands you run will follow the env var — easy to be looking at "
            f"the wrong account during debugging.",
        )
    if env_region:
        tfvars_region_var = provider_refs.get("region")
        tfvars_region = customer_tfvars.get(tfvars_region_var) if tfvars_region_var else None
        if tfvars_region and env_region != tfvars_region:
            warnings.append(
                f"AWS_REGION env var ({env_region!r}) differs from tfvars aws_region "
                f"({tfvars_region!r}). Same gotcha as above for ad-hoc `aws` CLI commands.",
            )
    return warnings


def check_aws_auth(profile: str | None, region: str | None) -> tuple[str, str]:
    """Run `aws sts get-caller-identity` to verify the configured profile/region authenticate.

    Returns `(level, message)` where `level` is `"ok"`, `"warn"`, or `"fail"`.
    `"warn"` is reserved for "aws CLI not installed" — we can't check, but don't fail.
    """
    cmd = ["aws", "sts", "get-caller-identity", "--output", "json"]
    if profile:
        cmd.extend(["--profile", profile])
    if region:
        cmd.extend(["--region", region])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15, check=False)  # noqa: S603
    except (FileNotFoundError, PermissionError) as exc:
        return (
            "warn",
            f"`aws` CLI unavailable ({exc.__class__.__name__}) — skipping auth probe. "
            "Terraform will surface auth errors at plan time.",
        )
    except subprocess.TimeoutExpired:
        return "fail", "`aws sts get-caller-identity` timed out (>15s). Check VPN/proxy/STS endpoint reachability."
    if result.returncode == 0:
        try:
            ident = json.loads(result.stdout)
        except json.JSONDecodeError:
            return "warn", f"sts returned non-JSON output: {result.stdout[:200]!r}"
        return (
            "ok",
            f"Authenticated as {ident.get('Arn', '<unknown>')} (Account: {ident.get('Account', '<unknown>')})",
        )
    err = (result.stderr or result.stdout).strip()
    # Compact the error to the last meaningful line for the summary.
    err_last = err.splitlines()[-1] if err else "(no error output)"
    return "fail", f"sts get-caller-identity failed: {err_last}"


# -------------------------------------------------------------------------------
# Runtime-readiness reporting
# -------------------------------------------------------------------------------
_LEVEL_GLYPH = {
    "ok": ("✓", lambda: Colour.GREEN),
    "warn": ("⚠", lambda: Colour.YELLOW),
    "fail": ("✗", lambda: Colour.RED),
}


def print_runtime_line(level: str, message: str) -> None:
    glyph, colour_fn = _LEVEL_GLYPH.get(level, ("•", lambda: Colour.DIM))
    print(f"  {colour_fn()}{glyph}{Colour.RESET} {message}")


def print_runtime_section(
    title: str,
    results: list[tuple[str, str]],
) -> None:
    # Tally for the section header coloration.
    failures = sum(1 for level, _ in results if level == "fail")
    warnings = sum(1 for level, _ in results if level == "warn")
    if failures:
        header_colour = Colour.RED
    elif warnings:
        header_colour = Colour.YELLOW
    else:
        header_colour = Colour.GREEN
    print(f"\n{header_colour}{Colour.BOLD}━━━ {title} ━━━{Colour.RESET}")
    for level, message in results:
        print_runtime_line(level, message)


# -------------------------------------------------------------------------------
# Entrypoint
# -------------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check terraform.tfvars completeness against variables.tf (read-only).",
    )
    parser.add_argument(
        "--tfvars",
        type=Path,
        default=DEFAULT_CUSTOMER_TFVARS,
        help=f"Path to customer's terraform.tfvars (default: {DEFAULT_CUSTOMER_TFVARS}).",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colour codes in output.",
    )
    args = parser.parse_args()

    if args.no_color or not sys.stdout.isatty():
        Colour.disable()

    for path in (VARIABLES_TF, TEMPLATE_TFVARS, args.tfvars):
        if not path.exists():
            print(f"{Colour.RED}Error:{Colour.RESET} required file not found: {path}", file=sys.stderr)
            return 1

    schema = parse_schema(VARIABLES_TF)
    template = parse_assignments(TEMPLATE_TFVARS)
    customer = parse_assignments(args.tfvars)
    template_lines = index_template_lines(TEMPLATE_TFVARS)

    declared = set(schema.keys())
    assigned = set(customer.keys())

    missing = sorted(declared - assigned)
    extra = sorted(assigned - declared)

    type_issues: list[tuple[str, str, str]] = []
    for name in sorted(declared & assigned):
        head = schema[name]["type_head"]
        if not is_type_compatible(customer[name], head):
            type_issues.append((name, schema[name]["type"], value_top_shape(customer[name])))

    required_missing = [n for n in missing if not schema[n]["has_default"]]
    optional_missing = [n for n in missing if schema[n]["has_default"]]

    # --- Header / summary ---
    print(f"{Colour.BOLD}check_upgrade — terraform.tfvars completeness check{Colour.RESET}")
    print(f"  schema:   {VARIABLES_TF}")
    print(f"  template: {TEMPLATE_TFVARS}")
    print(f"  tfvars:   {args.tfvars}")
    print()
    print(f"  {Colour.BOLD}Summary:{Colour.RESET} ", end="")
    print(
        f"{len(required_missing)} required missing, "
        f"{len(optional_missing)} optional missing, "
        f"{len(extra)} extra, "
        f"{len(type_issues)} type mismatch{'es' if len(type_issues) != 1 else ''}.",
    )

    # --- Detail sections ---
    print_missing(missing, schema, template, template_lines, TEMPLATE_TFVARS, required_only=True)
    print_missing(missing, schema, template, template_lines, TEMPLATE_TFVARS, required_only=False)
    print_extra(extra)
    print_type_issues(type_issues)

    # --- Runtime readiness (backend + AWS auth) ---
    runtime_failures = 0
    if MAIN_TF.exists():
        main_tf = parse_main_tf(MAIN_TF)
        backend_type, backend_config = extract_backend(main_tf)
        provider_refs = extract_provider_var_refs(main_tf)

        backend_results = check_backend(backend_type, backend_config, customer)
        print_runtime_section("Backend readiness", backend_results)
        runtime_failures += sum(1 for level, _ in backend_results if level == "fail")

        # Resolve aws_profile and aws_region from tfvars via the provider's `${var.X}` refs.
        profile_var = provider_refs.get("profile")
        region_var = provider_refs.get("region")
        profile = customer.get(profile_var) if profile_var else None
        region = customer.get(region_var) if region_var else None

        auth_results: list[tuple[str, str]] = []
        # Env-var conflicts (warnings only).
        for warning in detect_env_auth_conflicts(provider_refs, customer):
            auth_results.append(("warn", warning))
        # Region sanity.
        if region and region not in _KNOWN_AWS_REGIONS:
            auth_results.append(
                (
                    "warn",
                    f"aws_region={region!r} is not in this script's known-regions list; verify it's a real AWS region.",
                )
            )
        # The actual probe.
        level, message = check_aws_auth(profile, region)
        auth_results.append((level, message))
        print_runtime_section("AWS authentication (sts get-caller-identity)", auth_results)
        runtime_failures += sum(1 for lev, _ in auth_results if lev == "fail")
    else:
        print(f"\n{Colour.YELLOW}{Colour.BOLD}━━━ Runtime readiness ━━━{Colour.RESET}")
        print_runtime_line("warn", f"{MAIN_TF} not found — skipping backend + AWS auth checks.")

    print()  # trailing newline before exit
    if required_missing or type_issues or runtime_failures:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
