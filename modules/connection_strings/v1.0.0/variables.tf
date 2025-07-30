## ------------------------------------------------------------------------------------
## Feature Flags
## ------------------------------------------------------------------------------------
variable "flag_create_load_balancer" {
  description = "Whether to create a load balancer"
  type        = bool
}

variable "flag_do_not_use_https" {
  description = "Whether to disable HTTPS"
  type        = bool
}

variable "flag_create_external_db" {
  description = "Whether to create an external database"
  type        = bool
}

variable "flag_use_existing_external_db" {
  description = "Whether to use an existing external database"
  type        = bool
}

variable "flag_use_container_db" {
  description = "Whether to use a container db."
  type        = bool
}

variable "flag_create_external_redis" {
  description = "Whether to create external Redis"
  type        = bool
}

variable "flag_use_container_redis" {
  description = "Whether to use a Redis."
  type        = bool
}

variable "flag_use_wave" {
  description = "Whether to use Wave"
  type        = bool
}

variable "flag_use_wave_lite" {
  description = "Whether to use Wave"
  type        = bool
}

variable "flag_studio_enable_path_routing" {
  description = "Whether Studio should use favoured subdomain approach or workaround pathing approach."
  type        = bool
  default     = false
}

variable "data_studio_path_routing_url" {
  type        = string
  description = "Domain where Connect Proxy is available."
  default     = ""
}

## ------------------------------------------------------------------------------------
## Tower Core Configuration
## ------------------------------------------------------------------------------------
variable "tower_server_url" {
  description = "The server URL for Tower"
  type        = string
}

variable "tower_db_url" {
  description = "The database URL for Tower when not creating new DB"
  type        = string
}

variable "db_database_name" {
  description = "The name of the Tower database"
  type        = string
}


variable "rds_tower" {
  description = "The rds module object containing Tower RDS configuration"
  type        = any
  default     = null
}

variable "elasticache_tower" {
  description = "The aws_elasticache_cluster.redis object containing Redis cluster configuration"
  type        = any
  default     = null
}

## ------------------------------------------------------------------------------------
## Groundswell Configuration
## ------------------------------------------------------------------------------------
variable "swell_database_name" {
  description = "The name of the Groundswell database"
  type        = string
}

## ------------------------------------------------------------------------------------
## Wave Configuration
## ------------------------------------------------------------------------------------
variable "wave_server_url" {
  description = "The server URL for Wave or Wave-Lite"
  type        = string
}

variable "rds_wave_lite" {
  description = "The rds-wave-lite module object containing RDS configuration"
  type        = any
  default     = null
}

variable "elasticache_wave_lite" {
  description = "The elasticache_wave_lite module object containing Redis configuration"
  type        = any
  default     = null
}


## ------------------------------------------------------------------------------------
## External Resource References
## ------------------------------------------------------------------------------------
# Note: These are referenced in main.tf but should be passed as data/resource references
# from the parent module rather than as variables
# - module.rds[0].db_instance_address
# - aws_elasticache_cluster.redis[0].cache_nodes[0].address
# - aws_elasticache_cluster.redis[0].cache_nodes[0].port
# - module.rds-wave-lite[0].db_instance_address
# - module.elasticache_wave_lite[0].url


## ------------------------------------------------------------------------------------
## Testing
## ------------------------------------------------------------------------------------
variable "use_mocks" {
  type        = bool
  default     = false
  description = "Use to drive mocking behaviour for to-be-created resources."
}
