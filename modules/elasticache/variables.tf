# ELASTICACHE
# -----
variable "resource_prefix" {
  type        = string
  default     = null
  description = "Prefixes created resources."
}

variable "default_vpc_subnets" {
  type        = list(string)
  default     = []
  description = "Default VPC subnets to use if undefined in 'elasticache_instance' object."
}

variable "default_security_group_ids" {
  type        = list(string)
  default     = []
  description = "Default VPC security group ids to use if undefined in 'elasticache_instance' object."
}

variable "redis_password" {
  type        = string
  default     = null
  description = "SSM value for shared Redis password."
}

# Elasticache Cluster
# -----
variable "elasticache_instance" {
  type = object({
    apply_immediately = bool
    engine            = string
    engine_version    = string
    node_type         = string
    port              = number

    security_group_ids = list(string)
    subnet_ids         = list(string)

    unclustered = object({
      num_cache_nodes = number
    })

    clustered = object({
      multi_az_enabled           = bool
      automatic_failover_enabled = bool
      num_node_groups            = number
      replicas_per_node_group    = number
      parameter_group_name       = string
    })

    encryption = object({
      auth_token                 = optional(string)
      at_rest_encryption_enabled = bool
      transit_encryption_enabled = bool
      kms_key_id                 = optional(string)
    })
  })
  # default = {
  #   engine = "redis"
  #   engine_version = "7.0"
  #   apply_immediately = true
  #   node_type = "cache.m4.xlarge"
  #   num_cache_nodes = 1
  #   port = 6379
  #   security_group_ids = []
  #   subnet_ids = []
  #   # enable_replication = false
  #   replication = {
  #       enable = true
  #       automatic_failover_enabled = true
  #       multi_az_enabled = true
  #       num_node_groups = 1
  #       replicas_per_node_group = 2
  #   }
  # }
}
