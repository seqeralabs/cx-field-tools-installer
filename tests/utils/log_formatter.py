"""
Log formatting utilities for pytest structured logging.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class PytestLogFormatter:
    """Formatter for pytest structured logs with various output options."""
    
    def __init__(self, log_file: Optional[str] = None):
        if log_file is None:
            tests_dir = Path(__file__).parent.parent
            log_file = tests_dir / "logs" / "pytest_structured.log"
        
        self.log_file = Path(log_file)
    
    def read_log_entries(self, max_entries: int = None) -> List[Dict[str, Any]]:
        """Read and parse JSON Lines from log file."""
        entries = []
        
        if not self.log_file.exists():
            return entries
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                        
                        if max_entries and len(entries) >= max_entries:
                            break
                            
                    except json.JSONDecodeError as e:
                        print(f"Warning: Invalid JSON on line {line_num}: {e}")
                        continue
                        
        except FileNotFoundError:
            print(f"Warning: Log file not found: {self.log_file}")
        except Exception as e:
            print(f"Error reading log file: {e}")
        
        return entries
    
    def format_test_summary(self, entries: List[Dict[str, Any]]) -> str:
        """Format test summary in human-readable format."""
        if not entries:
            return "No test entries found."
        
        # Find session summary
        session_summary = None
        for entry in entries:
            if entry.get('event_type') == 'session_end':
                session_summary = entry.get('summary', {})
                break
        
        if not session_summary:
            return "No session summary found."
        
        # Format summary
        total = session_summary.get('total', 0)
        passed = session_summary.get('passed', 0)
        failed = session_summary.get('failed', 0)
        skipped = session_summary.get('skipped', 0)
        errors = session_summary.get('errors', 0)
        
        # Get session duration
        duration = 0.0
        for entry in entries:
            if entry.get('event_type') == 'session_end':
                duration = entry.get('duration', 0.0)
                break
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
        summary = f"""
Test Session Summary
====================
Total Tests: {total}
Passed: {passed}
Failed: {failed}
Skipped: {skipped}
Errors: {errors}
Duration: {duration:.2f}s

Success Rate: {success_rate:.1f}% ({passed}/{total})
"""
        return summary.strip()
    
    def format_failed_tests(self, entries: List[Dict[str, Any]]) -> str:
        """Format failed tests with failure reasons."""
        failed_tests = []
        
        for entry in entries:
            if (entry.get('event_type') == 'test_result' and 
                entry.get('status') == 'FAILED'):
                failed_tests.append(entry)
        
        if not failed_tests:
            return "No failed tests found."
        
        output = ["Failed Tests", "=" * 40, ""]
        
        for i, test in enumerate(failed_tests, 1):
            test_path = test.get('test_path', 'Unknown')
            duration = test.get('duration', 0.0)
            failure_reason = test.get('failure_reason', 'No failure reason provided')
            
            output.extend([
                f"{i}. {test_path}",
                f"   Duration: {duration:.3f}s",
                f"   Failure: {failure_reason[:200]}{'...' if len(failure_reason) > 200 else ''}",
                ""
            ])
        
        return "\n".join(output)
    
    def format_test_performance(self, entries: List[Dict[str, Any]]) -> str:
        """Format test performance statistics."""
        test_results = []
        
        for entry in entries:
            if entry.get('event_type') == 'test_result':
                test_results.append(entry)
        
        if not test_results:
            return "No test results found."
        
        # Sort by duration (slowest first)
        test_results.sort(key=lambda x: x.get('duration', 0), reverse=True)
        
        output = ["Test Performance (Slowest First)", "=" * 40, ""]
        
        for i, test in enumerate(test_results[:10], 1):  # Top 10 slowest
            test_path = test.get('test_path', 'Unknown')
            duration = test.get('duration', 0.0)
            status = test.get('status', 'UNKNOWN')
            
            output.append(f"{i:2d}. {duration:6.3f}s [{status:>6s}] {test_path}")
        
        if len(test_results) > 10:
            output.append(f"\n... and {len(test_results) - 10} more tests")
        
        return "\n".join(output)
    
    def format_marker_summary(self, entries: List[Dict[str, Any]]) -> str:
        """Format summary of test markers usage."""
        marker_counts = {}
        
        for entry in entries:
            if entry.get('event_type') == 'test_result':
                markers = entry.get('metadata', {}).get('markers', [])
                for marker in markers:
                    if marker not in marker_counts:
                        marker_counts[marker] = {'total': 0, 'passed': 0, 'failed': 0}
                    
                    marker_counts[marker]['total'] += 1
                    if entry.get('status') == 'PASSED':
                        marker_counts[marker]['passed'] += 1
                    elif entry.get('status') == 'FAILED':
                        marker_counts[marker]['failed'] += 1
        
        if not marker_counts:
            return "No markers found."
        
        output = ["Test Markers Summary", "=" * 40, ""]
        
        for marker, counts in sorted(marker_counts.items()):
            total = counts['total']
            passed = counts['passed']
            failed = counts['failed']
            success_rate = (passed / total * 100) if total > 0 else 0
            
            output.append(f"{marker:15s}: {total:3d} total, {passed:3d} passed, {failed:3d} failed ({success_rate:5.1f}%)")
        
        return "\n".join(output)
    
    def format_human_readable(self, entries: List[Dict[str, Any]]) -> str:
        """Format complete human-readable report."""
        sections = [
            self.format_test_summary(entries),
            "",
            self.format_failed_tests(entries),
            "",
            self.format_test_performance(entries),
            "",
            self.format_marker_summary(entries)
        ]
        
        return "\n".join(sections)
    
    def clean_output_for_llm(self, text: str) -> str:
        """Clean output text for LLM consumption."""
        # Remove ANSI color codes
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        text = ansi_escape.sub('', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove excessive punctuation
        text = re.sub(r'[=]{5,}', '====', text)
        text = re.sub(r'[-]{5,}', '----', text)
        
        return text.strip()
    
    def extract_key_insights(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract key insights for LLM analysis."""
        insights = {
            'session_info': {},
            'test_results': [],
            'performance_metrics': {},
            'failure_patterns': [],
            'marker_usage': {}
        }
        
        # Extract session info
        for entry in entries:
            if entry.get('event_type') == 'session_end':
                insights['session_info'] = {
                    'summary': entry.get('summary', {}),
                    'duration': entry.get('duration', 0.0),
                    'timestamp': entry.get('timestamp', '')
                }
                break
        
        # Extract test results
        for entry in entries:
            if entry.get('event_type') == 'test_result':
                insights['test_results'].append({
                    'test_path': entry.get('test_path', ''),
                    'status': entry.get('status', ''),
                    'duration': entry.get('duration', 0.0),
                    'markers': entry.get('metadata', {}).get('markers', []),
                    'failure_reason': entry.get('failure_reason', '') if entry.get('status') == 'FAILED' else ''
                })
        
        # Calculate performance metrics
        if insights['test_results']:
            durations = [t['duration'] for t in insights['test_results']]
            insights['performance_metrics'] = {
                'avg_duration': sum(durations) / len(durations),
                'max_duration': max(durations),
                'min_duration': min(durations),
                'total_tests': len(insights['test_results'])
            }
        
        # Extract failure patterns
        failed_tests = [t for t in insights['test_results'] if t['status'] == 'FAILED']
        insights['failure_patterns'] = [
            {
                'test_path': t['test_path'],
                'failure_reason': t['failure_reason'][:500]  # Truncate for LLM
            }
            for t in failed_tests
        ]
        
        # Extract marker usage
        marker_counts = {}
        for test in insights['test_results']:
            for marker in test['markers']:
                if marker not in marker_counts:
                    marker_counts[marker] = 0
                marker_counts[marker] += 1
        insights['marker_usage'] = marker_counts
        
        return insights