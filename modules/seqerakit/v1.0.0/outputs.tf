## ------------------------------------------------------------------------------------
## Seqerakit Configuration Outputs
## ------------------------------------------------------------------------------------
output "seqerakit_yml" {
  description = "Generated seqerakit setup YAML content"
  value       = local.seqerakit_yml
}

output "aws_batch_manual" {
  description = "Generated AWS Batch manual compute environment YAML"
  value       = local.aws_batch_manual
}

output "codecommit_script" {
  description = "Generated CodeCommit workspace ID script"
  value       = local.codecommit_seqerakit
}

output "load_secrets_script" {
  description = "Script to load Seqerakit secrets from SSM into environment variables"
  value       = "${path.module}/generated/load_seqerakit_secrets.sh"
}

## ------------------------------------------------------------------------------------
## Generated Files Outputs
## ------------------------------------------------------------------------------------
output "generated_files" {
  description = "Map of generated file paths"
  value = {
    setup_yml                    = local_file.seqerakit_yml.filename
    aws_batch_manual_yml         = local_file.aws_batch_manual_yml.filename
    codecommit_script            = local_file.codecommit_script.filename
    load_secrets_script          = local_file.load_secrets_script.filename
  }
}

## ------------------------------------------------------------------------------------
## Secrets Outputs
## ------------------------------------------------------------------------------------
output "seqerakit_secrets" {
  description = "Seqerakit secrets from SSM (sensitive)"
  value       = local.seqerakit_secrets
  sensitive   = true
}
