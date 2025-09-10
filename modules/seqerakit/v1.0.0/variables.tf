## ------------------------------------------------------------------------------------
## AWS Configuration
## ------------------------------------------------------------------------------------
variable "aws_account" {
  description = "AWS account ID"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "aws_profile" {
  description = "AWS profile to use"
  type        = string
}

## ------------------------------------------------------------------------------------
## Tags
## ------------------------------------------------------------------------------------
variable "default_tags" {
  description = "Default tags to apply to all resources"
  type        = map(string)
}

## ------------------------------------------------------------------------------------
## App Configuration
## ------------------------------------------------------------------------------------
variable "app_name" {
  description = "Application name"
  type        = string
}

## ------------------------------------------------------------------------------------
## Seqerakit Configuration
## ------------------------------------------------------------------------------------
variable "flag_run_seqerakit" {
  description = "Whether to run Seqerakit setup"
  type        = bool
}

variable "seqerakit_org_name" {
  description = "Seqerakit organization name"
  type        = string
}

variable "seqerakit_org_fullname" {
  description = "Seqerakit organization full name"
  type        = string
}

variable "seqerakit_org_url" {
  description = "Seqerakit organization URL"
  type        = string
}

variable "seqerakit_team_name" {
  description = "Seqerakit team name"
  type        = string
}

variable "seqerakit_team_members" {
  description = "Seqerakit team members (comma-separated)"
  type        = string
}

variable "seqerakit_workspace_name" {
  description = "Seqerakit workspace name"
  type        = string
}

variable "seqerakit_workspace_fullname" {
  description = "Seqerakit workspace full name"
  type        = string
}

variable "seqerakit_compute_env_name" {
  description = "Seqerakit compute environment name"
  type        = string
}

variable "seqerakit_compute_env_region" {
  description = "Seqerakit compute environment region"
  type        = string
}

variable "seqerakit_root_bucket" {
  description = "Seqerakit root S3 bucket"
  type        = string
}

variable "seqerakit_workdir" {
  description = "Seqerakit working directory"
  type        = string
}

variable "seqerakit_outdir" {
  description = "Seqerakit output directory"
  type        = string
}

## ------------------------------------------------------------------------------------
## Seqerakit AWS Configuration
## ------------------------------------------------------------------------------------
variable "seqerakit_aws_use_fusion_v2" {
  description = "Whether to use Fusion v2 for Seqerakit"
  type        = bool
}

variable "seqerakit_aws_use_forge" {
  description = "Whether to use Forge for Seqerakit"
  type        = bool
}

variable "seqerakit_aws_use_batch" {
  description = "Whether to use AWS Batch for Seqerakit"
  type        = bool
}

variable "seqerakit_aws_fusion_instances" {
  description = "Fusion instance types for Seqerakit"
  type        = string
}

variable "seqerakit_aws_normal_instances" {
  description = "Normal instance types for Seqerakit"
  type        = string
}

variable "seqerakit_aws_manual_head_queue" {
  description = "Manual head queue for Seqerakit"
  type        = string
}

variable "seqerakit_aws_manual_compute_queue" {
  description = "Manual compute queue for Seqerakit"
  type        = string
}

## ------------------------------------------------------------------------------------
## Seqerakit Credentials Configuration
## ------------------------------------------------------------------------------------
variable "seqerakit_flag_credential_create_aws" {
  description = "Whether to create AWS credentials for Seqerakit"
  type        = bool
}

variable "seqerakit_flag_credential_create_github" {
  description = "Whether to create GitHub credentials for Seqerakit"
  type        = bool
}

variable "seqerakit_flag_credential_create_docker" {
  description = "Whether to create Docker credentials for Seqerakit"
  type        = bool
}

variable "seqerakit_flag_credential_create_codecommit" {
  description = "Whether to create CodeCommit credentials for Seqerakit"
  type        = bool
}

variable "seqerakit_flag_credential_use_aws_role" {
  description = "Whether to use AWS role for Seqerakit credentials"
  type        = bool
}

## ------------------------------------------------------------------------------------
## Infrastructure Dependencies
## ------------------------------------------------------------------------------------
variable "vpc_id" {
  description = "VPC ID for compute environment"
  type        = string
  default     = ""
}

variable "subnet_ids" {
  description = "Subnet IDs for compute environment"
  type        = list(string)
  default     = []
}

variable "security_group_ids" {
  description = "Security group IDs for compute environment"
  type        = list(string)
  default     = []
}

variable "ec2_key_pair_name" {
  description = "EC2 Key pair name for compute environment"
  type        = string
  default     = ""
}

## ------------------------------------------------------------------------------------
## Secrets Configuration
## ------------------------------------------------------------------------------------
variable "secrets_bootstrap_seqerakit" {
  description = "SSM SecureString parameter name for Seqerakit secrets"
  type        = string
}
