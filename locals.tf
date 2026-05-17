# ----------------------------------------------------------------------------------------------------------------------
# locals.tf
#
# Locals whose only purpose is to satisfy `terraform console`-based test rendering when the
# referenced resources/data-sources don't exist (mock mode). Each follows the two-layer
# defense pattern documented above the `module "connection_strings"` invocation in 000_main.tf:
#
#   var.use_mocks ? <mock_literal> : try(<production_expression>, <fallback_literal>)
#
# The corresponding `output` block in 012_outputs.tf is a thin passthrough (`value = local.X`),
# which lets `terraform console` evaluate each output during the parallel-precompute pass
# without needing real AWS state. See `tests/utils/terraform/precompute.py`.
#
# Future cleanup: migrate the rest of the project's locals here from `000_main.tf`.
# ----------------------------------------------------------------------------------------------------------------------

locals {
  # AWS caller identity — populated by `data.aws_caller_identity` in production, mocked in tests.
  aws_account_id  = var.use_mocks ? "N/A" : try(data.aws_caller_identity.current[0].account_id, "N/A")
  aws_caller_arn  = var.use_mocks ? "N/A" : try(data.aws_caller_identity.current[0].arn, "N/A")
  aws_caller_user = var.use_mocks ? "N/A" : try(data.aws_caller_identity.current[0].user_id, "N/A")

  # EC2 SSH private key — `tls_private_key.ec2_ssh_key` doesn't exist under console-without-state.
  ec2_ssh_key = var.use_mocks ? "N/A" : try(tls_private_key.ec2_ssh_key.private_key_pem, "N/A")

  # EC2 instance IPs. Outer ternary preserves the production conditional on the deployment-mode flag;
  # inner `try()` neutralises the resource ref when the resource isn't created.
  aws_ec2_private_ip = var.use_mocks ? "192.168.0.1" : (
    var.flag_private_tower_without_eice == true ? try(aws_instance.ec2.private_ip, "192.168.0.1") : "N/A connect via EICE."
  )
  aws_ec2_public_ip = var.use_mocks ? "1.2.3.4" : (
    var.flag_make_instance_public == true ? try(aws_eip.towerhost[0].public_ip, "1.2.3.4") : "EC2 has no public IP."
  )
}
