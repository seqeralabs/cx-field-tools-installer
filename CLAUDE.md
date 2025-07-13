# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Terraform-based installer for Seqera Platform Enterprise (Docker-Compose deployment) that simplifies infrastructure provisioning and application configuration. The project is designed for non-Terraform experts and prioritizes simplicity over standard Terraform conventions.

## Architecture

The project follows a **sequential file naming convention** (000-012) to model the DAG execution flow:
- `000_main.tf` - Provider configuration and backend setup
- `001_vpc.tf` - VPC and networking infrastructure
- `002_security_groups.tf` - Security group definitions
- `003_database.tf` - Database resources (RDS or containerized)
- `004_iam.tf` - IAM roles and policies
- `005_parameter_store.tf` - AWS SSM Parameter Store management
- `006_ec2.tf` - EC2 instances and compute resources
- `007_load_balancer.tf` - Application Load Balancer setup
- `008_route53.tf` - DNS configuration
- `009_define_file_templates.tf` - Template file definitions
- `010_prepare_config_files.tf` - Configuration file generation
- `011_configure_vm.tf` - VM configuration via Ansible
- `012_outputs.tf` - Output values

### Key Design Principles
1. **Security-first**: Sensitive values stored in AWS SSM Parameter Store
2. **Repeatability**: Consistent outputs for same inputs
3. **Simplicity**: Files named for non-Terraform experts
4. **Template-based**: Uses `templatefile()` functions over in-resource definitions
5. **Regeneration**: All assets regenerated on every `terraform apply`

## Commands

### Development Commands
```bash
# Initialize Terraform
terraform init

# Plan with validation (recommended)
make plan

# Apply with validation (recommended)
make apply

# Destroy infrastructure
terraform destroy  # Note: destroys all data including databases

# Validation only
make verify

# Full validation with security scan
make verify-full
```

### Testing Commands
```bash
# Run all tests
./tests/run_tests.sh

# Run unit tests only
pytest tests/unit/test_module_connection_strings/ -v -s -x

# Run plan-based tests only
make test_plan_only

# Generate test data
make generate_test_data

# Generate JSON plan for testing
make generate_json_plan
```

### Python Development
```bash
# Run Python validation script
python3 scripts/installer/validation/check_configuration.py

# Format Python files (required after any Python modifications)
black <filename>.py

# Run pytest with specific markers
pytest -m "local" -v
pytest -m "db" -v
pytest -m "redis" -v
```

### Testing with Structured Logging
```bash
# View structured test results
python tests/utils/log_parser.py summarize

# Extract failed tests for LLM analysis
python tests/utils/log_parser.py extract-failures

# View pytest logs for debugging
tail -f tests/logs/pytest_structured.log

# Parse logs for LLM analysis
python tests/utils/log_parser.py llm-format --recent 100

# Validate log format
python tests/utils/log_parser.py validate

# Export logs as JSON for programmatic analysis
python tests/utils/log_parser.py export-json
```

## Project Structure

### Core Infrastructure (`*.tf` files)
Sequential numbered files defining infrastructure resources in dependency order.

### Python Scripts (`scripts/`)
- `scripts/installer/validation/` - Configuration validation
- `scripts/installer/data_external/` - External data providers
- `scripts/installer/utils/` - Utility functions (extractors, logging, subnets)

### Modules (`modules/`)
- `connection_strings/` - Database connection string generation
- `elasticache/` - Redis/ElastiCache configuration
- `subnet_collector/` - Subnet discovery utilities

### Assets (`assets/`)
- `assets/src/` - Template files for Ansible, Docker, configuration
- `assets/target/` - Generated configuration files (not in source control)

### Tests (`tests/`)
- `tests/unit/` - Unit tests for modules
- `tests/integration/` - Integration tests for end-to-end workflows
- `tests/datafiles/` - Test data generation
- `tests/logs/` - Structured pytest logs for LLM analysis
- `tests/utils/` - Test utilities including log parsing and formatting
- Pytest markers: `local`, `db`, `db_new`, `db_existing`, `redis`, `urls`, `urls_insecure`, `log_enabled`

## Configuration Files

### Required Files
- `terraform.tfvars` - Main configuration (copy from `templates/TEMPLATE_terraform.tfvars`). Some variables have a logical relationship to that is represented via a header comment `# Only one of these can be true.`, with the related keys existing as a single block without spaces.
- AWS SSM Parameter Store entries for secrets
- SSH key pair for EC2 access

### Template Files
- All templates in `assets/src/` use `.tpl` extension
- Generated files placed in `assets/target/`
- Templates support variable substitution via Terraform `templatefile()` function

## Development Notes

### Python Code Standards
- **Must run `black` formatter after any Python file modifications**
- Uses custom tfvars parser (`installer/utils/extractors.py`)
- Logging configured via `installer/utils/logger.py`
- No `__pycache__` directories created (disabled in pytest.ini)

### Terraform Conventions
- **No default values** in `variables.tf` - all values must be explicitly defined in `terraform.tfvars`
- Uses `null_resource` with `local-exec` provisioners instead of `local_file` resources
- State stored locally by default (`DONTDELETE/terraform.tfstate`)

### Security Considerations
- Sensitive values stored in AWS SSM Parameter Store only
- Uses AWS Instance Connect Endpoint for private subnet access
- Templates contain `.tpl` extension to avoid accidental secret exposure
- Custom certificates supported via `assets/src/customcerts/`

## Troubleshooting

### Common Issues
1. **Python path issues**: Scripts use `sys.path.append()` to add parent directories
2. **SSH connection**: Uses AWS Instance Connect Endpoint with ProxyCommand
3. **Template generation**: Files regenerated on every apply to prevent drift

### Validation
- Configuration validation via `check_configuration.py` before Terraform execution
- Destroy validation via `check_destroy.py` before teardown
- Security scanning available via `tfsec` (use `make verify-full`)

## Testing Strategy

The project uses a hybrid testing approach:
1. **Plan-based tests** - Mock resources using `terraform plan` output
    1. Plan outputs are cached in `tests/.plan_cache` to speed up n+1 test cycles when underlying values are unchanged.
2. **Unit tests** - Test individual modules in isolation
3. **Integration tests** - Full deployment and validation cycle
4. **Local value tests** - Validate computed values and data sources

All tests designed to run without requiring actual AWS resources for basic validation.