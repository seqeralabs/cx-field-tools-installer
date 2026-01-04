# Seqerakit Module

Generates and manages Seqerakit configuration files and scripts for Tower/Seqera Platform integration.

## Features

- Generates Seqerakit setup YAML configuration
- Creates AWS Batch compute environment configurations  
- Manages secrets loading from AWS Systems Manager (SSM)
- Supports both Fusion v2 and traditional compute environments
- Handles multiple credential types (AWS, GitHub, Docker, CodeCommit)
- Generates CodeCommit workspace ID scripts

## Usage

```hcl
module "seqerakit" {
  source = "./modules/seqerakit/v1.0.0"

  # Required Configuration
  aws_account = var.aws_account
  aws_region  = var.aws_region
  aws_profile = var.aws_profile
  default_tags = var.default_tags
  app_name = var.app_name

  # Seqerakit Settings
  flag_run_seqerakit = true
  seqerakit_org_name = "my-org"
  seqerakit_org_fullname = "My Organization"
  seqerakit_org_url = "https://my-org.seqera.io"
  seqerakit_team_name = "my-team"
  seqerakit_team_members = "user1@example.com,user2@example.com"
  seqerakit_workspace_name = "my-workspace"
  seqerakit_workspace_fullname = "My Workspace"
  seqerakit_compute_env_name = "my-compute-env"
  seqerakit_compute_env_region = "us-west-2"
  seqerakit_root_bucket = "my-s3-bucket"
  seqerakit_workdir = "/tmp/work"
  seqerakit_outdir = "/tmp/output"

  # AWS Configuration
  seqerakit_aws_use_fusion_v2 = true
  seqerakit_aws_use_forge = true
  seqerakit_aws_use_batch = true
  seqerakit_aws_fusion_instances = "m5.large,m5.xlarge"
  seqerakit_aws_normal_instances = "t3.medium,t3.large"
  seqerakit_aws_manual_head_queue = "head-queue"
  seqerakit_aws_manual_compute_queue = "compute-queue"

  # Credentials Configuration
  seqerakit_flag_credential_create_aws = true
  seqerakit_flag_credential_create_github = true
  seqerakit_flag_credential_create_docker = true
  seqerakit_flag_credential_create_codecommit = true
  seqerakit_flag_credential_use_aws_role = false

  # Infrastructure (optional)
  vpc_id = var.vpc_id
  subnet_ids = var.subnet_ids
  security_group_ids = var.security_group_ids
  ec2_key_pair_name = var.ec2_key_pair_name

  # Secrets
  secrets_bootstrap_seqerakit = "/myapp/seqerakit/secrets"
}
```

## Secrets Management

### Environment Variable Approach
The module uses environment variables instead of hardcoded secrets for security:

```bash
# Load secrets from SSM into environment variables
source helpers/load_seqerakit_secrets.sh

# Run terraform to generate config files
terraform apply
```

### SSM Parameter Structure
Store secrets in SSM as a JSON object:

```json
{
  "TOWER_AWS_USER": {"value": "AKIA..."},
  "TOWER_AWS_PASSWORD": {"value": "secret..."},
  "TOWER_AWS_ROLE": {"value": "arn:aws:iam::..."},
  "TOWER_GITHUB_USER": {"value": "username"},
  "TOWER_GITHUB_TOKEN": {"value": "ghp_..."},
  "TOWER_DOCKER_USER": {"value": "username"},
  "TOWER_DOCKER_TOKEN": {"value": "token..."},
  "TOWER_CODECOMMIT_USER": {"value": "username"},
  "TOWER_CODECOMMIT_PASSWORD": {"value": "password..."},
  "TOWER_CODECOMMIT_REGION": {"value": "us-west-2"}
}
```

### Loading Scripts
```bash
# Auto-detect AWS profile from terraform.tfvars
source helpers/load_seqerakit_secrets.sh

# Specify bootstrap path
source helpers/load_seqerakit_secrets.sh /myapp/seqerakit/config

# Specify both path and profile
source helpers/load_seqerakit_secrets.sh /myapp/seqerakit/config playground
```

## Generated Files

| File | Description |
|------|-------------|
| `setup.yml` | Main Seqerakit configuration |
| `aws_batch_manual.yml` | AWS Batch compute environment |
| `codecommit_set_workspace_id.sh` | CodeCommit workspace setup |
| `load_seqerakit_secrets.sh` | Secrets loading script |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| `aws_account` | AWS account ID | `string` | n/a | yes |
| `aws_region` | AWS region | `string` | n/a | yes |
| `aws_profile` | AWS profile to use | `string` | n/a | yes |
| `default_tags` | Default tags to apply to all resources | `map(string)` | n/a | yes |
| `app_name` | Application name | `string` | n/a | yes |
| `flag_run_seqerakit` | Whether to run Seqerakit setup | `bool` | n/a | yes |
| `seqerakit_org_name` | Seqerakit organization name | `string` | n/a | yes |
| `seqerakit_org_fullname` | Seqerakit organization full name | `string` | n/a | yes |
| `seqerakit_org_url` | Seqerakit organization URL | `string` | n/a | yes |
| `seqerakit_team_name` | Seqerakit team name | `string` | n/a | yes |
| `seqerakit_team_members` | Seqerakit team members (comma-separated) | `string` | n/a | yes |
| `seqerakit_workspace_name` | Seqerakit workspace name | `string` | n/a | yes |
| `seqerakit_workspace_fullname` | Seqerakit workspace full name | `string` | n/a | yes |
| `seqerakit_compute_env_name` | Seqerakit compute environment name | `string` | n/a | yes |
| `seqerakit_compute_env_region` | Seqerakit compute environment region | `string` | n/a | yes |
| `seqerakit_root_bucket` | Seqerakit root S3 bucket | `string` | n/a | yes |
| `seqerakit_workdir` | Seqerakit working directory | `string` | n/a | yes |
| `seqerakit_outdir` | Seqerakit output directory | `string` | n/a | yes |
| `seqerakit_aws_use_fusion_v2` | Whether to use Fusion v2 for Seqerakit | `bool` | n/a | yes |
| `seqerakit_aws_use_forge` | Whether to use Forge for Seqerakit | `bool` | n/a | yes |
| `seqerakit_aws_use_batch` | Whether to use AWS Batch for Seqerakit | `bool` | n/a | yes |
| `seqerakit_aws_fusion_instances` | Fusion instance types for Seqerakit | `string` | n/a | yes |
| `seqerakit_aws_normal_instances` | Normal instance types for Seqerakit | `string` | n/a | yes |
| `seqerakit_aws_manual_head_queue` | Manual head queue for Seqerakit | `string` | n/a | yes |
| `seqerakit_aws_manual_compute_queue` | Manual compute queue for Seqerakit | `string` | n/a | yes |
| `seqerakit_flag_credential_create_aws` | Whether to create AWS credentials for Seqerakit | `bool` | n/a | yes |
| `seqerakit_flag_credential_create_github` | Whether to create GitHub credentials for Seqerakit | `bool` | n/a | yes |
| `seqerakit_flag_credential_create_docker` | Whether to create Docker credentials for Seqerakit | `bool` | n/a | yes |
| `seqerakit_flag_credential_create_codecommit` | Whether to create CodeCommit credentials for Seqerakit | `bool` | n/a | yes |
| `seqerakit_flag_credential_use_aws_role` | Whether to use AWS role for Seqerakit credentials | `bool` | n/a | yes |
| `vpc_id` | VPC ID for compute environment | `string` | `""` | no |
| `subnet_ids` | Subnet IDs for compute environment | `list(string)` | `[]` | no |
| `security_group_ids` | Security group IDs for compute environment | `list(string)` | `[]` | no |
| `ec2_key_pair_name` | EC2 Key pair name for compute environment | `string` | `""` | no |
| `secrets_bootstrap_seqerakit` | SSM SecureString parameter name for Seqerakit secrets | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| `seqerakit_yml` | Generated seqerakit setup YAML content |
| `aws_batch_manual` | Generated AWS Batch manual compute environment YAML |
| `codecommit_script` | Generated CodeCommit workspace ID script |
| `load_secrets_script` | Script to load Seqerakit secrets from SSM into environment variables |
| `generated_files` | Map of generated file paths |
| `seqerakit_secrets` | Seqerakit secrets from SSM (sensitive) |

## Troubleshooting

### Missing Environment Variables
```bash
# Check if secrets are loaded
echo $TOWER_AWS_USER
echo $TOWER_GITHUB_TOKEN

# Verify SSM parameter exists
aws ssm get-parameter --name "/myapp/seqerakit/secrets" --with-decryption
```

### Empty Values
Empty values are normal if certain credentials aren't configured in your bootstrap parameter.

## Requirements

- Terraform >= 1.0
- AWS Provider >= 5.0
- Local Provider >= 2.0

## Version History

- **v1.0.0** - Initial release with consolidated module structure and environment variable secrets