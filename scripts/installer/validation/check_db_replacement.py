#!/usr/bin/env python3
"""Fail if the Terraform plan would delete or replace an RDS instance.

Run before applying a database change such as the MySQL 8.0 -> 8.4 upgrade (Design Decision 25).
Needs the same AWS credentials as `terraform plan`.

Exit code:
  0 — no RDS instance in the plan is deleted or replaced
  1 — at least one RDS instance would be deleted or replaced
"""

import json
from pathlib import Path
import subprocess  # nosec B404  (runs terraform with fixed arguments only)
import sys


PLAN_FILE = "tfplan-db-replacement-check"


def find_db_instance_changes(plan: dict) -> list[tuple[str, list[str]]]:
    """Returns (address, actions) for every `aws_db_instance` in a `terraform show -json` plan."""
    return [
        (change["address"], change["change"]["actions"])
        for change in plan.get("resource_changes", [])
        if change.get("type") == "aws_db_instance"
    ]


def main() -> int:
    """Plans, reports each RDS instance's planned action, and fails on any delete."""
    try:
        # terraform from PATH with fixed arguments, like `make plan`.
        plan_cmd = ["terraform", "plan", "-out", PLAN_FILE]
        show_cmd = ["terraform", "show", "-json", PLAN_FILE]
        subprocess.run(plan_cmd, check=True)  # noqa: S603  # nosec B603 B607
        shown = subprocess.run(show_cmd, check=True, capture_output=True, text=True)  # noqa: S603  # nosec B603 B607
    finally:
        Path(PLAN_FILE).unlink(missing_ok=True)

    changes = find_db_instance_changes(json.loads(shown.stdout))
    if not changes:
        print("No RDS instance in this plan.")
        return 0

    replaced = False
    for address, actions in changes:
        print(f"{address}: {', '.join(actions)}")
        if "delete" in actions:
            replaced = True

    if replaced:
        print("ERROR: the plan deletes or replaces an RDS instance. Don't apply it.")
        print("Check which setting forces the replacement (see documentation/setup/upgrade_mysql_8_4.md).")
        return 1

    print("OK: no RDS instance is deleted or replaced.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
