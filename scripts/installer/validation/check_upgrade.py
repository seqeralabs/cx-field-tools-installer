#!/usr/bin/env python3
"""Check terraform.tfvars completeness and runtime readiness before an upgrade apply.

Read-only. For each missing variable, the report shows the comment block above
its TEMPLATE entry plus the full TEMPLATE assignment (including multi-line
objects) so the customer can paste it into their tfvars without opening
TEMPLATE_terraform.tfvars themselves.

Exit code:
  0 — clean (no required-missing variables, backend OK, auth OK)
  1 — at least one required variable missing, backend unreachable, or auth failed
"""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


# Standard project import-path setup.
base_import_dir = Path(__file__).resolve().parents[2]
if str(base_import_dir) not in sys.path:
    sys.path.append(str(base_import_dir))

from installer.utils.extractors import hcl_to_json  # noqa: E402  (sys.path manipulation above)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
VARIABLES_TF = PROJECT_ROOT / "variables.tf"
TEMPLATE_TFVARS = PROJECT_ROOT / "templates" / "TEMPLATE_terraform.tfvars"
MAIN_TF = PROJECT_ROOT / "000_main.tf"
DEFAULT_TFVARS = PROJECT_ROOT / "terraform.tfvars"


# ANSI colour codes. Zeroed by `disable_colour()` for non-TTY / --no-color.
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def disable_colour():
    """Zero out the ANSI colour globals so all print() calls render plain text.

    Called from main() when stdout isn't a TTY or `--no-color` is passed. Avoids
    ANSI escape sequences leaking into piped output, log files, or CI logs.
    """
    global RED, GREEN, YELLOW, CYAN, BOLD, DIM, RESET
    RED = GREEN = YELLOW = CYAN = BOLD = DIM = RESET = ""


# -------------------------------------------------------------------------------
# Loaders
# -------------------------------------------------------------------------------
def load_schema():
    """Return {varname: has_default_bool} from variables.tf.

    hcl2json parses variables.tf into:
        {"variable": {
            "<varname>": [{"type": "${string}", "default": "x", "description": "...", ...}],
            ...
        }}
    Each value is a 1-element list (HCL allows multiple blocks with the same name
    — this codebase never does). We unwrap it and check for a "default" key:
    present  -> variable is OPTIONAL (Terraform falls back to the default if unset)
    absent   -> variable is REQUIRED (Terraform refuses to plan without it).
    """
    parsed = hcl_to_json(str(VARIABLES_TF))
    schema = {}
    for name, attrs_list in parsed.get("variable", {}).items():
        attrs = attrs_list[0] if isinstance(attrs_list, list) and attrs_list else {}
        schema[name] = "default" in attrs
    return schema


def load_template_lines():
    """Return {varname: lineno} for each top-level assignment in TEMPLATE_terraform.tfvars.

    Scans for `^<identifier>\\s*=` at column 0 — i.e. assignments with no leading
    whitespace. This deliberately skips indented assignments (which belong to
    nested object/map values like `tower_compute_env_cleanup.enabled`), comment
    lines, and blank lines.

    The line number is used in the report's "(TEMPLATE:<lineno>)" reference and
    as the starting point for `get_template_comment_context()` and
    `get_full_assignment()` below.
    """
    pattern = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=")
    index = {}
    for lineno, line in enumerate(TEMPLATE_TFVARS.read_text().splitlines(), start=1):
        m = pattern.match(line)
        if m:
            index.setdefault(m.group(1), lineno)
    return index


def get_template_comment_context(line_num):
    """Return the contiguous comment block immediately above `line_num` in TEMPLATE.

    Walks backwards from `line_num` collecting consecutive `#`-prefixed lines.
    Stops at the first blank line, non-comment line, or the top of the file.
    Returned list is in original (top-to-bottom) order with the leading `#`
    preserved on each line — the caller renders it verbatim under "context:".

    Example for TEMPLATE around line 481:
        478:   # Connect proxy - server config (v0.11.0+)
        479:   connect_management_port     = ""    # ...
        480:   connect_management_auth_key = ""    # ...
        481:   connect_log_level           = "debug"  # ...
    Calling with line_num=479 returns ["# Connect proxy - server config (v0.11.0+)"].
    Calling with line_num=480 returns [] (line above is an assignment, not a comment).
    """
    all_lines = TEMPLATE_TFVARS.read_text().splitlines()
    context = []
    i = line_num - 2  # 1-based line_num -> 0-based index of the line directly above
    while i >= 0:
        stripped = all_lines[i].strip()
        if not stripped or not stripped.startswith("#"):
            break
        context.insert(0, all_lines[i].rstrip())
        i -= 1
    return context


def get_full_assignment(line_num, max_lines=200):
    """Return the full TEMPLATE text of an assignment starting at `line_num`.

    Handles both single-line (`foo = "x"`) and multi-line (`foo = { ... }` or
    `foo = [ ... ]`) assignments by tracking brace/bracket depth as it walks
    forward. The first line is always captured; subsequent lines are captured
    until `{`/`[` count balances `}`/`]` count. `max_lines` is a safety bound
    against malformed TEMPLATE input.

    Returns lines verbatim from TEMPLATE, INCLUDING any inline `# ...` comments
    — the caller (_print_missing_variable) strips those via
    `split_trailing_comment()` so the copy-paste block is pasteable.

    Example for a multi-line object:
        Input  (starting at the `tower_compute_env_cleanup = {` line):
            tower_compute_env_cleanup = {
              enabled  = false  # run the cleanup job
              ...
            }
        Returns the list of all those lines, brace-balanced.
    """
    all_lines = TEMPLATE_TFVARS.read_text().splitlines()
    start = line_num - 1  # 1-based -> 0-based
    if start >= len(all_lines):
        return []

    depth = 0
    captured = []
    for i in range(start, min(start + max_lines, len(all_lines))):
        line = all_lines[i]
        captured.append(line)
        for ch in line:
            if ch in "{[":
                depth += 1
            elif ch in "}]":
                depth -= 1
        if depth == 0:
            # Either a single-line assignment (no braces) or we've closed all opened blocks.
            break
    return captured


def split_trailing_comment(line):
    """Split `line` into (code, comment) where comment is None or starts with `#`.

    Naive HCL tokeniser: scans for the first `#` that isn't inside a single- or
    double-quoted string. Tracks `\\`-escaped quote characters. The code half
    is rstrip()-ed so removing a trailing comment doesn't leave whitespace.

    Examples:
        'foo = "bar"        # explanation'  -> ('foo = "bar"', '# explanation')
        'foo = "x # y"'                     -> ('foo = "x # y"', None)
        'foo = 42'                          -> ('foo = 42', None)
    """
    in_string = False
    quote = None
    for i, ch in enumerate(line):
        if in_string:
            if ch == quote and line[i - 1] != "\\":
                in_string = False
        elif ch in ('"', "'"):
            in_string = True
            quote = ch
        elif ch == "#":
            return line[:i].rstrip(), line[i:].strip()
    return line, None


# -------------------------------------------------------------------------------
# Checks — each prints its own report block and returns the blocking-error count.
# -------------------------------------------------------------------------------
def check_missing_variables(schema, customer, template_lines):
    """Report variables declared in variables.tf but absent from the customer's tfvars.

    Inputs:
        schema:         {varname: has_default_bool}  (from `load_schema()`)
        customer:       {varname: value}             (raw hcl2json of customer's tfvars)
        template_lines: {varname: lineno}            (from `load_template_lines()`)

    Splits the missing-variable set into:
        REQUIRED — no default declared upstream; blocks `terraform plan`. Each
                   one increments the error counter that drives exit code.
        OPTIONAL — has a default upstream; informational only, doesn't count
                   toward the exit code.

    Returns the count of REQUIRED-missing variables.

    Variables within each group (REQUIRED, OPTIONAL) are listed in TEMPLATE
    order — not alphabetical — so that section headers, master flags, and
    their dependent keys stay grouped the way the maintainer arranged them.
    """
    missing = set(schema) - set(customer)

    # Sort key: TEMPLATE line number, with anything not in TEMPLATE pushed to the end.
    def template_order(n):
        return template_lines.get(n, float("inf"))

    required = sorted([n for n in missing if not schema[n]], key=template_order)
    optional = sorted([n for n in missing if schema[n]], key=template_order)

    if required:
        print(f"\n{RED}{BOLD}━━━ Missing — REQUIRED ({len(required)}) ━━━{RESET}")
        for name in required:
            _print_missing_variable(name, template_lines, f"{RED}[REQUIRED]{RESET}")

    if optional:
        print(f"\n{YELLOW}{BOLD}━━━ Missing — OPTIONAL ({len(optional)}) ━━━{RESET}")
        for name in optional:
            _print_missing_variable(name, template_lines, f"{YELLOW}[optional]{RESET}")

    return len(required)


def _print_missing_variable(name, template_lines, marker):
    """Render one missing-variable block to stdout.

    Output layout (per missing variable):
        [MARKER] <name>  (TEMPLATE:<line>)
            context:
                # comment lines harvested from above the TEMPLATE assignment
                # plus any inline `# ...` comments stripped off assignment lines
            copy-paste:
                <assignment text with trailing `# ...` comments removed>

    The trailing-comment split is what makes the copy-paste block pasteable
    verbatim into a tfvars file — explanatory inline comments move into
    `context:` (informational) instead of cluttering the assignment.

    If the variable isn't in TEMPLATE at all (e.g. test-only `use_mocks`),
    only the header line is printed.
    """
    line = template_lines.get(name)
    ref = f" {DIM}(TEMPLATE:{line}){RESET}" if line is not None else f" {DIM}(not in TEMPLATE){RESET}"
    print(f"\n  {marker} {BOLD}{name}{RESET}{ref}")

    if line is None:
        return  # No TEMPLATE entry to harvest comment/assignment from.

    # Comments BEFORE the assignment, plus inline comments harvested below.
    above = get_template_comment_context(line)

    cleaned_assignment = []
    inline_comments = []
    for raw in get_full_assignment(line):
        code, comment = split_trailing_comment(raw)
        if comment:
            cleaned_assignment.append(code)
            inline_comments.append(comment)
        else:
            cleaned_assignment.append(raw)

    context = above + inline_comments
    if context:
        print(f"      {DIM}context:{RESET}")
        for ctx_line in context:
            print(f"          {DIM}{ctx_line}{RESET}")

    if cleaned_assignment:
        print(f"      {CYAN}copy-paste:{RESET}")
        for assn_line in cleaned_assignment:
            print(f"          {assn_line}")


def check_extra_variables(schema, customer):
    """Report variables in customer's tfvars but not declared in variables.tf.

    Inputs:
        schema:   {varname: has_default_bool}  (from `load_schema()`)
        customer: {varname: value}             (raw hcl2json of customer's tfvars)

    Informational only — always returns 0. Terraform itself warns or errors on
    undeclared variables at plan time (behaviour varies by version); we surface
    them here so the customer can clean them up proactively during an upgrade.
    """
    extra = sorted(set(customer) - set(schema))
    if not extra:
        return 0

    print(f"\n{YELLOW}{BOLD}━━━ Extra — assigned but not declared upstream ({len(extra)}) ━━━{RESET}")
    for name in extra:
        print(f"  {YELLOW}-{RESET} {name}")
    print(
        f"\n  {DIM}These variables are no longer declared in variables.tf. Terraform may warn or error; consider removing.{RESET}"
    )
    return 0


def check_backend(customer):
    """Verify the active (uncommented) backend block in 000_main.tf is reachable.

    hcl2json shape of 000_main.tf:
        {"terraform": [{
            "backend": {"local"|"s3": [{path|bucket|key|region|profile|...}]},
            "required_providers": [...],
            ...
        }]}

    Branches by backend kind:
      - local: check the state file exists at the configured path (relative to
               project root). Missing file is a WARNING, not a failure — fresh
               deploys legitimately don't have one yet.
      - s3:    run `aws s3api head-bucket` (using the backend's own `profile`
               if set, else falling back to the customer's tfvars `aws_profile`).
               Inaccessible bucket is a FAILURE. Also checks
               `shared_credentials_file` existence if specified.

    Returns 1 if the backend is unreachable / misconfigured, 0 otherwise.
    """
    main_tf = hcl_to_json(str(MAIN_TF))
    terraform_blocks = main_tf.get("terraform", [])
    backend = terraform_blocks[0].get("backend", {}) if terraform_blocks else {}

    print(f"\n{CYAN}{BOLD}━━━ Backend readiness ━━━{RESET}")

    if not backend:
        print(f"  {YELLOW}⚠{RESET} No backend block declared in 000_main.tf — Terraform will use ephemeral state.")
        return 0

    if "local" in backend:
        cfg = backend["local"]
        if isinstance(cfg, list):
            cfg = cfg[0]
        rel = cfg.get("path", "terraform.tfstate")
        state_path = (PROJECT_ROOT / rel).resolve()
        if state_path.exists():
            kb = state_path.stat().st_size / 1024
            print(f"  {GREEN}✓{RESET} Local backend: state file at {state_path} ({kb:.1f} KB)")
            return 0
        print(f"  {YELLOW}⚠{RESET} Local backend: state file NOT found at {state_path}.")
        print(f"      {DIM}Fresh deploy = expected. Upgrade copy-over = check if state file was brought across.{RESET}")
        return 0

    if "s3" in backend:
        cfg = backend["s3"]
        if isinstance(cfg, list):
            cfg = cfg[0]
        bucket = cfg.get("bucket")
        region = cfg.get("region")
        # Backend's own profile wins; fall back to tfvars `aws_profile` if not set.
        profile = cfg.get("profile") or customer.get("aws_profile")
        print(f"  {GREEN}✓{RESET} S3 backend: bucket={bucket} key={cfg.get('key')} region={region}")

        shared_creds = cfg.get("shared_credentials_file")
        if shared_creds:
            expanded = Path(os.path.expanduser(shared_creds))
            if not expanded.exists():
                print(f"  {RED}✗{RESET} shared_credentials_file does not exist: {expanded}")
                return 1
            print(f"  {GREEN}✓{RESET} Using shared_credentials_file={expanded}")

        if not bucket:
            print(f"  {RED}✗{RESET} S3 backend declared but `bucket` is empty.")
            return 1

        cmd = ["aws", "s3api", "head-bucket", "--bucket", bucket]
        if region:
            cmd.extend(["--region", region])
        if profile:
            cmd.extend(["--profile", profile])
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=15, check=False)  # noqa: S603
        except (FileNotFoundError, PermissionError) as exc:
            print(
                f"  {YELLOW}⚠{RESET} aws CLI unavailable ({exc.__class__.__name__}) — skipping bucket reachability check."
            )
            return 0
        except subprocess.TimeoutExpired:
            print(f"  {RED}✗{RESET} head-bucket timed out reaching {bucket}.")
            return 1

        if r.returncode == 0:
            print(f"  {GREEN}✓{RESET} S3 bucket {bucket} reachable.")
            return 0
        err = (r.stderr or r.stdout).strip().splitlines()
        print(f"  {RED}✗{RESET} Cannot access S3 bucket {bucket}: {err[-1] if err else '(no error)'}")
        return 1

    print(f"  {YELLOW}⚠{RESET} Unrecognised backend type: {next(iter(backend))}")
    return 0


def check_aws_auth(customer):
    """Run `aws sts get-caller-identity` to confirm AWS auth resolves correctly.

    Uses `aws_profile` and `aws_region` from the customer's tfvars (passed in
    as the `customer` dict via hcl2json — flat {varname: value}). Before the
    probe, surfaces two env-var gotchas as warnings:
      - AWS_ACCESS_KEY_ID set → Terraform's AWS provider will use env credentials
                                and ignore aws_profile from tfvars.
      - AWS_PROFILE set and differs from tfvars `aws_profile` → operator's ad-hoc
                                `aws` commands will target a different profile
                                than `terraform apply` will.

    Returns 1 on auth failure (sts non-zero / timeout). Returns 0 if the aws
    CLI isn't available on PATH or is sandbox-blocked — we can't probe in
    that case, but `terraform plan` will surface the same error later.
    """
    profile = customer.get("aws_profile")
    region = customer.get("aws_region")

    print(f"\n{CYAN}{BOLD}━━━ AWS authentication ━━━{RESET}")

    if os.environ.get("AWS_ACCESS_KEY_ID"):
        print(
            f"  {YELLOW}⚠{RESET} AWS_ACCESS_KEY_ID is set in your env. Terraform will use env credentials "
            f"and ignore aws_profile from tfvars. The identity below reflects env credentials.",
        )
    env_profile = os.environ.get("AWS_PROFILE")
    if env_profile and profile and env_profile != profile:
        print(f"  {YELLOW}⚠{RESET} AWS_PROFILE env ({env_profile!r}) differs from tfvars aws_profile ({profile!r}).")

    cmd = ["aws", "sts", "get-caller-identity", "--output", "json"]
    if profile:
        cmd.extend(["--profile", profile])
    if region:
        cmd.extend(["--region", region])

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15, check=False)  # noqa: S603
    except (FileNotFoundError, PermissionError) as exc:
        print(
            f"  {YELLOW}⚠{RESET} aws CLI unavailable ({exc.__class__.__name__}) — skipping auth probe. "
            f"Terraform will surface auth errors at plan time.",
        )
        return 0
    except subprocess.TimeoutExpired:
        print(f"  {RED}✗{RESET} sts get-caller-identity timed out (>15s).")
        return 1

    if r.returncode == 0:
        ident = json.loads(r.stdout)
        print(f"  {GREEN}✓{RESET} Authenticated as {ident.get('Arn')} (Account: {ident.get('Account')})")
        return 0
    err = (r.stderr or r.stdout).strip().splitlines()
    print(f"  {RED}✗{RESET} sts get-caller-identity failed: {err[-1] if err else '(no error)'}")
    return 1


# -------------------------------------------------------------------------------
# Entrypoint
# -------------------------------------------------------------------------------
def main():
    """CLI entrypoint. Returns the exit code (0 if clean, 1 if blocking issues).

    Sequence:
      1. Parse args, decide on colour.
      2. Sanity-check that all input files exist.
      3. Load the three input sources: schema (variables.tf), customer tfvars,
         template line index.
      4. Run each check_* in order. Each prints its own section and returns the
         count of blocking errors (REQUIRED-missing, backend unreachable, auth
         failed). Extra-variables is informational only.
      5. Sum the errors. Non-zero → exit 1.
    """
    parser = argparse.ArgumentParser(description="Check tfvars completeness and runtime readiness (read-only).")
    parser.add_argument(
        "--tfvars",
        type=Path,
        default=DEFAULT_TFVARS,
        help=f"Path to customer's terraform.tfvars (default: {DEFAULT_TFVARS}).",
    )
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colour codes.")
    args = parser.parse_args()

    if args.no_color or not sys.stdout.isatty():
        disable_colour()

    for p in (VARIABLES_TF, TEMPLATE_TFVARS, MAIN_TF, args.tfvars):
        if not p.exists():
            print(f"{RED}Error:{RESET} required file not found: {p}", file=sys.stderr)
            return 1

    schema = load_schema()
    customer = hcl_to_json(str(args.tfvars))
    template_lines = load_template_lines()

    print(f"{BOLD}check_upgrade — terraform.tfvars completeness check{RESET}")
    print(f"  schema:   {VARIABLES_TF}")
    print(f"  template: {TEMPLATE_TFVARS}")
    print(f"  tfvars:   {args.tfvars}")

    errors = 0
    errors += check_missing_variables(schema, customer, template_lines)
    errors += check_extra_variables(schema, customer)
    errors += check_backend(customer)
    errors += check_aws_auth(customer)

    print()
    if errors:
        print(f"{RED}{BOLD}check_upgrade: {errors} blocking issue(s) found.{RESET}")
        return 1
    print(f"{GREEN}{BOLD}check_upgrade: all checks passed.{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
