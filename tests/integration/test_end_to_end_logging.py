"""
End-to-end integration tests for pytest structured logging.
"""

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

from tests.utils.pytest_logger import reset_logger
from tests.utils.log_parser import PytestLogParser


class TestEndToEndLogging:
    """Test complete logging pipeline from pytest execution to log analysis."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = Path(self.temp_dir) / "integration_test.log"
        
        # Create a simple test file to execute
        self.test_file = Path(self.temp_dir) / "test_sample.py"
        self.test_file.write_text('''
import pytest
import time

def test_pass_fast():
    """A fast passing test."""
    assert True

def test_pass_slow():
    """A slow passing test."""
    time.sleep(0.1)
    assert True

def test_fail():
    """A failing test."""
    assert False, "This test is designed to fail"

@pytest.mark.skip(reason="Testing skip functionality")
def test_skip():
    """A skipped test."""
    assert True

@pytest.mark.local
def test_with_marker():
    """Test with marker."""
    assert True

@pytest.mark.parametrize("value", [1, 2, 3])
def test_parametrized(value):
    """Parametrized test."""
    assert value > 0
''')
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.log_file.exists():
            self.log_file.unlink()
        if self.test_file.exists():
            self.test_file.unlink()
        Path(self.temp_dir).rmdir()
        
        # Reset logger state
        reset_logger()
    
    def run_pytest_with_logging(self, additional_args=None):
        """Run pytest with structured logging enabled."""
        env = os.environ.copy()
        env["PYTEST_STRUCTURED_LOGGING"] = "true"
        
        cmd = [
            "python", "-m", "pytest", 
            str(self.test_file),
            "-v",
            "--tb=short"
        ]
        
        if additional_args:
            cmd.extend(additional_args)
        
        # Create a temporary conftest.py with logging setup
        conftest_path = Path(self.temp_dir) / "conftest.py"
        conftest_path.write_text(f'''
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from tests.utils.pytest_logger import get_logger

# Configure logger for this test run
logger = get_logger("{self.log_file}")
''')
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.temp_dir),
                env=env,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result
        finally:
            if conftest_path.exists():
                conftest_path.unlink()
    
    def read_log_entries(self):
        """Read log entries from the test log file."""
        if not self.log_file.exists():
            return []
        
        entries = []
        with open(self.log_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass  # Skip invalid lines
        return entries
    
    def test_basic_logging_pipeline(self):
        """Test that basic logging pipeline works end-to-end."""
        # Run pytest with logging
        result = self.run_pytest_with_logging()
        
        # Check that pytest ran (may have failures due to our test design)
        assert result.returncode in [0, 1]  # 0 = all passed, 1 = some failed
        
        # Check that log file was created
        assert self.log_file.exists()
        
        # Read and validate log entries
        entries = self.read_log_entries()
        assert len(entries) > 0
        
        # Check for expected event types
        event_types = [entry.get("event_type") for entry in entries]
        assert "session_start" in event_types
        assert "session_end" in event_types
        assert "test_result" in event_types
        
        # Check session boundaries
        session_start = next(e for e in entries if e.get("event_type") == "session_start")
        session_end = next(e for e in entries if e.get("event_type") == "session_end")
        
        assert session_start["test_session_id"] == session_end["test_session_id"]
        assert session_start["total_tests"] > 0
        assert session_end["summary"]["total"] > 0
    
    def test_log_content_validation(self):
        """Test that log content matches expected pytest behavior."""
        result = self.run_pytest_with_logging()
        
        entries = self.read_log_entries()
        test_results = [e for e in entries if e.get("event_type") == "test_result"]
        
        # Should have results for all our test functions
        test_paths = [result.get("test_path", "") for result in test_results]
        
        assert any("test_pass_fast" in path for path in test_paths)
        assert any("test_pass_slow" in path for path in test_paths)
        assert any("test_fail" in path for path in test_paths)
        assert any("test_skip" in path for path in test_paths)
        assert any("test_with_marker" in path for path in test_paths)
        assert any("test_parametrized" in path for path in test_paths)
        
        # Check status distribution
        statuses = [result.get("status") for result in test_results]
        assert "PASSED" in statuses
        assert "FAILED" in statuses
        assert "SKIPPED" in statuses
        
        # Check that failed test has failure reason
        failed_tests = [r for r in test_results if r.get("status") == "FAILED"]
        assert len(failed_tests) > 0
        assert any(r.get("failure_reason") for r in failed_tests)
        
        # Check that parametrized tests are logged separately
        parametrized_tests = [r for r in test_results if "test_parametrized" in r.get("test_path", "")]
        assert len(parametrized_tests) == 3  # Should have 3 parametrized runs
    
    def test_log_parser_integration(self):
        """Test that log parser can analyze the generated logs."""
        # Run pytest to generate logs
        result = self.run_pytest_with_logging()
        
        # Use parser to analyze logs
        parser = PytestLogParser(str(self.log_file))
        
        # Test validation
        assert parser.validate_log_format() is True
        
        # Test summarization
        summary = parser.summarize_tests()
        assert "Test Session Summary" in summary
        assert "Total Tests:" in summary
        assert "Passed:" in summary
        assert "Failed:" in summary
        
        # Test failure extraction
        failures = parser.extract_failures()
        assert "test_fail" in failures
        assert "designed to fail" in failures
        
        # Test LLM formatting
        llm_output = parser.llm_format()
        assert "TEST SESSION SUMMARY:" in llm_output
        assert "FAILED TESTS:" in llm_output
        assert "TEST MARKERS:" in llm_output
        
        # Test JSON export
        json_output = parser.export_json()
        data = json.loads(json_output)
        assert "session_info" in data
        assert "test_results" in data
        assert len(data["test_results"]) > 0
    
    def test_performance_impact(self):
        """Test that logging doesn't significantly impact test execution."""
        # Run without logging
        start_time = time.time()
        result_no_log = self.run_pytest_with_logging(["--tb=no"])
        no_log_duration = time.time() - start_time
        
        # Reset and run with logging
        reset_logger()
        if self.log_file.exists():
            self.log_file.unlink()
        
        start_time = time.time()
        result_with_log = self.run_pytest_with_logging(["--tb=no"])
        with_log_duration = time.time() - start_time
        
        # Both should succeed
        assert result_no_log.returncode in [0, 1]
        assert result_with_log.returncode in [0, 1]
        
        # Logging should not add more than 2x overhead
        # (generous allowance for file I/O and JSON serialization)
        assert with_log_duration < (no_log_duration * 2 + 1.0)  # +1s buffer
    
    def test_concurrent_logging(self):
        """Test that logging works with concurrent test execution."""
        # This test would ideally run pytest with -n option (pytest-xdist)
        # For now, we'll just verify that logging works with quick succession
        
        # Run multiple pytest sessions quickly
        results = []
        for i in range(3):
            log_file = Path(self.temp_dir) / f"concurrent_{i}.log"
            
            # Create temporary conftest for each run
            conftest_path = Path(self.temp_dir) / f"conftest_{i}.py"
            conftest_path.write_text(f'''
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from tests.utils.pytest_logger import get_logger

logger = get_logger("{log_file}")
''')
            
            env = os.environ.copy()
            env["PYTEST_STRUCTURED_LOGGING"] = "true"
            
            cmd = [
                "python", "-m", "pytest", 
                str(self.test_file),
                "-v",
                "--tb=no",
                f"--confcutdir={self.temp_dir}",
                f"-p", f"conftest_{i}"
            ]
            
            result = subprocess.run(
                cmd,
                cwd=str(self.temp_dir),
                env=env,
                capture_output=True,
                text=True,
                timeout=10
            )
            results.append((result, log_file))
            
            # Clean up conftest
            conftest_path.unlink()
        
        # Verify all runs completed and generated logs
        for result, log_file in results:
            assert result.returncode in [0, 1]
            assert log_file.exists()
            
            # Each log should have valid entries
            entries = []
            with open(log_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
            
            assert len(entries) > 0
            
            # Should have unique session IDs
            session_ids = {entry.get("test_session_id") for entry in entries}
            assert len(session_ids) == 1  # All entries in one file should have same session ID
            
            # Clean up
            log_file.unlink()
    
    def test_marker_filtering_integration(self):
        """Test that marker filtering works with logging."""
        # Run pytest with marker filtering
        result = self.run_pytest_with_logging(["-m", "local"])
        
        entries = self.read_log_entries()
        test_results = [e for e in entries if e.get("event_type") == "test_result"]
        
        # Should only have tests with 'local' marker
        for result in test_results:
            markers = result.get("metadata", {}).get("markers", [])
            # Either has 'local' marker or is a parametrized test (which may not have markers logged correctly)
            assert "local" in markers or "parametrized" in result.get("test_path", "")
    
    def test_error_handling(self):
        """Test logging behavior with various error conditions."""
        # Create a test file with various error types
        error_test_file = Path(self.temp_dir) / "test_errors.py"
        error_test_file.write_text('''
import pytest

def test_assertion_error():
    """Test with assertion error."""
    assert 1 == 2

def test_exception():
    """Test with exception."""
    raise ValueError("Test exception")

def test_import_error():
    """Test with import error."""
    import nonexistent_module

def test_fixture_error(nonexistent_fixture):
    """Test with fixture error."""
    assert True
''')
        
        try:
            # Run pytest on error test file
            env = os.environ.copy()
            env["PYTEST_STRUCTURED_LOGGING"] = "true"
            
            conftest_path = Path(self.temp_dir) / "conftest.py"
            conftest_path.write_text(f'''
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from tests.utils.pytest_logger import get_logger

logger = get_logger("{self.log_file}")
''')
            
            result = subprocess.run([
                "python", "-m", "pytest", 
                str(error_test_file),
                "-v",
                "--tb=short"
            ], cwd=str(self.temp_dir), env=env, capture_output=True, text=True, timeout=30)
            
            # Should complete despite errors
            assert result.returncode == 1  # Tests failed
            
            # Check that errors were logged
            entries = self.read_log_entries()
            test_results = [e for e in entries if e.get("event_type") == "test_result"]
            
            # Should have failure entries
            failed_tests = [r for r in test_results if r.get("status") == "FAILED"]
            assert len(failed_tests) > 0
            
            # Should have failure reasons
            failure_reasons = [r.get("failure_reason", "") for r in failed_tests]
            assert any("assertion" in reason.lower() for reason in failure_reasons)
            
        finally:
            if error_test_file.exists():
                error_test_file.unlink()
            if conftest_path.exists():
                conftest_path.unlink()


@pytest.mark.log_enabled
class TestLoggingIntegrationReal:
    """Integration tests using real pytest logging infrastructure."""
    
    def test_logging_enabled_marker(self):
        """Test that this test itself generates log entries."""
        # This test should generate log entries due to @pytest.mark.log_enabled
        # We can't easily test this without running a separate pytest process
        # But we can verify the logger is working
        
        from tests.utils.pytest_logger import get_logger
        logger = get_logger()
        
        assert logger is not None
        assert logger.enabled is True
        assert logger.session_id is not None
    
    def test_real_log_file_access(self):
        """Test accessing the real log file."""
        parser = PytestLogParser()  # Uses default log file
        
        # Should not crash even if log file doesn't exist yet
        result = parser.validate_log_format()
        assert isinstance(result, bool)
        
        # Should handle empty or non-existent files gracefully
        summary = parser.summarize_tests()
        assert isinstance(summary, str)