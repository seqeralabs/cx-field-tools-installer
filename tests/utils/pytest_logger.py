"""
Pytest structured logging utilities for LLM-friendly test output capture.
"""

import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List

from tests.utils.local import root


class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class PytestStructuredLogger:
    """Centralized logger for pytest execution data in JSON Lines format."""

    def __init__(self, log_file: str = "", enabled: bool = True, log_level: LogLevel = LogLevel.INFO):
        self.enabled = enabled
        if not self.enabled:
            return

        # Default log file location
        if log_file == "":
            tests_dir = Path(__file__).parent.parent
            log_file = (tests_dir / "logs" / "pytest_structured.log").as_posix()

        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Session tracking
        self.session_id = str(uuid.uuid4())[:8]
        self.session_start_time = time.time()

        # Setup file handler
        self.logger = logging.getLogger(f"pytest_structured_{self.session_id}")
        self.logger.setLevel(log_level.value)

        # Remove existing handlers to avoid duplicates then create file handler
        self.logger.handlers.clear()
        handler = logging.FileHandler(self.log_file, mode="a", encoding="utf-8")
        handler.setLevel(log_level.value)

        # Use simple formatter since we're writing JSON
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

    def _create_base_entry(self, event_type: str, **kwargs) -> Dict[str, Any]:
        """
        Create base log entry with common fields.
        Other methods use this to generate a fulsome Python dictionary, then dump it to JSON output.
        """
        return {
            # "timestamp": datetime.utcnow().isoformat() + "Z",
            # "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "test_session_id": self.session_id,
            "event_type": event_type,
            **kwargs,
        }

    def log_session_start(self, markers: List[str] = []):
        """Log test session start."""
        if not self.enabled:
            return

        entry = self._create_base_entry(
            "session_start",
            markers=markers,
            python_version=sys.version,
            working_directory=str(Path.cwd()),
        )
        self.logger.info(json.dumps(entry))

    def log_collection_modifyitems(self, total_tests: int):
        """Log test session start."""
        if not self.enabled:
            return

        entry = self._create_base_entry(
            "collection_modifyitems",
            total_tests=total_tests,
            working_directory=str(Path.cwd()),
        )
        self.logger.info(json.dumps(entry))

    def log_deselected(self, deselected_count: int, reasons: List[str] = []):
        """Log information about tests that were deselected (filtered out)."""
        if not self.enabled:
            return

        entry = self._create_base_entry(
            "deselected",
            deselected_count=deselected_count,
            reasons=reasons,
            working_directory=str(Path.cwd()),
        )
        self.logger.info(json.dumps(entry))

    def log_session_end(self, passed: int, failed: int, skipped: int, errors: int, duration: float):
        """Log test session end with summary."""
        if not self.enabled:
            return

        entry = self._create_base_entry(
            "session_end",
            summary={
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "errors": errors,
                "total": passed + failed + skipped + errors,
            },
            duration=duration,
        )
        self.logger.info(json.dumps(entry))

    def log_test_start(self, test_path: str, markers: List[str] = [], fixtures: List[str] = [], parametrize: str = ""):
        """Log individual test start."""
        if not self.enabled:
            return

        entry = self._create_base_entry(
            "test_start",
            # test_path=test_path.replace(root, "<PROJECT_ROOT>"),
            test_path=test_path,
            metadata={"markers": markers, "fixtures": fixtures, "parametrize": parametrize},
        )
        self.logger.info(json.dumps(entry))

    def log_test_end(self, test_path: str, duration: float):
        """Log individual test end."""
        if not self.enabled:
            return

        entry = self._create_base_entry("test_end", test_path=test_path, duration=duration)
        self.logger.info(json.dumps(entry))

    def log_custom_event(self, event_type: str, **kwargs):
        """Log custom event with arbitrary data."""
        if not self.enabled:
            return

        entry = self._create_base_entry(event_type, **kwargs)
        self.logger.info(json.dumps(entry))

    def log_test_result(
        self,
        test_path: str,
        status: str,
        duration: float,
        stdout: str = "",
        stderr: str = "",
        failure_reason: str = "",
        markers: List[str] = [],
        fixtures: List[str] = [],
        parametrize: str = "",
    ):
        """Log individual test result."""
        if not self.enabled:
            return

        entry = self._create_base_entry(
            "test_result",
            # test_path=test_path,
            test_path=f"{root}/tests/{test_path}",
            status=status,
            duration=duration,
            stdout=stdout,
            stderr=stderr,
            failure_reason=failure_reason,
            metadata={"markers": markers, "fixtures": fixtures, "parametrize": parametrize},
        )
        self.logger.info(json.dumps(entry))


# Global logger instance
_logger_instance = None


def get_logger(log_file: str = "") -> PytestStructuredLogger:
    """Get or create global logger instance."""
    global _logger_instance

    # Check environment variable to see if should be disabled
    logger_setting = os.environ.get("PYTEST_STRUCTURED_LOGGING", "n/a")
    if logger_setting.lower() == "false":
        enabled = False
    else:
        enabled = True

    logger_level_setting = os.environ.get("PYTEST_STRUCTURED_LOGGING_LEVEL", LogLevel.INFO.name)
    if logger_level_setting != LogLevel.INFO.name:
        log_level = LogLevel[logger_level_setting]
    else:
        log_level = LogLevel.INFO

    if _logger_instance is None:
        _logger_instance = PytestStructuredLogger(log_file=log_file, enabled=enabled, log_level=log_level)

    return _logger_instance


def reset_logger():
    """Reset global logger instance (primarily for testing)."""
    global _logger_instance
    _logger_instance = None
