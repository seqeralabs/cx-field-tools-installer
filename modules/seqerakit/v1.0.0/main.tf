## ------------------------------------------------------------------------------------
## Seqerakit Module - Main Configuration
## ------------------------------------------------------------------------------------

## ------------------------------------------------------------------------------------
## Data Sources
## ------------------------------------------------------------------------------------
data "aws_ssm_parameter" "seqerakit_secrets" {
  count = var.secrets_bootstrap_seqerakit != "" ? 1 : 0
  name  = var.secrets_bootstrap_seqerakit
}

## ------------------------------------------------------------------------------------
## Locals
## ------------------------------------------------------------------------------------
locals {
  # Use SSM secrets if available, otherwise use empty values
  seqerakit_secrets = var.secrets_bootstrap_seqerakit != "" ? jsondecode(nonsensitive(data.aws_ssm_parameter.seqerakit_secrets[0].value)) : {
    "TOWER_AWS_USER" = { "value" = "CHANGE_ME" }
    "TOWER_AWS_PASSWORD" = { "value" = "CHANGE_ME" }
    "TOWER_AWS_ROLE" = { "value" = "CHANGE_ME" }
    "TOWER_GITHUB_USER" = { "value" = "CHANGE_ME" }
    "TOWER_GITHUB_TOKEN" = { "value" = "CHANGE_ME" }
    "TOWER_DOCKER_USER" = { "value" = "CHANGE_ME" }
    "TOWER_DOCKER_TOKEN" = { "value" = "CHANGE_ME" }
    "TOWER_CODECOMMIT_USER" = { "value" = "CHANGE_ME" }
    "TOWER_CODECOMMIT_PASSWORD" = { "value" = "CHANGE_ME" }
    "TOWER_CODECOMMIT_REGION" = { "value" = "CHANGE_ME" }
  }

  # Seqerakit - Main Configuration Template
  seqerakit_yml = templatefile("${path.module}/setup.yml.tpl",
    {
      seqerakit_org_name     = var.seqerakit_org_name,
      seqerakit_org_fullname = var.seqerakit_org_fullname,
      seqerakit_org_url      = var.seqerakit_org_url,

      seqerakit_team_name    = var.seqerakit_team_name,
      seqerakit_team_members = replace(var.seqerakit_team_members, "/\\s+/", ""),

      seqerakit_workspace_name     = var.seqerakit_workspace_name,
      seqerakit_workspace_fullname = var.seqerakit_workspace_fullname,

      seqerakit_workdir          = var.seqerakit_workdir,
      seqerakit_outdir           = var.seqerakit_outdir,
      seqerakit_compute_env_name = var.seqerakit_compute_env_name,

      seqerakit_flag_credential_create_aws    = var.seqerakit_flag_credential_create_aws,
      seqerakit_flag_credential_create_github = var.seqerakit_flag_credential_create_github,
      seqerakit_flag_credential_create_docker = var.seqerakit_flag_credential_create_docker,
      seqerakit_flag_credential_create_codecommit = var.seqerakit_flag_credential_create_codecommit,

      seqerakit_flag_credential_use_aws_role = var.seqerakit_flag_credential_use_aws_role

      # Environment variable names for secrets (values sourced from SSM)
      aws_access_key_env_var = "$TOWER_AWS_USER"
      aws_secret_key_env_var = "$TOWER_AWS_PASSWORD"
      aws_role_arn_env_var   = "$TOWER_AWS_ROLE"
      github_username_env_var = "$TOWER_GITHUB_USER"
      github_token_env_var   = "$TOWER_GITHUB_TOKEN"
      docker_username_env_var = "$TOWER_DOCKER_USER"
      docker_password_env_var = "$TOWER_DOCKER_TOKEN"

      # Compute environment variables
      seqerakit_aws_use_forge = var.seqerakit_aws_use_forge,
      aws_region = var.seqerakit_compute_env_region,
      vpc_id = var.vpc_id,
      subnets = length(var.subnet_ids) > 0 ? join(",", var.subnet_ids) : "",
      securityGroups = length(var.security_group_ids) > 0 ? join(",", var.security_group_ids) : "",
      ec2KeyPair = var.ec2_key_pair_name,

      use_fusion_v2    = var.seqerakit_aws_use_fusion_v2 == true ? "True" : "False",
      use_wave         = var.seqerakit_aws_use_fusion_v2 == true ? "True" : "False",
      use_fast_storage = var.seqerakit_aws_use_fusion_v2 == true ? "True" : "False",

      instance_types = (
        var.seqerakit_aws_use_fusion_v2 == true ?
        replace(var.seqerakit_aws_fusion_instances, "/\\s+/", "") :
        replace(var.seqerakit_aws_normal_instances, "/\\s+/", "")
      )
    }
  )

  # Seqerakit - AWS Batch Manual Compute Environment Template
  aws_batch_manual = templatefile("${path.module}/compute-envs/aws_batch_manual.yml.tpl",
    {
      aws_region = var.seqerakit_compute_env_region,

      seqerakit_org_name         = var.seqerakit_org_name,
      seqerakit_workspace_name   = var.seqerakit_workspace_name,
      seqerakit_workdir          = var.seqerakit_workdir,
      seqerakit_compute_env_name = var.seqerakit_compute_env_name,

      seqerakit_aws_manual_head_queue    = var.seqerakit_aws_manual_head_queue,
      seqerakit_aws_manual_compute_queue = var.seqerakit_aws_manual_compute_queue,

      use_fusion_v2    = var.seqerakit_aws_use_fusion_v2 == true ? "True" : "False",
      use_wave         = var.seqerakit_aws_use_fusion_v2 == true ? "True" : "False",
      use_fast_storage = var.seqerakit_aws_use_fusion_v2 == true ? "True" : "False"
    }
  )

  # Seqerakit - CodeCommit Workspace ID Script Template
  codecommit_seqerakit = templatefile("${path.module}/helpers/codecommit_set_workspace_id.sh.tpl",
    {
      seqerakit_org_name = var.seqerakit_org_name,
      seqerakit_workspace_name = var.seqerakit_workspace_name
    }
  )
}

## ------------------------------------------------------------------------------------
## Resources
## ------------------------------------------------------------------------------------
resource "local_file" "seqerakit_yml" {
  content  = local.seqerakit_yml
  filename = "${path.module}/generated/setup.yml"
}

resource "local_file" "aws_batch_manual_yml" {
  content  = local.aws_batch_manual
  filename = "${path.module}/generated/aws_batch_manual.yml"
}

resource "local_file" "codecommit_script" {
  content  = local.codecommit_seqerakit
  filename = "${path.module}/generated/codecommit_set_workspace_id.sh"
}

# Copy the secrets loading script
resource "local_file" "load_secrets_script" {
  source   = "${path.module}/helpers/load_seqerakit_secrets.sh"
  filename = "${path.module}/generated/load_seqerakit_secrets.sh"
}

# Make scripts executable
resource "null_resource" "make_scripts_executable" {
  depends_on = [local_file.codecommit_script, local_file.load_secrets_script]
  
  provisioner "local-exec" {
    command = "chmod +x ${path.module}/generated/codecommit_set_workspace_id.sh ${path.module}/generated/load_seqerakit_secrets.sh"
  }
}
