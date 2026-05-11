## ------------------------------------------------------------------------------------
## Tower Core Outputs
## ------------------------------------------------------------------------------------
output "tower_base_url" {
  description = "The base URL for Tower"
  value       = local.composed_tower_base_url
}

output "tower_server_url" {
  description = "The server URL for Tower with appropriate protocol and port"
  value       = local.composed_tower_server_url
}

output "tower_api_endpoint" {
  description = "The API endpoint URL for Tower"
  value       = local.composed_tower_api_endpoint
}

output "tower_db_dns" {
  description = "The root database connection for Tower"
  value       = local.resolved_platform_db_dns
  sensitive   = false
}

output "tower_db_url" {
  description = "The complete database URL for Tower including database name and connection string"
  value       = local.composed_tower_db_url
  sensitive   = false
}

output "platform_connstring" {
  description = "The JDBC connection-string suffix for Tower DB, conditional on engine version (empty for non-MySQL-8 engines)."
  value       = local.resolved_platform_db_connstring
}

output "tower_redis_dns" {
  description = "The Redis DNS for Tower"
  value       = local.resolved_platform_redis_dns
  sensitive   = false
}
output "tower_redis_url" {
  description = "The Redis URL for Tower"
  value       = local.composed_tower_redis_url
  sensitive   = false
}

## ------------------------------------------------------------------------------------
## Groundswell Outputs
## ------------------------------------------------------------------------------------
output "swell_db_dns" {
  description = "The DNS for Groundswell"
  value       = local.composed_swell_db_dns
  sensitive   = false
}
output "swell_db_url" {
  description = "The complete database URL for Groundswell"
  value       = local.composed_swell_db_url
  sensitive   = false
}

## ------------------------------------------------------------------------------------
## Connect (Studio) Outputs
## ------------------------------------------------------------------------------------
output "tower_connect_dns" {
  description = "The DNS name for Connect"
  value       = local.composed_tower_connect_dns
}

output "tower_connect_wildcard_dns" {
  description = "The wildcard DNS pattern for Connect host-matching in ALB"
  value       = local.composed_tower_connect_wildcard_dns
}

output "tower_connect_server_url" {
  description = "The server URL for Connect with appropriate protocol and port"
  value       = local.composed_tower_connect_server_url
}

output "tower_connect_redis_dns" {
  description = "The Redis DNS for Connect (shares Platform Redis; N/A when studios disabled)"
  value       = local.composed_tower_connect_redis_dns
  sensitive   = false
}

output "tower_connect_redis_url" {
  description = "The Redis URL for Connect (no scheme prefix; Studios prepends its own)"
  value       = local.composed_tower_connect_redis_url
  sensitive   = false
}

output "tower_connect_ssh_dns" {
  description = "The DNS name for Connect SSH (without protocol prefix)"
  value       = local.composed_tower_connect_ssh_dns
}

output "tower_connect_ssh_url" {
  description = "The URL for Connect SSH with protocol prefix"
  value       = local.composed_tower_connect_ssh_url
}

## ------------------------------------------------------------------------------------
## Wave / Wave-Lite Outputs
## ------------------------------------------------------------------------------------
output "tower_wave_url" {
  description = "The URL for Wave or Wave-Lite depending on configuration"
  value       = local.composed_tower_wave_url
}

output "tower_wave_dns" {
  description = "The DNS name for Wave without protocol prefix"
  value       = local.composed_tower_wave_dns
}

output "wave_lite_db_dns" {
  description = "The database DNS for Wave-Lite (N/A when wave_mode != 'wave-lite')"
  value       = local.composed_wave_lite_db_dns
  sensitive   = false
}
output "wave_lite_db_url" {
  description = "The database URL for Wave-Lite"
  value       = local.composed_wave_lite_db_url
  sensitive   = false
}

output "wave_lite_redis_dns" {
  description = "The Redis DNS for Wave-Lite (N/A when wave_mode != 'wave-lite')"
  value       = local.composed_wave_lite_redis_dns
  sensitive   = false
}
output "wave_lite_redis_url" {
  description = "The Redis URL for Wave-Lite"
  value       = local.composed_wave_lite_redis_url
  sensitive   = false
}
