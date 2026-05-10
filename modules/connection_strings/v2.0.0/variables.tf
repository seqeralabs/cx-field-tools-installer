## ------------------------------------------------------------------------------------
## Feature Flags
## ------------------------------------------------------------------------------------
variable "platform_security_mode" {
  type = string
  # NOTE: must match keys of local.platform_security_mode_options in main.tf
  validation {
    condition     = contains(["secure", "insecure"], var.platform_security_mode)
    error_message = "platform_security_mode must be one of: secure, insecure."
  }
}

variable "platform_db_deployment" {
  type = string
  # NOTE: must match keys of local.platform_db_dns_options in main.tf
  validation {
    condition     = contains(["container", "new", "existing", "mock"], var.platform_db_deployment)
    error_message = "platform_db_deployment must be one of: container, new, existing, mock."
  }
}

variable "platform_redis_deployment" {
  type = string
  # NOTE: must match keys of local.platform_redis_dns_options in main.tf
  validation {
    condition     = contains(["container", "new", "mock"], var.platform_redis_deployment)
    error_message = "platform_redis_deployment must be one of: container, new, mock."
  }
}

variable "studio_mode" {
  type = string
  # NOTE: must match keys of local.studio_dns_options in main.tf
  validation {
    condition     = contains(["subdomain", "path", "disabled"], var.studio_mode)
    error_message = "studio_mode must be one of: wildcard, path, disabled."
  }
}

variable "wave_mode" {
  type = string
  # NOTE: must match keys of local.wave_options in main.tf
  validation {
    condition     = contains(["wave", "wave-lite", "disabled"], var.wave_mode)
    error_message = "wave_mode must be one of: wave, wave-lite, disabled."
  }
}

variable "flag_enable_data_studio" {
  description = "Whether to use Studios."
  type        = bool
}

variable "flag_enable_data_studio_ssh" {
  description = "Whether SSH access to Data Studios is enabled."
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

variable "platform_existing_db_url" {
  description = "The database URL for an existing Platform DB."
  type        = string
}

variable "platform_db_schema_name" {
  description = "The name of the Tower database schema."
  type        = string
}

variable "platform_db_engine" {
  description = "The active DB engine version string (e.g., \"8.0\" or \"5.7\"). Used to select the correct JDBC connection-string suffix."
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
variable "flag_enable_groundswell" {
  description = "Whether to activate Groundswell."
  type        = bool
}

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
