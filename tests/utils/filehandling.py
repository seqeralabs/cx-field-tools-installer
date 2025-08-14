from typing import Dict, Any

import subprocess
import json
import shutil
import sys
import yaml


## ------------------------------------------------------------------------------------
## File Utility Functions
## ------------------------------------------------------------------------------------
def read_json(file_path: str) -> dict:
    """Read a JSON plan file."""
    with open(file_path, "r") as f:
        return json.load(f)


def read_yaml(file_path: str) -> Any:
    """Read a JSON plan file."""
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def read_file(file_path: str) -> str:
    """Read a file."""
    with open(file_path, "r") as f:
        return f.read()


def write_file(file_path: str, content: str | bytes) -> None:
    """Write content to a file."""
    if isinstance(content, bytes):
        content = content.decode("utf-8")
    with open(file_path, "w") as f:
        f.write(content)


def move_file(source: str, target: str) -> None:
    """Move a file."""
    try:
        shutil.move(source, target)
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        sys.exit(1)


def copy_file(source: str, target: str) -> None:
    """Move a file."""
    try:
        shutil.copy2(source, target)
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        sys.exit(1)


def parse_key_value_file(file_path: str) -> Dict[str, Any]:
    """Parse a file containing KEY=VALUE pairs. Function intended to be used with tfvars files.

    Args:
        file_path: Path to the file to parse

    Returns:
        Dictionary containing key-value pairs

    NOTE:
        Double-quotes / single-quottes as part of string messes up pytest string assertions. Remove these to normalize.
        Terraform always hasd double-quotes.
        Env files can be either double-quotes or single-quotes.
    """
    result = {}
    raw = read_file(file_path)

    for line in raw.splitlines():
        line = line.strip()
        if line and "=" in line:
            key, value = line.split("=", 1)
            value = value.strip()

            # Edgecase: Empty strings represented by "" or '' but this confuses python (e.g. '""')
            if (value == '""') or (value == "''"):
                value = ""
            elif value.startswith("'") and value.endswith("'"):
                value = value.strip("'")
            elif value.startswith('"') and value.endswith('"'):
                value = value.strip('"')

            result[key.strip()] = value.strip()

    return result
