## ------------------------------------------------------------------------------------
## Write local values to output for testing purposes
## Keep name of local the same; prefix with 'local_' for easy conversion
## ------------------------------------------------------------------------------------
terraform {
  required_version = ">= 1.7.0"
}

output "local_wave_enabled" {
  value = local.wave_enabled
}
