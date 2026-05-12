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

output "subnet_ids_ec2" {
  description = "List of EC2 subnet IDs"
  value       = local.subnet_ids_ec2
}

output "subnet_ids_batch" {
  description = "List of Batch subnet IDs"
  value       = local.subnet_ids_batch
}

output "subnet_ids_db" {
  description = "List of DB subnet IDs"
  value       = local.subnet_ids_db
}

output "subnet_ids_redis" {
  description = "List of Redis subnet IDs"
  value       = local.subnet_ids_redis
}

output "subnet_ids_alb" {
  description = "List of ALB subnet IDs"
  value       = local.subnet_ids_alb
}
