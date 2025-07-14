"""
Tests for log parser utilities.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.utils.log_parser import PytestLogParser


class TestPytestLogParser:
    """Test the PytestLogParser class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = Path(self.temp_dir) / "test_parser.log"
        self.parser = PytestLogParser(str(self.log_file))

    def teardown_method(self):
        """Clean up after each test."""
        if self.log_file.exists():
            self.log_file.unlink()
        Path(self.temp_dir).rmdir()

    def create_sample_log_entries(self):
        """Create sample log entries for testing."""
        entries = [
            {
                "timestamp": "2025-01-13T10:30:00Z",
                "test_session_id": "test-session-123",
                "event_type": "session_start",
                "total_tests": 4,
                "markers": ["local", "db"],
                "python_version": "3.9.7",
                "working_directory": "/test/path",
            },
            {
                "timestamp": "2025-01-13T10:30:01Z",
                "test_session_id": "test-session-123",
                "event_type": "test_result",
                "test_path": "tests/unit/test_fast.py::test_quick",
                "status": "PASSED",
                "duration": 0.01,
                "stdout": "Quick test",
                "stderr": "",
                "failure_reason": "",
                "metadata": {"markers": ["local"], "fixtures": [], "parametrize": ""},
            },
            {
                "timestamp": "2025-01-13T10:30:02Z",
                "test_session_id": "test-session-123",
                "event_type": "test_result",
                "test_path": "tests/unit/test_slow.py::test_heavy",
                "status": "PASSED",
                "duration": 5.67,
                "stdout": "Heavy computation",
                "stderr": "",
                "failure_reason": "",
                "metadata": {"markers": ["db"], "fixtures": ["db_connection"], "parametrize": ""},
            },
            {
                "timestamp": "2025-01-13T10:30:03Z",
                "test_session_id": "test-session-123",
                "event_type": "test_result",
                "test_path": "tests/unit/test_error.py::test_broken",
                "status": "FAILED",
                "duration": 0.45,
                "stdout": "",
                "stderr": "Connection error",
                "failure_reason": "ConnectionError: Database connection failed",
                "metadata": {"markers": ["db"], "fixtures": ["db_connection"], "parametrize": ""},
            },
            {
                "timestamp": "2025-01-13T10:30:04Z",
                "test_session_id": "test-session-123",
                "event_type": "test_result",
                "test_path": "tests/unit/test_skip.py::test_conditional",
                "status": "SKIPPED",
                "duration": 0.01,
                "stdout": "",
                "stderr": "",
                "failure_reason": "",
                "metadata": {"markers": ["local"], "fixtures": [], "parametrize": ""},
            },
            {
                "timestamp": "2025-01-13T10:30:05Z",
                "test_session_id": "test-session-123",
                "event_type": "session_end",
                "summary": {"passed": 2, "failed": 1, "skipped": 1, "errors": 0, "total": 4},
                "duration": 10.5,
            },
        ]

        # Write entries to log file
        with open(self.log_file, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        return entries

    def test_validate_log_format_empty(self):
        """Test validation with empty log file."""
        result = self.parser.validate_log_format()
        assert result is False

    def test_validate_log_format_valid(self):
        """Test validation with valid log file."""
        self.create_sample_log_entries()

        # Capture print output
        with patch("builtins.print") as mock_print:
            result = self.parser.validate_log_format()

        assert result is True

        # Check that validation messages were printed
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        assert any("Found 6 log entries" in call for call in print_calls)
        assert any("All entries have required fields" in call for call in print_calls)
        assert any("Session boundaries found" in call for call in print_calls)

    def test_validate_log_format_missing_fields(self):
        """Test validation with missing required fields."""
        # Create invalid entries
        entries = [
            {"timestamp": "2025-01-13T10:30:00Z", "event_type": "session_start"},  # Missing test_session_id
            {"test_session_id": "123", "event_type": "test_result"},  # Missing timestamp
        ]

        with open(self.log_file, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        # TODO: I dont love that we're patching print -- don't fully understand why we need to do it (yet).
        with patch("builtins.print") as mock_print:
            result = self.parser.validate_log_format()

        # assert result is True  # Still valid if some entries are good
        assert result is False

        print_calls = [call.args[0] for call in mock_print.call_args_list]
        assert any("missing required fields" in call for call in print_calls)

    def test_summarize_tests(self):
        """Test test summarization."""
        self.create_sample_log_entries()

        summary = self.parser.summarize_tests()

        assert "Test Session Summary" in summary
        assert "Total Tests: 4" in summary
        assert "Passed: 2" in summary
        assert "Failed: 1" in summary
        assert "Duration: 10.50s" in summary

    def test_summarize_tests_with_limit(self):
        """Test test summarization with entry limit."""
        self.create_sample_log_entries()

        summary = self.parser.summarize_tests(recent=3)

        # Should still work with limited entries
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_extract_failures_with_reasons(self):
        """Test extracting failures with reasons."""
        self.create_sample_log_entries()

        failures = self.parser.extract_failures(include_reasons=True)

        assert "Failed Tests" in failures
        assert "test_broken" in failures
        assert "ConnectionError: Database connection failed" in failures
        assert "Duration: 0.450s" in failures

    def test_extract_failures_without_reasons(self):
        """Test extracting failures without reasons."""
        self.create_sample_log_entries()

        failures = self.parser.extract_failures(include_reasons=False)

        assert "test_broken" in failures
        assert "ConnectionError" not in failures
        assert "Duration" not in failures

    def test_extract_failures_none(self):
        """Test extracting failures when none exist."""
        # Create entries with only passed tests
        entries = [
            {
                "event_type": "test_result",
                "status": "PASSED",
                "test_path": "test_pass",
                "duration": 1.0,
                "failure_reason": "",
            }
        ]

        with open(self.log_file, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        failures = self.parser.extract_failures(include_reasons=False)
        assert failures == "No failed tests found."

    def test_llm_format(self):
        """Test LLM-friendly formatting."""
        self.create_sample_log_entries()

        llm_output = self.parser.llm_format()

        # Should contain structured sections
        assert "TEST SESSION SUMMARY:" in llm_output
        assert "PERFORMANCE METRICS:" in llm_output
        assert "FAILED TESTS:" in llm_output
        assert "TEST MARKERS:" in llm_output

        # Should contain specific data
        assert "Total: 4" in llm_output
        assert "Passed: 2" in llm_output
        assert "Failed: 1" in llm_output
        assert "test_broken" in llm_output
        assert "local: 2 tests" in llm_output
        assert "db: 2 tests" in llm_output

    def test_llm_format_with_limit(self):
        """Test LLM formatting with entry limit."""
        self.create_sample_log_entries()

        llm_output = self.parser.llm_format(recent=3)

        # Should still produce valid output
        assert isinstance(llm_output, str)
        assert len(llm_output) > 0

    def test_export_json(self):
        """Test JSON export functionality."""
        self.create_sample_log_entries()

        json_output = self.parser.export_json()

        # Should be valid JSON
        data = json.loads(json_output)

        # Check structure
        assert "session_info" in data
        assert "test_results" in data
        assert "performance_metrics" in data
        assert "failure_patterns" in data
        assert "marker_usage" in data

        # Check content
        assert data["session_info"]["summary"]["total"] == 4
        assert len(data["test_results"]) == 4
        assert len(data["failure_patterns"]) == 1
        assert data["marker_usage"]["local"] == 2
        assert data["marker_usage"]["db"] == 2

    def test_export_json_with_limit(self):
        """Test JSON export with entry limit."""
        self.create_sample_log_entries()

        json_output = self.parser.export_json(recent=3)

        # Should be valid JSON
        data = json.loads(json_output)

        # Should have limited data
        assert isinstance(data, dict)
        assert "test_results" in data

    def test_llm_test(self):
        """Test LLM compatibility testing."""
        self.create_sample_log_entries()

        llm_test_output = self.parser.llm_test()

        assert "LLM COMPATIBILITY TEST" in llm_test_output
        assert "Query:" in llm_test_output
        assert "Answer:" in llm_test_output

        # Should contain answers to sample queries
        assert "failing" in llm_test_output.lower()
        assert "performance" in llm_test_output.lower()
        assert "markers" in llm_test_output.lower()

    def test_llm_test_empty_log(self):
        """Test LLM compatibility with empty log."""
        llm_test_output = self.parser.llm_test()

        assert "No log entries found for testing" in llm_test_output


@pytest.mark.log_enabled
class TestLogParserIntegration:
    """Integration tests for log parser."""

    def test_parser_with_default_log_file(self):
        """Test parser with default log file location."""
        parser = PytestLogParser()

        # Should handle case where log file doesn't exist yet
        summary = parser.summarize_tests()
        assert isinstance(summary, str)

    def test_parser_validation_real_file(self):
        """Test validation with real log file."""
        parser = PytestLogParser()

        # Should not crash even if file doesn't exist
        result = parser.validate_log_format()
        assert isinstance(result, bool)
