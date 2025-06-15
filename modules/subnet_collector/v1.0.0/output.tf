output "cidr_to_id_map" {
  description = "Map of subnet CIDR blocks to their IDs"
  value       = local.cidr_to_id_map
}

output "public_subnets" {
  description = "Details of public subnets"
  value       = local.subnet_details.public
}

output "private_subnets" {
  description = "Details of private subnets"
  value       = local.subnet_details.private
} 