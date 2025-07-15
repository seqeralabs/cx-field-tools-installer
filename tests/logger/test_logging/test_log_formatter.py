"""
Tests for log formatting utilities.
"""

import json
import tempfile
from pathlib import Path

import pytest

from tests.utils.log_formatter import PytestLogFormatter


class TestPytestLogFormatter:
    """Test the PytestLogFormatter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = Path(self.temp_dir) / "test_format.log"
        self.formatter = PytestLogFormatter(str(self.log_file))

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
                "total_tests": 3,
                "markers": ["local", "db"],
                "python_version": "3.9.7",
                "working_directory": "/test/path",
            },
            {
                "timestamp": "2025-01-13T10:30:01Z",
                "test_session_id": "test-session-123",
                "event_type": "test_start",
                "test_path": "tests/unit/test_example.py::test_pass",
                "metadata": {"markers": ["local"], "fixtures": ["fixture1"], "parametrize": ""},
            },
            {
                "timestamp": "2025-01-13T10:30:02Z",
                "test_session_id": "test-session-123",
                "event_type": "test_result",
                "test_path": "tests/unit/test_example.py::test_pass",
                "status": "PASSED",
                "duration": 1.23,
                "stdout": "Test passed",
                "stderr": "",
                "failure_reason": "",
                "metadata": {"markers": ["local"], "fixtures": ["fixture1"], "parametrize": ""},
            },
            {
                "timestamp": "2025-01-13T10:30:03Z",
                "test_session_id": "test-session-123",
                "event_type": "test_result",
                "test_path": "tests/unit/test_example.py::test_fail",
                "status": "FAILED",
                "duration": 0.45,
                "stdout": "",
                "stderr": "Error occurred",
                "failure_reason": "AssertionError: Expected 5 but got 3",
                "metadata": {"markers": ["db"], "fixtures": ["fixture2"], "parametrize": ""},
            },
            {
                "timestamp": "2025-01-13T10:30:04Z",
                "test_session_id": "test-session-123",
                "event_type": "test_result",
                "test_path": "tests/unit/test_example.py::test_skip",
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
                "summary": {"passed": 1, "failed": 1, "skipped": 1, "errors": 0, "total": 3},
                "duration": 5.0,
            },
        ]

        # Write entries to log file
        with open(self.log_file, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        return entries

    def test_read_log_entries_empty_file(self):
        """Test reading from empty log file."""
        entries = self.formatter.read_log_entries()
        assert entries == []

    def test_read_log_entries_nonexistent_file(self):
        """Test reading from non-existent log file."""
        formatter = PytestLogFormatter("/nonexistent/file.log")
        entries = formatter.read_log_entries()
        assert entries == []

    def test_read_log_entries_valid_file(self):
        """Test reading valid log entries."""
        sample_entries = self.create_sample_log_entries()
        entries = self.formatter.read_log_entries()

        assert len(entries) == 6
        assert entries[0]["event_type"] == "session_start"
        assert entries[-1]["event_type"] == "session_end"

    def test_read_log_entries_with_limit(self):
        """Test reading log entries with limit."""
        self.create_sample_log_entries()
        entries = self.formatter.read_log_entries(max_entries=3)

        assert len(entries) == 3
        assert entries[0]["event_type"] == "session_start"
        assert entries[2]["event_type"] == "test_result"

    def test_read_log_entries_invalid_json(self):
        """Test reading log file with invalid JSON."""
        with open(self.log_file, "w") as f:
            f.write('{"valid": "json"}\n')
            f.write("invalid json line\n")
            f.write('{"another": "valid"}\n')

        entries = self.formatter.read_log_entries()
        assert len(entries) == 2
        assert entries[0]["valid"] == "json"
        assert entries[1]["another"] == "valid"

    def test_format_test_summary(self):
        """Test formatting test summary."""
        self.create_sample_log_entries()
        entries = self.formatter.read_log_entries()

        summary = self.formatter.format_test_summary(entries)

        assert "Test Session Summary" in summary
        assert "Total Tests: 3" in summary
        assert "Passed: 1" in summary
        assert "Failed: 1" in summary
        assert "Skipped: 1" in summary
        assert "Duration: 5.00s" in summary
        assert "Success Rate: 33.3%" in summary

    def test_format_test_summary_empty(self):
        """Test formatting empty test summary."""
        summary = self.formatter.format_test_summary([])
        assert summary == "No test entries found."

    def test_format_failed_tests(self):
        """Test formatting failed tests."""
        self.create_sample_log_entries()
        entries = self.formatter.read_log_entries()

        failed_output = self.formatter.format_failed_tests(entries)

        assert "Failed Tests" in failed_output
        assert "test_fail" in failed_output
        assert "AssertionError" in failed_output
        assert "Duration: 0.450s" in failed_output

    def test_format_failed_tests_none(self):
        """Test formatting failed tests when none exist."""
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

        failed_output = self.formatter.format_failed_tests(entries)
        assert failed_output == "No failed tests found."

    def test_format_test_performance(self):
        """Test formatting test performance."""
        self.create_sample_log_entries()
        entries = self.formatter.read_log_entries()

        performance = self.formatter.format_test_performance(entries)

        assert "Test Performance" in performance
        assert "test_pass" in performance
        assert "test_fail" in performance
        assert "1.230s" in performance  # Slowest first
        assert "0.450s" in performance

    def test_format_test_performance_empty(self):
        """Test formatting empty performance data."""
        performance = self.formatter.format_test_performance([])
        assert performance == "No test results found."

    def test_format_marker_summary(self):
        """Test formatting marker summary."""
        self.create_sample_log_entries()
        entries = self.formatter.read_log_entries()

        marker_summary = self.formatter.format_marker_summary(entries)

        assert "Test Markers Summary" in marker_summary
        assert "local" in marker_summary
        assert "db" in marker_summary
        # Check that it shows counts and percentages
        assert "total" in marker_summary
        assert "passed" in marker_summary
        assert "failed" in marker_summary

    def test_format_marker_summary_empty(self):
        """Test formatting empty marker summary."""
        marker_summary = self.formatter.format_marker_summary([])
        assert marker_summary == "No markers found."

    def test_format_human_readable(self):
        """Test complete human-readable formatting."""
        self.create_sample_log_entries()
        entries = self.formatter.read_log_entries()

        report = self.formatter.format_human_readable(entries)

        # Should contain all sections
        assert "Test Session Summary" in report
        assert "Failed Tests" in report
        assert "Test Performance" in report
        assert "Test Markers Summary" in report

    def test_clean_output_for_llm(self):
        """Test cleaning output for LLM consumption."""
        dirty_text = "\x1b[31mError\x1b[0m\n\n\n  Multiple   spaces  \n\n============================="

        clean_text = self.formatter.clean_output_for_llm(dirty_text)

        # Should remove ANSI codes
        assert "\x1b[31m" not in clean_text
        assert "\x1b[0m" not in clean_text

        # Should normalize whitespace
        assert "Multiple spaces" in clean_text

        # Should reduce excessive punctuation
        assert "====" in clean_text
        assert "=====" not in clean_text or clean_text.count("=") <= 8

    def test_extract_key_insights(self):
        """Test extracting key insights."""
        self.create_sample_log_entries()
        entries = self.formatter.read_log_entries()

        insights = self.formatter.extract_key_insights(entries)

        # Check structure
        assert "session_info" in insights
        assert "test_results" in insights
        assert "performance_metrics" in insights
        assert "failure_patterns" in insights
        assert "marker_usage" in insights

        # Check session info
        assert insights["session_info"]["summary"]["total"] == 3
        assert insights["session_info"]["duration"] == 5.0

        # Check test results
        assert len(insights["test_results"]) == 3
        assert insights["test_results"][0]["status"] == "PASSED"
        assert insights["test_results"][1]["status"] == "FAILED"

        # Check performance metrics
        perf = insights["performance_metrics"]
        assert perf["total_tests"] == 3
        assert perf["max_duration"] == 1.23
        assert perf["min_duration"] == 0.01
        assert 0 < perf["avg_duration"] < 1

        # Check failure patterns
        assert len(insights["failure_patterns"]) == 1
        assert "test_fail" in insights["failure_patterns"][0]["test_path"]
        assert "AssertionError" in insights["failure_patterns"][0]["failure_reason"]

        # Check marker usage
        assert insights["marker_usage"]["local"] == 2
        assert insights["marker_usage"]["db"] == 1


@pytest.mark.logger
class TestLogFormatterIntegration:
    """Integration tests for log formatter."""

    def test_formatter_with_real_log_file(self):
        """Test formatter with actual pytest log file."""
        # This will use the default log file location
        formatter = PytestLogFormatter()

        # Should handle case where log file doesn't exist yet
        entries = formatter.read_log_entries()
        assert isinstance(entries, list)

        # Should be able to format even empty entries
        summary = formatter.format_test_summary(entries)
        assert isinstance(summary, str)
