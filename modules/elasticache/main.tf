locals {

  subnet_ids = (
    length(var.elasticache_instance.subnet_ids) > 0 ?
    var.elasticache_instance.subnet_ids : var.default_vpc_subnets
  )

  # Had to run for expression to get around type mismatch (list vs tuple)
  security_group_ids = (
    length(var.elasticache_instance.security_group_ids) > 0 ?
    var.elasticache_instance.security_group_ids : [for k in var.default_security_group_ids : k]
  )
}

resource "aws_elasticache_subnet_group" "redis" {

  name       = var.resource_prefix
  subnet_ids = local.subnet_ids
}


# Replication group
# https://skundunotes.com/2023/10/21/create-an-amazon-elasticache-for-redis-cluster-using-terraform/
resource "aws_elasticache_replication_group" "redis" {

  # expected length of replication_group_id to be in the range (1 - 40)
  replication_group_id = substr("${var.resource_prefix}-replication", 0, 40)

  apply_immediately = var.elasticache_instance.apply_immediately
  engine            = var.elasticache_instance.engine
  engine_version    = var.elasticache_instance.engine_version
  node_type         = var.elasticache_instance.node_type
  port              = var.elasticache_instance.port

  subnet_group_name  = aws_elasticache_subnet_group.redis.name
  security_group_ids = local.security_group_ids

  # If clustered desired, this value must be null. Else non-zero positive integer.
  num_cache_clusters = try(var.elasticache_instance.unclustered.num_cache_nodes, null)

  # If clustered desired, these values must be true / positive integers.
  automatic_failover_enabled = var.elasticache_instance.clustered.automatic_failover_enabled
  multi_az_enabled           = var.elasticache_instance.clustered.multi_az_enabled
  num_node_groups            = var.elasticache_instance.clustered.num_node_groups
  replicas_per_node_group    = var.elasticache_instance.clustered.replicas_per_node_group

  description          = var.resource_prefix
  parameter_group_name = var.elasticache_instance.clustered.parameter_group_name

  # If encryption in transit true, auth_token must be set (sync with secret in SSM).
  # IF encryption at rest set, kms_key_id must be populate to use custom KMS key or left null to use AWS-managed key.
  at_rest_encryption_enabled = var.elasticache_instance.encryption.at_rest_encryption_enabled
  transit_encryption_enabled = var.elasticache_instance.encryption.transit_encryption_enabled
  auth_token                 = try(var.redis_password, null)
  kms_key_id                 = try(var.elasticache_instance.encryption.kms_key_id, null)

  # log_delivery_configuration {
  #   destination = TODO
  #   destination_type = TODO
  #   log_format = TODO
  #   log_type = TODO
  # }

  # lifecycle {
  #   ignore_changes = [ kms_key_id ]
  # }
}
