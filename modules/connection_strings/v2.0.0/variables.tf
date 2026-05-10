## ------------------------------------------------------------------------------------
## Mode strings
## Caller resolves user-facing flags into mode strings; module dispatches off the strings.
## Validation enforces that the value matches a key in the corresponding `*_options` table
## in main.tf — keep these lists in sync with that file when modes are added/removed.
## ------------------------------------------------------------------------------------
variable "platform_security_mode" {
  description = "Tower URL scheme: 'secure' (https) or 'insecure' (http with port 8000). Must match keys of local.platform_url_options."
  type        = string
  validation {
    condition     = contains(["secure", "insecure"], var.platform_security_mode)
    error_message = "platform_security_mode must be one of: secure, insecure."
  }
}

variable "platform_db_deployment" {
  description = "Tower DB deployment intent: 'container' (Docker), 'new' (newly-provisioned RDS), or 'existing' (caller-provided URL). Mock-vs-real host swap happens orthogonally via var.use_mocks. Must match keys of local.platform_db_dns_options."
  type        = string
  validation {
    condition     = contains(["container", "new", "existing"], var.platform_db_deployment)
    error_message = "platform_db_deployment must be one of: container, new, existing."
  }
}

variable "platform_redis_deployment" {
  description = "Tower Redis deployment intent: 'container' (Docker) or 'new' (newly-provisioned ElastiCache). Mock-vs-real host swap happens orthogonally via var.use_mocks. Must match keys of local.platform_redis_dns_options."
  type        = string
  validation {
    condition     = contains(["container", "new"], var.platform_redis_deployment)
    error_message = "platform_redis_deployment must be one of: container, new."
  }
}

variable "use_mocks" {
  description = "When true, the 'new' deployment mode uses mock host strings instead of dereferencing the (possibly-null) RDS/ElastiCache module objects. Container/existing deployments are unaffected (they're real regardless)."
  type        = bool
  default     = false
}

variable "studio_mode" {
  description = "Studio (Connect) DNS routing: 'subdomain' (e.g., connect.example.com), 'path' (path-based routing), or 'disabled'. Must match keys of local.studio_options."
  type        = string
  validation {
    condition     = contains(["subdomain", "path", "disabled"], var.studio_mode)
    error_message = "studio_mode must be one of: subdomain, path, disabled."
  }
}

variable "wave_mode" {
  description = "Wave deployment: 'wave-lite' (self-hosted), 'wave' (Seqera-hosted), or 'disabled'. Must match keys of local.wave_options."
  type        = string
  validation {
    condition     = contains(["wave-lite", "wave", "disabled"], var.wave_mode)
    error_message = "wave_mode must be one of: wave-lite, wave, disabled."
  }
}

## ------------------------------------------------------------------------------------
## Flag inputs (TODO: promote to mode strings in a later pass)
## ------------------------------------------------------------------------------------
variable "flag_enable_data_studio_ssh" {
  description = "Whether SSH access to Data Studios is enabled. TODO: promote to var.studio_ssh_mode."
  type        = bool
}

variable "flag_enable_groundswell" {
  description = "Whether to activate Groundswell. TODO: promote to var.groundswell_mode."
  type        = bool
}

## ------------------------------------------------------------------------------------
## Tower Core Configuration
## ------------------------------------------------------------------------------------
variable "tower_server_url" {
  description = "The base server URL for Tower (host only, e.g., 'tower.example.com')."
  type        = string
}

variable "platform_existing_db_url" {
  description = "Pre-existing DB URL (host:port). Only consulted when platform_db_deployment = 'existing'."
  type        = string
  default     = "N/A"
}

variable "platform_db_schema_name" {
  description = "Name of the Tower DB schema."
  type        = string
}

variable "platform_db_engine" {
  description = "Active DB engine version string (e.g., '8.0' or '5.7'). Selects the JDBC connection-string suffix."
  type        = string
}

variable "data_studio_path_routing_url" {
  description = "Domain where Connect Proxy is available. Only consulted when studio_mode = 'path'."
  type        = string
  default     = ""
}

## ------------------------------------------------------------------------------------
## Groundswell Configuration
## ------------------------------------------------------------------------------------
variable "swell_database_name" {
  description = "Name of the Groundswell DB schema."
  type        = string
}

## ------------------------------------------------------------------------------------
## Wave Configuration
## ------------------------------------------------------------------------------------
variable "wave_server_url" {
  description = "Server URL for Wave or Wave-Lite (host only)."
  type        = string
  default     = null
}

## ------------------------------------------------------------------------------------
## External Resource References
## TODO: replace these composite-typed inputs with resolved address strings (var.platform_db_address, etc.)
## ------------------------------------------------------------------------------------
variable "rds_tower" {
  description = "RDS module object for Tower DB. Used only when platform_db_deployment = 'new'."
  type        = any
  default     = null
}

variable "rds_wave_lite" {
  description = "RDS module object for Wave-Lite DB. Used only when wave_mode = 'wave-lite' AND platform_db_deployment = 'new'."
  type        = any
  default     = null
}

variable "elasticache_tower" {
  description = "ElastiCache cluster object for Tower Redis. Used only when platform_redis_deployment = 'new'."
  type        = any
  default     = null
}

variable "elasticache_wave_lite" {
  description = "ElastiCache module object for Wave-Lite Redis. Used only when wave_mode = 'wave-lite' AND platform_redis_deployment = 'new'."
  type        = any
  default     = null
}
