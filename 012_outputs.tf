# ----------------------------------------------------------------------------------------------------------------------
# AWS Account Details
# ----------------------------------------------------------------------------------------------------------------------
output "aws_account_id" {
  value = var.local_testing_active ? "N/A" : data.aws_caller_identity.current[0].account_id
}

output "aws_caller_arn" {
  value = var.local_testing_active ? "N/A" : data.aws_caller_identity.current[0].arn
}

output "aws_caller_user" {
  value = var.local_testing_active ? "N/A" : data.aws_caller_identity.current[0].user_id
}


# ----------------------------------------------------------------------------------------------------------------------
# EC2 Keys
# ----------------------------------------------------------------------------------------------------------------------
output "ec2_ssh_key" {
  value     = tls_private_key.ec2_ssh_key.private_key_pem
  sensitive = true
}

# ----------------------------------------------------------------------------------------------------------------------
# Tower Core
# ----------------------------------------------------------------------------------------------------------------------
output "tower_base_url" {
  value = module.connection_strings.tower_base_url
}

output "tower_server_url" {
  value = module.connection_strings.tower_server_url
}

output "tower_api_endpoint" {
  value = module.connection_strings.tower_api_endpoint
}

output "aws_ec2_private_ip" {
  value = var.flag_private_tower_without_eice == true ? aws_instance.ec2.private_ip : "N/A connect via EICE."
}

output "aws_ec2_public_ip" {
  value = var.flag_make_instance_public == true ? aws_eip.towerhost[0].public_ip : "EC2 has no public IP."
}

# output "database_connection_string" {
#   description = "Dynamically generated db connectino string based on tfvars selections."
#   value = data.external.generate_db_connection_string.result.value
# }
output "tower_db_dns" {
  description = "The DB root."
  value       = module.connection_strings.tower_db_dns
}

output "tower_db_url" {
  description = "The complete database URL for Tower including database name and connection string"
  value       = module.connection_strings.tower_db_url
}

output "tower_redis_dns" {
  description = "The Redis DNS for Tower"
  value       = module.connection_strings.tower_redis_dns
}
output "tower_redis_url" {
  description = "The Redis URL for Tower"
  value       = module.connection_strings.tower_redis_url
}

# ----------------------------------------------------------------------------------------------------------------------
# Groundswell
# ----------------------------------------------------------------------------------------------------------------------
output "swell_db_dns" {
  description = "The DNS for Groundswell"
  value       = module.connection_strings.swell_db_dns
}

output "swell_db_url" {
  description = "The complete database URL for Groundswell"
  value       = module.connection_strings.swell_db_url
}

# ----------------------------------------------------------------------------------------------------------------------
# Connect (Studio)
# ----------------------------------------------------------------------------------------------------------------------
output "tower_connect_dns" {
  description = "The DNS name for Connect"
  value       = module.connection_strings.tower_connect_dns
}

output "tower_connect_wildcard_dns" {
  description = "The DNS name for Connect"
  value       = module.connection_strings.tower_connect_wildcard_dns
}

output "tower_connect_server_url" {
  description = "The server URL for Connect with appropriate protocol and port"
  value       = module.connection_strings.tower_connect_server_url
}

output "tower_connect_redis_dns" {
  description = "The DNS for the Redis instance used by Connect."
  value       = module.connection_strings.tower_connect_redis_dns
}

output "tower_connect_redis_url" {
  description = "The URL for the Redis instance used by Connect."
  value       = module.connection_strings.tower_connect_redis_url
}

# ----------------------------------------------------------------------------------------------------------------------
# Wave / Wave Lite
# ----------------------------------------------------------------------------------------------------------------------
output "tower_wave_url" {
  description = "The URL for Wave-Lite"
  value       = module.connection_strings.tower_wave_url
}

output "tower_wave_dns" {
  description = "The DNS name for Wave without protocol prefix"
  value       = module.connection_strings.tower_wave_dns
}

output "wave_lite_db_dns" {
  description = "The database DNS for Wave-Lite"
  value       = module.connection_strings.wave_lite_db_dns
}

output "wave_lite_db_url" {
  description = "The database URL for Wave-Lite"
  value       = module.connection_strings.wave_lite_db_url
}

output "wave_lite_redis_dns" {
  description = "The Redis DNS for Wave-Lite"
  value       = module.connection_strings.wave_lite_redis_dns
}
output "wave_lite_redis_url" {
  description = "The Redis URL for Wave-Lite"
  value       = module.connection_strings.wave_lite_redis_url
}

# ----------------------------------------------------------------------------------------------------------------------
# Route53
# ----------------------------------------------------------------------------------------------------------------------
output "route53_record_status" { value = var.flag_create_hosts_file_entry == true ? "Hosts file only. No R53 record." : "R53 record created." }

