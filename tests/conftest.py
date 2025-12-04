import os
import subprocess
import time
from pathlib import Path

import pytest

# Single-sourced in top-level conftest.py.
# base_import_dir = Path(__file__).resolve().parents[3]
# print(f"{base_import_dir=}")
# if base_import_dir not in sys.path:
#     sys.path.append(str(base_import_dir))
from scripts.installer.utils.purge_folders import delete_pycache_folders
from tests.utils.config import FP
from tests.utils.filehandling import FileHelper
from tests.utils.preflight.preflight import check_aws_sso_token
from tests.utils.pytest_logger import get_logger
from tests.utils.terraform.executor import TF, execute_subprocess, prepare_plan

"""
EXPLANATION
=======================================
Originally tried using [tftest](https://pypi.org/project/tftest/) package to test but this became complicated and unwieldy. Instead, simplified
testing loop to:

1. Test in the project directory.
2. Take a backup of the existing `terraform.tfvars` file.
3. Create a new `terraform.tfvars` file for testing purposes (_sourced from `tests/datafiles/generate_core_data.sh`).
4. Provide override values to test fixtures (which will generate a new `override.auto.tfvars` file in the project root).
    This file supercedes the same keys defined in the `terraform.tfvars` file.
5. Run the tests:
    1. For each fixture, run `terraform plan` based on the test tvars and override file. Results as cached to speed up n+1 test runs.
    2. Execute tests tied to that fixture.
    3. Repeat.
6. Purge the test tfvars and override file.
7.Restore the original `terraform.tfvars` file when testing is complete.
"""


## ------------------------------------------------------------------------------------
## Helper Fixtures
## ------------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def session_setup():
    # Confirm the tester has a valid AWS SSO login token or else tests will fail.
    # TODO - Fix -- this failed. My token was not valid but the STS call was returning successfully? Go figure.
    check_aws_sso_token()

    # Create a fresh copy of the base testing terraform.tfvars file.
    subprocess.run("make generate_test_data", shell=True, check=True)

    print("\nBacking up terraform.tfvars.")
    FileHelper.move_file(FP.TFVARS_BASE, FP.TFVARS_BACKUP)

    # Swap in test tfvars (base and base-override), and testing-specific outputs (e.g. locals).
    print("\nLoading test tfvars and output artefacts.")
    FileHelper.copy_file(FP.TFVARS_TEST_SRC, FP.TFVARS_TEST_DST)
    FileHelper.copy_file(FP.TFVARS_BASE_OVERRIDE_SRC, FP.TFVARS_BASE_OVERRIDE_DST)
    FileHelper.copy_file(FP.OUTPUTS_SRC, FP.OUTPUTS_DST)

    # Prepare plan cache directory
    os.makedirs(FP.CACHE_PLAN_DIR, exist_ok=True)

    # Prepare JSONified 009 (via hcl2json container)
    # CLI_command = "./hcl2json 009_define_file_templates.tf > 009_define_file_templates.json"
    command = (
        f"docker run --rm -v {FP.ROOT}:/tmp ghcr.io/seqeralabs/cx-field-tools-installer/hcl2json:vendored"
        f" /tmp/009_define_file_templates.tf > {FP.ROOT}/009_define_file_templates.json"
    )
    result = execute_subprocess(command)

    yield

    print("\nRestoring original environment.")

    # Single-source destroy at end of testing cycle to save time
    # Not actually running Terraform apply anymore, do I don't need to do a destroy
    # run_terraform_destroy()

    # Remove testing files, delete __pycache__ folders, restore origin tfvars.
    files_to_purge = [
        FP.TFVARS_AUTO_OVERRIDE_DST,
        FP.TFVARS_BASE,
        FP.TFVARS_BASE_OVERRIDE_DST,
        FP.OUTPUTS_DST,
        "009_define_file_templates.json",
    ]

    for file in files_to_purge:
        Path(file).unlink(missing_ok=True)

    delete_pycache_folders(FP.ROOT)

    # Restore original tfvars
    FileHelper.move_file(FP.TFVARS_BACKUP, FP.TFVARS_BASE)


@pytest.fixture(scope="session")  # function
def config_baseline_settings_default():
    """
    Terraform plan and apply the default test terraform.tfvars and base-override.auto.tfvars.
    Plan with ALL resources rather than targeted, to get all outputs in plan document.
    """

    tf_modifiers = """#NONE"""
    plan = prepare_plan(tf_modifiers)

    # DONT USE THESE - no longer needed since the new `terraform template` approach is used.
    # qualifier = "-target=null_resource.generate_independent_config_files"
    # run_terraform_apply(qualifier)

    yield plan

    # run_terraform_destroy()


@pytest.fixture(scope="function")
def teardown_tf_state_all():
    print("This testcase will have all tf state destroyed.")

    yield

    TF.destroy()


## ------------------------------------------------------------------------------------
## Pytest Structured Logging Hooks
## ------------------------------------------------------------------------------------
# Hooks are native pytest mechanisms that execute at specific points in the test lifecycle.
# They are defined in this file and are called by pytest at the appropriate time.
# See: https://docs.pytest.org/en/stable/reference/reference.html#hooks

"""
As per ChatGPT: Pytest Lifecycle (Simplified)
1.Session Start
  - pytest_sessionstart hook is called.
2. Collection Phase
  - Pytest discovers and collects all test files, classes, and functions.
  - The list of tests is built and stored (e.g., in session.items and session.testscollected).
3. Setup Phase
  - Fixtures and setup code are prepared.
4. Test Execution Phase
  - Tests are executed.
5. Teardown Phase
  - Cleanup and fixture teardown.
6. Session Finish
  - pytest_sessionfinish hook is called.

Key Point:
- Test collection happens after pytest_sessionstart.
- The pytest_sessionstart hook is called before test collection, so you cannot reliably access the total number of tests at this point.
- The correct place to access the number of collected tests is in the pytest_collection_finish hook, which runs after collection is complete.
"""
global_marker_expression = []


def pytest_sessionstart(session):
    """Log session start information."""
    logger = get_logger()

    # Extract markers from config
    # WARNING: Originally looked for `session.config.option.m` but this is not set in the config.
    # Instead, we use `session.config.option.markexpr` which is set in the config.
    markers = []
    if hasattr(session.config, "option") and hasattr(session.config.option, "markexpr"):
        marker_expr = session.config.option.markexpr
        if marker_expr:
            # Convert marker expression to list format for logging
            # This is a simplified approach - marker expressions can be complex
            markers = [marker_expr]  # Store as list with the full expression

            global global_marker_expression
            global_marker_expression = [marker_expr]

    logger.log_session_start(markers=markers)


def pytest_collection_modifyitems(session, config, items):
    """Log number of tests found once collected."""
    logger = get_logger()
    total_tests = len(items)
    logger.log_collection_modifyitems(total_tests=total_tests)


def pytest_deselected(items):
    """Log information about tests that were deselected (filtered out)."""
    logger = get_logger()

    # Count deselected tests by reason
    deselected_count = len(items)

    # Try to determine the reason for deselection
    deselection_reasons = []
    for item in items:
        if hasattr(item, "deselected_reason"):
            deselection_reasons.append(item.deselected_reason)

    # Add identifier for the marker expression used to deselect tests.
    global global_marker_expression
    if len(global_marker_expression) > 0:
        deselection_reasons.append(f"Presence of marker: {global_marker_expression[0]}")

    # Log deselection information
    logger.log_deselected(deselected_count=deselected_count, reasons=deselection_reasons)


def pytest_sessionfinish(session, exitstatus):
    """Log session end information with summary."""
    logger = get_logger()

    # Get test results summary from terminalreporter
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if reporter:
        passed = len(reporter.stats.get("passed", []))
        failed = len(reporter.stats.get("failed", []))
        skipped = len(reporter.stats.get("skipped", []))
        errors = len(reporter.stats.get("error", []))
    else:
        # Fallback if terminalreporter is not available
        passed = failed = skipped = errors = 0

    # Calculate session duration
    duration = time.time() - logger.session_start_time

    logger.log_session_end(passed=passed, failed=failed, skipped=skipped, errors=errors, duration=duration)


def pytest_runtest_setup(item):
    """Log test setup/start."""
    logger = get_logger()

    # Extract test information
    test_path = str(item.fspath) + "::" + item.name

    # Get markers
    markers = [mark.name for mark in item.iter_markers()]

    # Get fixtures
    fixtures = list(item.fixturenames) if hasattr(item, "fixturenames") else []

    # Get parametrize info
    parametrize = None
    if hasattr(item, "callspec") and item.callspec:
        parametrize = str(item.callspec.params)

    logger.log_test_start(
        test_path=test_path,
        markers=markers,
        fixtures=fixtures,
        parametrize=parametrize or "",
    )


def pytest_runtest_teardown(item, nextitem):
    """Log test teardown/end."""
    # logger = get_logger()

    # test_path = str(item.fspath) + "::" + item.name

    # # Calculate duration if available
    # duration = 0.0
    # if hasattr(item, "duration"):
    #     duration = item.duration

    # logger.log_test_end(test_path=test_path, duration=duration)
    pass


def pytest_runtest_logreport(report):
    """Log test results with captured output."""
    logger = get_logger()

    # Only log on call phase (not setup/teardown)
    if report.when != "call":
        return

    test_path = str(report.fspath) + "::" + report.head_line if hasattr(report, "head_line") else str(report.nodeid)

    # Map pytest outcomes to our status
    status_map = {
        "passed": "PASSED",
        "failed": "FAILED",
        "skipped": "SKIPPED",
        "error": "ERROR",
    }
    status = status_map.get(report.outcome, "UNKNOWN")

    # Get captured output
    stdout = ""
    stderr = ""
    if hasattr(report, "capstdout"):
        stdout = report.capstdout
    if hasattr(report, "capstderr"):
        stderr = report.capstderr

    # Get failure reason
    failure_reason = ""
    if report.failed and hasattr(report, "longrepr"):
        failure_reason = str(report.longrepr)

    # Get test metadata
    markers = []
    fixtures = []
    parametrize = None

    if hasattr(report, "item"):
        markers = [mark.name for mark in report.item.iter_markers()]
        fixtures = list(report.item.fixturenames) if hasattr(report.item, "fixturenames") else []
        if hasattr(report.item, "callspec") and report.item.callspec:
            parametrize = str(report.item.callspec.params)

    logger.log_test_result(
        test_path=test_path,
        status=status,
        duration=report.duration,
        stdout=stdout,
        stderr=stderr,
        failure_reason=failure_reason,
        markers=markers,
        fixtures=fixtures,
        parametrize=parametrize or "",
    )
