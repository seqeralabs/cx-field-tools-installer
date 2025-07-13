#!/usr/bin/env python3
"""
LLM-friendly log parsing utilities for pytest structured logs.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

from tests.utils.log_formatter import PytestLogFormatter


class PytestLogParser:
    """Parser for pytest structured logs with LLM-friendly output."""

    def __init__(self, log_file: Optional[str] = None):
        self.formatter = PytestLogFormatter(log_file)

    def validate_log_format(self) -> bool:
        """Validate log file format and structure."""
        entries = self.formatter.read_log_entries()

        if not entries:
            print("❌ No log entries found")
            return False

        print(f"✅ Found {len(entries)} log entries")

        # Check required fields
        required_fields = ["timestamp", "test_session_id", "event_type"]
        valid_entries = 0

        for entry in entries:
            if all(field in entry for field in required_fields):
                valid_entries += 1

        if valid_entries == len(entries):
            print("✅ All entries have required fields")
        else:
            print(f"⚠️  {len(entries) - valid_entries} entries missing required fields")
            return False

        # Check event types
        # TODO: Validation missing. Maybe extend once enum is implemented?
        event_types = set()
        for entry in entries:
            event_types.add(entry.get("event_type"))
        print(f"✅ Event types found: {sorted(event_types)}")

        # Check for session boundaries
        has_session_start = any(e.get("event_type") == "session_start" for e in entries)
        has_session_end = any(e.get("event_type") == "session_end" for e in entries)

        if has_session_start and has_session_end:
            print("✅ Session boundaries found")
        else:
            print(f"⚠️  Missing session boundaries (start: {has_session_start}, end: {has_session_end})")
            return False

        # return valid_entries > 0
        return True

    def summarize_tests(self, recent: int = 0) -> str:
        """Generate human-readable test summary."""
        entries = self.formatter.read_log_entries(max_entries=recent)
        return self.formatter.format_human_readable(entries)

    def extract_failures(self, include_reasons: bool = True) -> str:
        """Extract failed tests for analysis."""
        entries = self.formatter.read_log_entries()

        if include_reasons:
            return self.formatter.format_failed_tests(entries)
        else:
            failed_tests = []
            for entry in entries:
                if entry.get("event_type") == "test_result" and entry.get("status") == "FAILED":
                    failed_tests.append(entry.get("test_path", "Unknown"))

            return "\n".join(failed_tests) if failed_tests else "No failed tests found."

    def llm_format(self, recent: int = None) -> str:
        """Format logs for LLM consumption."""
        entries = self.formatter.read_log_entries(max_entries=recent)
        insights = self.formatter.extract_key_insights(entries)

        # Format as structured text for LLM analysis
        output = []

        # Session summary
        if insights["session_info"]:
            summary = insights["session_info"].get("summary", {})
            output.append("TEST SESSION SUMMARY:")
            output.append(f"- Total: {summary.get('total', 0)}")
            output.append(f"- Passed: {summary.get('passed', 0)}")
            output.append(f"- Failed: {summary.get('failed', 0)}")
            output.append(f"- Duration: {insights['session_info'].get('duration', 0.0):.2f}s")
            output.append("")

        # Performance insights
        if insights["performance_metrics"]:
            perf = insights["performance_metrics"]
            output.append("PERFORMANCE METRICS:")
            output.append(f"- Average test duration: {perf.get('avg_duration', 0.0):.3f}s")
            output.append(f"- Slowest test: {perf.get('max_duration', 0.0):.3f}s")
            output.append(f"- Fastest test: {perf.get('min_duration', 0.0):.3f}s")
            output.append("")

        # Failure analysis
        if insights["failure_patterns"]:
            output.append("FAILED TESTS:")
            for i, failure in enumerate(insights["failure_patterns"][:5], 1):
                output.append(f"{i}. {failure['test_path']}")
                if failure["failure_reason"]:
                    # Clean failure reason for LLM
                    reason = self.formatter.clean_output_for_llm(failure["failure_reason"])
                    output.append(f"   Error: {reason[:200]}{'...' if len(reason) > 200 else ''}")
            output.append("")

        # Marker usage
        if insights["marker_usage"]:
            output.append("TEST MARKERS:")
            for marker, count in sorted(insights["marker_usage"].items()):
                output.append(f"- {marker}: {count} tests")
            output.append("")

        return "\n".join(output)

    def export_json(self, recent: int = None) -> str:
        """Export log data as JSON for programmatic analysis."""
        entries = self.formatter.read_log_entries(max_entries=recent)
        insights = self.formatter.extract_key_insights(entries)
        return json.dumps(insights, indent=2)

    def llm_test(self) -> str:
        """Test log parsing with sample LLM-style queries."""
        entries = self.formatter.read_log_entries()

        if not entries:
            return "No log entries found for testing."

        # Simulate LLM analysis queries
        queries = [
            "Which tests are failing consistently?",
            "What are the performance bottlenecks?",
            "Which test markers have the highest failure rates?",
            "What are the common failure patterns?",
        ]

        output = ["LLM COMPATIBILITY TEST", "=" * 40, ""]

        for query in queries:
            output.append(f"Query: {query}")

            # Simulate analysis based on the query
            if "failing" in query.lower():
                failures = self.extract_failures(include_reasons=False)
                output.append(f"Answer: {failures}")
            elif "performance" in query.lower():
                perf_data = self.formatter.format_test_performance(entries)
                cleaned = self.formatter.clean_output_for_llm(perf_data)
                output.append(f"Answer: {cleaned[:200]}...")
            elif "markers" in query.lower():
                marker_data = self.formatter.format_marker_summary(entries)
                cleaned = self.formatter.clean_output_for_llm(marker_data)
                output.append(f"Answer: {cleaned[:200]}...")
            else:
                output.append("Answer: Analysis requires specific log data context.")

            output.append("")

        return "\n".join(output)


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Parse pytest structured logs for LLM analysis")

    parser.add_argument(
        "command",
        choices=["validate", "summarize", "extract-failures", "llm-format", "llm-test", "export-json"],
        help="Command to execute",
    )

    parser.add_argument("--log-file", type=str, help="Path to log file (default: tests/logs/pytest_structured.log)")

    parser.add_argument("--recent", type=int, help="Limit to N most recent entries")

    args = parser.parse_args()

    parser_instance = PytestLogParser(args.log_file)

    try:
        if args.command == "validate":
            success = parser_instance.validate_log_format()
            sys.exit(0 if success else 1)

        elif args.command == "summarize":
            print(parser_instance.summarize_tests(args.recent))

        elif args.command == "extract-failures":
            print(parser_instance.extract_failures())

        elif args.command == "llm-format":
            print(parser_instance.llm_format(args.recent))

        elif args.command == "llm-test":
            print(parser_instance.llm_test())

        elif args.command == "export-json":
            print(parser_instance.export_json(args.recent))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
