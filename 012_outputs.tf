output "aws_account_id" { value = data.aws_caller_identity.current.account_id }
output "aws_caller_arn" { value = data.aws_caller_identity.current.arn }
output "aws_caller_user" { value = data.aws_caller_identity.current.user_id }

output "ec2_ssh_key" {
  value     = tls_private_key.ec2_ssh_key.private_key_pem
  sensitive = true
}

output "tower_server_url" { value = "https://${var.tower_server_url}" }
output "route53_record_status" { value = var.flag_create_hosts_file_entry == true ? "Hosts file only. No R53 record." : "R53 record created." }
output "aws_ec2_private_ip" { value = var.flag_private_tower_without_eice == true ? aws_instance.ec2.private_ip : "N/A connect via EICE." }
output "aws_ec2_public_ip" { value = var.flag_make_instance_public == true ? aws_eip.towerhost[0].public_ip : "EC2 has no public IP." }

# Outputs for SEQERAKIT
output "tower_api_endpoint" { value = local.tower_api_endpoint }
output "seqera_configuration" { value = "${path.module}/assets/target/seqerakit/setup.yml" }

output "redis_endpoint" {
  value = (
    var.flag_create_external_redis == true ?
    "redis://${aws_elasticache_cluster.redis[0].cache_nodes[0].address}:${aws_elasticache_cluster.redis[0].cache_nodes[0].port}" :
    "Using container redis."
  )
}