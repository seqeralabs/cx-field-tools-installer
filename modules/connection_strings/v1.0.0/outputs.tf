## ------------------------------------------------------------------------------------
## Tower Core Outputs
## ------------------------------------------------------------------------------------
output "tower_base_url" {
  description = "The base URL for Tower"
  value       = local.tower_base_url
}

output "tower_server_url" {
  description = "The server URL for Tower with appropriate protocol and port"
  value       = local.tower_server_url
}

output "tower_api_endpoint" {
  description = "The API endpoint URL for Tower"
  value       = local.tower_api_endpoint
}

output "tower_db_root" {
  description = "The root database connection for Tower"
  value       = local.tower_db_root
  sensitive   = false
}

output "tower_db_url" {
  description = "The complete database URL for Tower including database name and connection string"
  value       = local.tower_db_url
  sensitive   = false
}

output "tower_redis_url" {
  description = "The Redis URL for Tower"
  value       = local.tower_redis_url
  sensitive   = false
}

## ------------------------------------------------------------------------------------
## Groundswell Outputs
## ------------------------------------------------------------------------------------
output "swell_db_url" {
  description = "The complete database URL for Groundswell"
  value       = local.swell_db_url
  sensitive   = false
}

## ------------------------------------------------------------------------------------
## Connect (Studio) Outputs
## ------------------------------------------------------------------------------------
output "tower_connect_dns" {
  description = "The DNS name for Connect"
  value       = local.tower_connect_dns
}

output "tower_connect_wildcard_dns" {
  description = "The wildcard DNS pattern for Connect host-matching in ALB"
  value       = local.tower_connect_wildcard_dns
}

output "tower_connect_server_url" {
  description = "The server URL for Connect with appropriate protocol and port"
  value       = local.tower_connect_server_url
}

output "tower_connect_redis_dns" {
  description = "The Redis DNS for Connect"
  value       = local.tower_connect_redis_dns
  sensitive   = false
}

output "tower_connect_redis_url" {
  description = "The Redis URL for Connect"
  value       = local.tower_connect_redis_url
  sensitive   = false
}

## ------------------------------------------------------------------------------------
## Wave-Lite Outputs
## ------------------------------------------------------------------------------------
output "tower_wave_url" {
  description = "The URL for Wave or Wave-Lite depending on configuration"
  value       = local.tower_wave_url
}

output "tower_wave_dns" {
  description = "The DNS name for Wave without protocol prefix"
  value       = local.tower_wave_dns
}

output "wave_lite_db_dns" {
  description = "The database DNS for Wave-Lite"
  value       = local.wave_lite_db_dns
  sensitive   = false
}
output "wave_lite_db_url" {
  description = "The database URL for Wave-Lite"
  value       = local.wave_lite_db_url
  sensitive   = false
}

output "wave_lite_redis_dns" {
  description = "The Redis DNS for Wave-Lite"
  value       = local.wave_lite_redis_dns
  sensitive   = false
}
output "wave_lite_redis_url" {
  description = "The Redis URL for Wave-Lite"
  value       = local.wave_lite_redis_url
  sensitive   = false
}
