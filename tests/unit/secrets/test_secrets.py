#!/usr/bin/env python3
"""
Unit tests for comparing template JSON files with their testing equivalents.

This module tests that:
1. Each template JSON file has a corresponding testing version
2. Key counts match between template and testing files
3. Key names are identical between template and testing files
"""

import pytest
from pathlib import Path

from tests.utils.local import root
from tests.utils.filehandling import read_json


templates_dir = Path(root) / "templates"
test_data_dir = Path(root) / "tests" / "datafiles" / "secrets"
json_files = list(templates_dir.glob("ssm_sensitive_values_*.json"))


@pytest.mark.local
@pytest.mark.secrets
@pytest.mark.quick
def test_secret_keys_match():
    """
    Ensure that they SSM testing files have the same keys and count as template files.
    """

    for json_file in json_files:
        template_data = read_json(json_file.as_posix())
        testing_data = read_json(f"{test_data_dir.as_posix()}/{json_file.name.replace('.json', '_testing.json')}")

        template_data_keys = template_data.keys()
        testing_data_keys = testing_data.keys()

        assert len(template_data_keys) == len(testing_data_keys)

        for key in template_data_keys:
            assert key in testing_data_keys


# TODO:
# - Ensure SSM keys are pointed to 'tower-testing'
# - Verify tfvars too
