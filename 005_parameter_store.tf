# ------------------------------------------------
# Get Omnibuse SSM Secrets
# Handled by locals in in main.tf 
# ------------------------------------------------
data "aws_ssm_parameter" "tower_secrets" {
  name = var.secrets_bootstrap_tower
}


data "aws_ssm_parameter" "seqerakit_secrets" {
  name = var.secrets_bootstrap_seqerakit
}


data "aws_ssm_parameter" "groundswell_secrets" {
  name = var.secrets_bootstrap_groundswell
}


# ------------------------------------------------
# Generate individual SSM Parameters
# ------------------------------------------------
resource "aws_ssm_parameter" "client_supplied_secrets_tower" {
  for_each = local.tower_secret_keys
  name     = nonsensitive(local.tower_secrets[each.key]["ssm_key"])
  value    = local.tower_secrets[each.key]["value"]
  type     = "SecureString"
  overwrite           = var.flag_overwrite_ssm_keys
}


resource "aws_ssm_parameter" "client_supplied_secrets_seqerakit" {
  # for_each            = local.seqerakit_secret_keys

  for_each = var.flag_run_seqerakit == true ? local.seqerakit_secret_keys : []
  name     = nonsensitive(local.seqerakit_secrets[each.key]["ssm_key"])
  value    = local.seqerakit_secrets[each.key]["value"]
  type     = "SecureString"
  overwrite           = var.flag_overwrite_ssm_keys
}


resource "aws_ssm_parameter" "client_supplied_secrets_groundswell" {

  # count               = var.flag_enable_groundswell == true ? 1 : 0
  # for_each            = local.groundswell_secret_keys

  for_each = var.flag_enable_groundswell == true ? local.groundswell_secret_keys : []
  name     = nonsensitive(local.groundswell_secrets[each.key]["ssm_key"])
  value    = local.groundswell_secrets[each.key]["value"]
  type     = "SecureString"
  overwrite           = var.flag_overwrite_ssm_keys
}