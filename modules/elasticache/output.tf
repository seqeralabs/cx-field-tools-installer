# output "url" {
#   value = (
#     var.elasticache_instance.clustered.multi_az_enabled == true ?
#       "${aws_elasticache_replication_group.clustered[0].configuration_endpoint_address}:${aws_elasticache_replication_group.clustered[0].port}" :
#       "${aws_elasticache_replication_group.singleton[0].primary_endpoint_address}:${aws_elasticache_replication_group.singleton[0].port}"
#   )
#   description = "Address of the Elasticache instance / cluster."
# }

# MultiAz nodes expose a different endpoint. Check whether nodes is clustered or not and then output proper endpoint.
output "dns" {
  value = (
    var.elasticache_instance.clustered.multi_az_enabled == true ?
    "${aws_elasticache_replication_group.redis.configuration_endpoint_address}" :
    "${aws_elasticache_replication_group.redis.primary_endpoint_address}"
  )
  description = "DNS of the Elasticache instance / cluster."
}

output "url" {
  value = (
    var.elasticache_instance.clustered.multi_az_enabled == true ?
    "${aws_elasticache_replication_group.redis.configuration_endpoint_address}:${aws_elasticache_replication_group.redis.port}" :
    "${aws_elasticache_replication_group.redis.primary_endpoint_address}:${aws_elasticache_replication_group.redis.port}"
  )
  description = "DNS & Port of the Elasticache instance / cluster."
}

output "transit_encryption_enabled" {
  value       = var.elasticache_instance.encryption.transit_encryption_enabled
  description = "Identifies if instance has transit encryption enabled."
}
