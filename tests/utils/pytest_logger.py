"""
Pytest structured logging utilities for LLM-friendly test output capture.
"""

import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List


class PytestStructuredLogger:
    """Centralized logger for pytest execution data in JSON Lines format."""
    
    def __init__(self, log_file: Optional[str] = None, enabled: bool = True):
        self.enabled = enabled
        if not self.enabled:
            return
            
        # Default log file location
        if log_file is None:
            tests_dir = Path(__file__).parent.parent
            log_file = tests_dir / "logs" / "pytest_structured.log"
        
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Session tracking
        self.session_id = str(uuid.uuid4())
        self.session_start_time = time.time()
        
        # Setup file handler
        self.logger = logging.getLogger(f"pytest_structured_{self.session_id}")
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Create file handler
        handler = logging.FileHandler(self.log_file, mode='a', encoding='utf-8')
        handler.setLevel(logging.INFO)
        
        # Use simple formatter since we're writing JSON
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        
    def _create_base_entry(self, event_type: str, **kwargs) -> Dict[str, Any]:
        """Create base log entry with common fields."""
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "test_session_id": self.session_id,
            "event_type": event_type,
            **kwargs
        }
    
    def log_session_start(self, total_tests: int, markers: List[str] = None):
        """Log test session start."""
        if not self.enabled:
            return
            
        entry = self._create_base_entry(
            "session_start",
            total_tests=total_tests,
            markers=markers or [],
            python_version=sys.version,
            working_directory=str(Path.cwd())
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
                "total": passed + failed + skipped + errors
            },
            duration=duration
        )
        self.logger.info(json.dumps(entry))
    
    def log_test_start(self, test_path: str, markers: List[str] = None, 
                      fixtures: List[str] = None, parametrize: str = ""):
        """Log individual test start."""
        if not self.enabled:
            return
            
        entry = self._create_base_entry(
            "test_start",
            test_path=test_path,
            metadata={
                "markers": markers or [],
                "fixtures": fixtures or [],
                "parametrize": parametrize
            }
        )
        self.logger.info(json.dumps(entry))
    
    def log_test_result(self, test_path: str, status: str, duration: float,
                       stdout: str = "", stderr: str = "", failure_reason: str = "",
                       markers: List[str] = None, fixtures: List[str] = None,
                       parametrize: str = ""):
        """Log individual test result."""
        if not self.enabled:
            return
            
        entry = self._create_base_entry(
            "test_result",
            test_path=test_path,
            status=status,
            duration=duration,
            stdout=stdout,
            stderr=stderr,
            failure_reason=failure_reason,
            metadata={
                "markers": markers or [],
                "fixtures": fixtures or [],
                "parametrize": parametrize
            }
        )
        self.logger.info(json.dumps(entry))
    
    def log_test_end(self, test_path: str, duration: float):
        """Log individual test end."""
        if not self.enabled:
            return
            
        entry = self._create_base_entry(
            "test_end",
            test_path=test_path,
            duration=duration
        )
        self.logger.info(json.dumps(entry))
    
    def log_custom_event(self, event_type: str, **kwargs):
        """Log custom event with arbitrary data."""
        if not self.enabled:
            return
            
        entry = self._create_base_entry(event_type, **kwargs)
        self.logger.info(json.dumps(entry))


# Global logger instance
_logger_instance = None

def get_logger(log_file: Optional[str] = None, enabled: bool = None) -> PytestStructuredLogger:
    """Get or create global logger instance."""
    global _logger_instance
    
    # Check environment variable for enabled state
    if enabled is None:
        enabled = os.environ.get("PYTEST_STRUCTURED_LOGGING", "true").lower() == "true"
    
    if _logger_instance is None:
        _logger_instance = PytestStructuredLogger(log_file=log_file, enabled=enabled)
    
    return _logger_instance


def reset_logger():
    """Reset global logger instance (primarily for testing)."""
    global _logger_instance
    _logger_instance = None