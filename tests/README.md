# Testing
Testing framework implement via Python and Bash (_leveraging native Terraform capabilites_). TBD if native Terraform testing capabilities will be used.


## Necessary packages for testing
- pip install pytest
- pip install pyyaml


## Local Testing (Plan-Only)


## Minimal Deployment Testing (Targeted Apply)


## Full Deployment Testing

## Structured Logging for LLM Analysis

The testing framework includes comprehensive structured logging that captures pytest execution data in JSON Lines format, making it accessible to LLM Agent-type tooling for analysis, debugging, and automated insights.

### Log File Locations

- **Main log file**: `tests/logs/pytest_structured.log`
- **Log format**: JSON Lines (one JSON object per line)
- **Automatic logging**: Enabled by default for all pytest runs

### Log Format

Each log entry contains:
- **timestamp**: ISO 8601 UTC timestamp
- **test_session_id**: UUID identifying the pytest session
- **event_type**: Type of event (session_start, session_end, test_start, test_end, test_result)
- **test_path**: Full test path (e.g., `tests/unit/test_example.py::test_function`)
- **status**: Test outcome (PASSED, FAILED, SKIPPED, ERROR)
- **duration**: Execution time in seconds
- **metadata**: Test markers, fixtures, and parametrization info
- **failure_reason**: Detailed error information for failed tests

### Analyzing Test Patterns

Use the log parsing utilities to extract insights:

```bash
# View human-readable test summary
python tests/utils/log_parser.py summarize

# Extract failed tests with failure reasons
python tests/utils/log_parser.py extract-failures

# Get LLM-friendly formatted output
python tests/utils/log_parser.py llm-format --recent 100

# Validate log file format
python tests/utils/log_parser.py validate

# Export structured data as JSON
python tests/utils/log_parser.py export-json
```

### LLM Integration Examples

The structured logs enable LLM tools to:
- Identify patterns in test failures
- Analyze performance bottlenecks
- Suggest optimizations based on test execution data
- Generate reports on test coverage and reliability
- Provide debugging assistance for failing tests

Example LLM queries:
- "Which tests are failing most frequently?"
- "What are the performance characteristics of database tests?"
- "Are there patterns in the failure reasons?"
- "Which test markers have the highest failure rates?"

### Environment Variables

- `PYTEST_STRUCTURED_LOGGING`: Enable/disable logging (`true`/`false`, default: `true`)
- `PYTEST_LOG_FILE`: Override default log file path

### Log Management

- **Rotation**: Logs append to existing files; implement rotation as needed
- **Size**: Monitor log file size to prevent disk space issues
- **Retention**: Archive old logs for historical analysis
- **Privacy**: Ensure no sensitive data is logged in test output