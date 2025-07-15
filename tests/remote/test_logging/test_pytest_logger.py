"""
Tests for pytest structured logging functionality.
"""

import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.utils.pytest_logger import PytestStructuredLogger, get_logger, reset_logger


# TODO: Rewrite this as a fixture? TBD.
class TestPytestStructuredLogger:
    """Test the PytestStructuredLogger class."""

    def setup_method(self):
        """Reset logger state before each test."""
        reset_logger()

        # Create temporary log file
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = Path(self.temp_dir) / "test_pytest.log"

    def teardown_method(self):
        """Clean up after each test."""
        if self.log_file.exists():
            self.log_file.unlink()
        Path(self.temp_dir).rmdir()

    def read_log_entries(self):
        """Helper to read log entries from file."""
        if not self.log_file.exists():
            return []

        entries = []
        with open(self.log_file, "r") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line.strip()))
        return entries

    def test_logger_initialization(self):
        """Test logger initialization with custom log file."""
        logger = PytestStructuredLogger(str(self.log_file))

        assert logger.enabled is True
        assert logger.log_file == self.log_file
        assert logger.session_id is not None
        assert len(logger.session_id) == 8  # UUID length
        assert logger.session_start_time > 0

    def test_logger_disabled(self):
        """Test logger when disabled."""
        logger = PytestStructuredLogger(str(self.log_file), enabled=False)

        assert logger.enabled is False

        # Should not create log file when disabled
        logger.log_session_start(["test"])
        assert not self.log_file.exists()

    def test_log_session_start(self):
        """Test session start logging."""
        logger = PytestStructuredLogger(str(self.log_file))

        logger.log_session_start(markers=["local", "db"])

        entries = self.read_log_entries()
        assert len(entries) == 1

        entry = entries[0]
        assert entry["event_type"] == "session_start"
        assert entry["markers"] == ["local", "db"]
        assert entry["test_session_id"] == logger.session_id
        assert "timestamp" in entry
        assert "python_version" in entry
        assert "working_directory" in entry

    def test_log_session_end(self):
        """Test session end logging."""
        logger = PytestStructuredLogger(str(self.log_file))

        logger.log_session_end(passed=8, failed=2, skipped=1, errors=0, duration=123.45)

        entries = self.read_log_entries()
        assert len(entries) == 1

        entry = entries[0]
        assert entry["event_type"] == "session_end"
        assert entry["summary"]["passed"] == 8
        assert entry["summary"]["failed"] == 2
        assert entry["summary"]["skipped"] == 1
        assert entry["summary"]["errors"] == 0
        assert entry["summary"]["total"] == 11
        assert entry["duration"] == 123.45

    def test_log_test_start(self):
        """Test test start logging."""
        logger = PytestStructuredLogger(str(self.log_file))

        logger.log_test_start(
            test_path="tests/unit/test_example.py::test_function",
            markers=["db", "local"],
            fixtures=["db_connection"],
            parametrize="{'param': 'value'}",
        )

        entries = self.read_log_entries()
        assert len(entries) == 1

        entry = entries[0]
        assert entry["event_type"] == "test_start"
        assert entry["test_path"] == "tests/unit/test_example.py::test_function"
        assert entry["metadata"]["markers"] == ["db", "local"]
        assert entry["metadata"]["fixtures"] == ["db_connection"]
        assert entry["metadata"]["parametrize"] == "{'param': 'value'}"

    def test_log_test_result_passed(self):
        """Test logging a passed test result."""
        logger = PytestStructuredLogger(str(self.log_file))

        logger.log_test_result(
            test_path="tests/unit/test_example.py::test_function",
            status="PASSED",
            duration=1.23,
            stdout="Test output",
            stderr="",
            failure_reason="",
            markers=["db"],
            fixtures=["db_connection"],
            parametrize="",
        )

        entries = self.read_log_entries()
        assert len(entries) == 1

        entry = entries[0]
        assert entry["event_type"] == "test_result"
        assert entry["status"] == "PASSED"
        assert entry["duration"] == 1.23
        assert entry["stdout"] == "Test output"
        assert entry["stderr"] == ""
        assert entry["failure_reason"] == ""

    def test_log_test_result_failed(self):
        """Test logging a failed test result."""
        logger = PytestStructuredLogger(str(self.log_file))

        failure_reason = "AssertionError: Expected 5 but got 3"

        logger.log_test_result(
            test_path="tests/unit/test_example.py::test_function",
            status="FAILED",
            duration=0.45,
            stdout="",
            stderr="Error output",
            failure_reason=failure_reason,
            markers=["db"],
            fixtures=["db_connection"],
            parametrize="",
        )

        entries = self.read_log_entries()
        assert len(entries) == 1

        entry = entries[0]
        assert entry["event_type"] == "test_result"
        assert entry["status"] == "FAILED"
        assert entry["duration"] == 0.45
        assert entry["stderr"] == "Error output"
        assert entry["failure_reason"] == failure_reason

    def test_log_test_end(self):
        """Test test end logging."""
        logger = PytestStructuredLogger(str(self.log_file))

        logger.log_test_end(test_path="tests/unit/test_example.py::test_function", duration=2.34)

        entries = self.read_log_entries()
        assert len(entries) == 1

        entry = entries[0]
        assert entry["event_type"] == "test_end"
        assert entry["test_path"] == "tests/unit/test_example.py::test_function"
        assert entry["duration"] == 2.34

    def test_log_custom_event(self):
        """Test custom event logging."""
        logger = PytestStructuredLogger(str(self.log_file))

        logger.log_custom_event("custom_event", custom_field="custom_value", another_field=42)

        entries = self.read_log_entries()
        assert len(entries) == 1

        entry = entries[0]
        assert entry["event_type"] == "custom_event"
        assert entry["custom_field"] == "custom_value"
        assert entry["another_field"] == 42

    def test_multiple_log_entries(self):
        """Test multiple log entries in sequence."""
        logger = PytestStructuredLogger(str(self.log_file))

        logger.log_session_start(["test"])
        logger.log_test_start("test1", ["marker1"], ["fixture1"])
        logger.log_test_result("test1", "PASSED", 1.0, "", "", "", ["marker1"], ["fixture1"])
        logger.log_test_end("test1", 1.0)
        logger.log_session_end(1, 0, 0, 0, 2.0)

        entries = self.read_log_entries()
        assert len(entries) == 5

        # Check sequence
        assert entries[0]["event_type"] == "session_start"
        assert entries[1]["event_type"] == "test_start"
        assert entries[2]["event_type"] == "test_result"
        assert entries[3]["event_type"] == "test_end"
        assert entries[4]["event_type"] == "session_end"

        # Check same session ID
        session_id = entries[0]["test_session_id"]
        for entry in entries:
            assert entry["test_session_id"] == session_id


class TestLoggerGlobals:
    """Test global logger functionality."""

    def setup_method(self):
        """Reset logger state before each test."""
        reset_logger()
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = Path(self.temp_dir) / "test_global.log"

    def teardown_method(self):
        """Clean up after each test."""
        if self.log_file.exists():
            self.log_file.unlink()
        Path(self.temp_dir).rmdir()

    def test_get_logger_singleton(self):
        """Test that get_logger returns the same instance."""
        logger1 = get_logger(str(self.log_file))
        logger2 = get_logger(str(self.log_file))

        assert logger1 is logger2
        assert logger1.session_id == logger2.session_id

    def test_get_logger_enabled_environment(self):
        """Test get_logger respects environment variable."""
        reset_logger()
        with patch.dict(os.environ, {"PYTEST_STRUCTURED_LOGGING": "false"}):
            logger = get_logger(str(self.log_file))
            assert logger.enabled is False

        reset_logger()
        with patch.dict(os.environ, {"PYTEST_STRUCTURED_LOGGING": "true"}):
            reset_logger()
            logger = get_logger(str(self.log_file))
            assert logger.enabled is True

    def test_reset_logger(self):
        """Test logger reset functionality."""
        logger1 = get_logger(str(self.log_file))
        session_id1 = logger1.session_id

        reset_logger()

        logger2 = get_logger(str(self.log_file))
        session_id2 = logger2.session_id

        assert logger1 is not logger2
        assert session_id1 != session_id2


@pytest.mark.logger
class TestLoggerIntegration:
    """Integration tests for logger with pytest."""

    def test_logger_with_pytest_markers(self):
        """Test that logger works with pytest markers."""
        # This test itself should be logged
        logger = get_logger()
        assert logger is not None
        assert logger.enabled is True

    def test_logger_performance_impact(self):
        """Test that logging doesn't significantly impact performance."""
        logger = get_logger()

        # Time without logging
        start = time.time()
        for i in range(100):
            pass
        baseline = time.time() - start

        # Time with logging
        start = time.time()
        for i in range(100):
            logger.log_custom_event("performance_test", iteration=i)
        logged = time.time() - start

        # Logging should not add more than 10x overhead
        assert logged < (baseline * 10 + 0.1)  # Add 0.1s buffer for file I/O
