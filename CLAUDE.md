# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Path Prefixes
References in the table below use these prefixes:

- `proj:` → `<repo>/.claude/guidelines/`

## Important Reminders - LOAD BEFORE EVERY TASK
- Identify task type(s) and load applicable resources per the table below.

| Task Type | Required |
|-----------|----------|
| ALWAYS DO FOR ALL TASKS | `proj:variable_default_values.md` |
| Any PR that changes deployer-visible behaviour (variables, component config, components added/removed) | `proj:changelog_protocol.md` |
| Writing or editing Terraform (`*.tf`, `terraform.tfvars`) | `proj:terraform_conventions.md`, `proj:terraform_style_guide.md` |
| Writing or editing Python | `proj:python_standards.md` |
| Running, writing, or analysing tests | `proj:testing_strategy.md`, `proj:testing_commands.md` |
| Working on security-sensitive code (secrets, IAM, SSM, certificates) | `proj:security_considerations.md` |

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

For test commands and structured-logging tooling, see [`proj:testing_commands.md`](.claude/guidelines/testing_commands.md).

## Project Structure

### Core Infrastructure (`*.tf` files)
Sequential numbered files defining infrastructure resources in (rough) dependency order.

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
- Pytest markers are defined in [`tests/pytest.ini`](tests/pytest.ini).

## Configuration Files

### Required Files
- `terraform.tfvars` - Main configuration (copy from `templates/TEMPLATE_terraform.tfvars`). Some variables have a logical relationship to that is represented via a header comment `# Only one of these can be true.`, with the related keys existing as a single block without spaces.
- AWS SSM Parameter Store entries for secrets
- SSH key pair for EC2 access

### Template Files
- All templates in `assets/src/` use `.tpl` extension
- Generated files placed in `assets/target/`
- Templates support variable substitution via Terraform `templatefile()` function

## Troubleshooting

### Common Issues
1. **Python path issues**: Scripts use `sys.path.append()` to add parent directories
2. **SSH connection**: Uses AWS Instance Connect Endpoint with ProxyCommand
3. **Template generation**: Files regenerated on every apply to prevent drift

### Validation
- Configuration validation via `check_configuration.py` before Terraform execution
- Destroy validation via `check_destroy.py` before teardown
- Security scanning available via `tfsec` (use `make verify-full`)
