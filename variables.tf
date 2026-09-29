# ------------------------------------------------------------------------------------
# Testing
# ------------------------------------------------------------------------------------
# Added June 21/2025 for testing purposes (to drive mocking behaviour for to-be-created resources).
variable "use_mocks" {
  type        = bool
  default     = false
  description = "Use to drive mocking behaviour for to-be-created resources."
}


# ------------------------------------------------------------------------------------
# Mandatory Bootstrap Values
# ------------------------------------------------------------------------------------

variable "app_name" { type = string }

variable "secrets_bootstrap_tower" {
  type        = string
  description = "SSM SecureString for Tower secrets."
}

variable "secrets_bootstrap_seqerakit" {
  type        = string
  description = "SSM SecureString for Seqerakit secrets."
}

variable "secrets_bootstrap_groundswell" {
  type        = string
  description = "SSM SecureString for Groundswell secrets."
}

variable "secrets_bootstrap_wave_lite" {
  type        = string
  description = "SSM SecureString for Wave Lite secrets."
}

variable "aws_account" { type = string }
variable "aws_region" { type = string }
variable "aws_profile" { type = string }

variable "tower_container_version" {
  type        = string
  description = "Seqera Platform container version. master supports only v25+ — earlier majors live on the tag/legacy-final-pre-v25."
  # TODO(#332): once v26.1.x GA is selected, document the exact pinned tag here for reference.
  validation {
    # Match `v<digits>...`, then extract the major version as a number and compare numerically.
    # HCL's `>=` requires numeric operands; lexicographic string compare (the Python equivalent) is not supported.
    condition     = can(regex("^v[0-9]+", var.tower_container_version)) && tonumber(regex("^v([0-9]+)", var.tower_container_version)[0]) >= 25
    error_message = "tower_container_version must start with \"v\" and be v25.x or higher. For v24.x or earlier, check out git tag 'legacy-final-pre-v25'."
  }
}


# ------------------------------------------------------------------------------------
# SSM
# ------------------------------------------------------------------------------------

variable "flag_overwrite_ssm_keys" {
  type        = bool
  description = "Not to be used in PROD but helpful when sharing same instance in DEV."
  default     = false
}


# ------------------------------------------------------------------------------------
# Tags -- Default
# ------------------------------------------------------------------------------------

variable "default_tags" { type = map(string) }


# ------------------------------------------------------------------------------------
# Flags - Custom Naming
# ------------------------------------------------------------------------------------

variable "flag_use_custom_resource_naming_prefix" { type = bool }
variable "custom_resource_naming_prefix" { type = string }


# ------------------------------------------------------------------------------------
# Flags - Infrastructure
# ------------------------------------------------------------------------------------

variable "flag_create_new_vpc" { type = bool }
variable "flag_use_existing_vpc" { type = bool }

variable "flag_create_external_db" { type = bool }
variable "flag_use_existing_external_db" { type = bool }
variable "flag_use_container_db" { type = bool }

variable "flag_create_external_redis" { type = bool } # TO DO
variable "flag_use_container_redis" { type = bool }

variable "flag_create_load_balancer" { type = bool }
variable "flag_use_private_cacert" { type = bool }

variable "flag_run_studios_via_private_ca" {
  type        = bool
  description = "Make Platform and Studios trust the private root CA (Platform v26.2.0+, data_studio_container_version 0.12.2+, Studio images on Connect 0.13.0+). Mounts rootCA.crt into backend and cron and sets TOWER_SSL_CUSTOM_CA_CERT_FILE. Requires flag_use_private_cacert = true."

  # TODO: uncomment when the minimum Terraform version supports cross-variable checks (Terraform 1.9+;
  # 000_main.tf currently allows >= 1.1.0). Until then, check_configuration.py (verify_studios_private_ca)
  # enforces the same rules at `make verify` and exits with an error on a violation.
  #
  # validation {
  #   condition     = !var.flag_run_studios_via_private_ca || var.flag_use_private_cacert
  #   error_message = "flag_run_studios_via_private_ca = true requires flag_use_private_cacert = true."
  # }
  #
  # # Platform major.minor must be >= 26.2 ("v26.2.0-RC16" counts as 26.2).
  # validation {
  #   condition = !var.flag_run_studios_via_private_ca || (
  #     tonumber(regex("^v([0-9]+)\\.([0-9]+)", var.tower_container_version)[0]) > 26 ||
  #     (tonumber(regex("^v([0-9]+)\\.([0-9]+)", var.tower_container_version)[0]) == 26 &&
  #     tonumber(regex("^v([0-9]+)\\.([0-9]+)", var.tower_container_version)[1]) >= 2)
  #   )
  #   error_message = "flag_run_studios_via_private_ca = true requires tower_container_version >= v26.2.0."
  # }
  #
  # # Connect version must be >= 0.12.2.
  # validation {
  #   condition = !var.flag_run_studios_via_private_ca || (
  #     tonumber(split(".", var.data_studio_container_version)[0]) > 0 ||
  #     tonumber(split(".", var.data_studio_container_version)[1]) > 12 ||
  #     (tonumber(split(".", var.data_studio_container_version)[1]) == 12 && tonumber(split(".", var.data_studio_container_version)[2]) >= 2)
  #   )
  #   error_message = "flag_run_studios_via_private_ca = true requires data_studio_container_version >= 0.12.2."
  # }
}
variable "flag_do_not_use_https" { type = bool }

variable "flag_use_aws_ses_iam_integration" { type = bool }
variable "flag_use_existing_smtp" { type = bool }


# ------------------------------------------------------------------------------------
# Flags - Networking
# ------------------------------------------------------------------------------------

variable "flag_make_instance_public" { type = bool }
variable "flag_make_instance_private" { type = bool }
variable "flag_make_instance_private_behind_public_alb" { type = bool }
variable "flag_private_tower_without_eice" { type = bool }

variable "flag_vm_copy_files_to_instance" { type = bool }


# ------------------------------------------------------------------------------------
# Wave Service
# ------------------------------------------------------------------------------------

variable "flag_use_wave" { type = bool }
variable "flag_use_wave_lite" { type = bool }

variable "num_wave_lite_replicas" { type = number }
variable "wave_server_url" { type = string }
variable "wave_lite_container_version" { type = string }


# ------------------------------------------------------------------------------------
# Flags - DNS
# ------------------------------------------------------------------------------------

variable "flag_create_route53_private_zone" { type = bool }
variable "flag_use_existing_route53_public_zone" { type = bool }
variable "flag_use_existing_route53_private_zone" { type = bool }
variable "flag_create_hosts_file_entry" { type = bool }

variable "new_route53_private_zone_name" { type = string }

variable "existing_route53_public_zone_name" { type = string }
variable "existing_route53_private_zone_name" { type = string }


# ------------------------------------------------------------------------------------
# Custom Private CA
# ------------------------------------------------------------------------------------

variable "private_cacert_bucket_prefix" {
  type = string
  validation {
    condition     = var.private_cacert_bucket_prefix == "" || startswith(var.private_cacert_bucket_prefix, "s3://")
    error_message = "private_cacert_bucket_prefix must be empty or start with \"s3://\"."
  }
}


# ------------------------------------------------------------------------------------
# VPC (New)
# ------------------------------------------------------------------------------------

variable "vpc_new_cidr_range" { type = string }
variable "vpc_new_azs" { type = list(string) }

variable "vpc_new_private_subnets" { type = list(string) }
variable "vpc_new_public_subnets" { type = list(string) }

variable "vpc_new_ec2_subnets" { type = list(string) }
variable "vpc_new_batch_subnets" { type = list(string) }
variable "vpc_new_db_subnets" { type = list(string) }
variable "vpc_new_redis_subnets" { type = list(string) }

variable "vpc_new_alb_subnets" { type = list(string) }

variable "enable_vpc_flow_logs" { type = bool }
variable "flag_map_public_ip_on_launch" {
  type    = bool
  default = false
}


# ------------------------------------------------------------------------------------
# VPC (Existing)
# ------------------------------------------------------------------------------------

variable "vpc_existing_id" { type = string }
variable "vpc_existing_ec2_subnets" { type = list(string) }
variable "vpc_existing_batch_subnets" { type = list(string) }
variable "vpc_existing_db_subnets" { type = list(string) }
variable "vpc_existing_redis_subnets" { type = list(string) }

variable "vpc_existing_alb_subnets" { type = list(string) }


# ------------------------------------------------------------------------------------
# VPC Endpoints
# ssm,ssmmessages,ec2messages,cloudwatch-monitoring,cloudwatch-logs,smtp-ses,
# awsbatch,secretsmanager,rds,ecr-dkr,codecommit,git-codecommit,
# ecs-agent,ecs-telemetry,ecs
# ------------------------------------------------------------------------------------

variable "vpc_gateway_endpoints_all" { type = list(any) }

variable "vpc_interface_endpoints_tower" { type = list(any) }
variable "vpc_interface_endpoints_batch" { type = list(any) }


# ------------------------------------------------------------------------------------
# Security Group - Transaction Sources
# ------------------------------------------------------------------------------------

variable "sg_ingress_cidrs" { type = list(string) }
variable "sg_ssh_cidrs" { type = list(string) }
variable "sg_studio_ssh_cidrs" { type = list(string) }

variable "sg_egress_eice" { type = list(string) }
variable "sg_egress_tower_ec2" { type = list(string) }
variable "sg_egress_tower_alb" { type = list(string) }
variable "sg_egress_batch_ec2" { type = list(string) }
variable "sg_egress_interface_endpoint" { type = list(string) }


# ------------------------------------------------------------------------------------
# Groundswell
# ------------------------------------------------------------------------------------

variable "flag_enable_groundswell" { type = bool }

variable "swell_container_version" { type = string }
variable "swell_database_name" { type = string }


# ------------------------------------------------------------------------------------
# Data Explorer - Feature Gated (23.4.3+)
# ------------------------------------------------------------------------------------

variable "flag_data_explorer_enabled" { type = bool }

variable "data_explorer_disabled_workspaces" { type = string }


# ------------------------------------------------------------------------------------
# Data Studio - Feature Gated (24.1.0+)
# ------------------------------------------------------------------------------------

variable "flag_enable_data_studio" { type = bool }
variable "data_studio_container_version" { type = string }
variable "flag_limit_data_studio_to_some_workspaces" { type = bool }
variable "data_studio_eligible_workspaces" {
  type = string
  validation {
    condition     = var.data_studio_eligible_workspaces == "" || can(regex("^[0-9]+(,[0-9]+)*$", var.data_studio_eligible_workspaces))
    error_message = "data_studio_eligible_workspaces must be empty or a comma-separated list of numeric workspace IDs (e.g., \"123\" or \"123,456,789\")."
  }
}

variable "flag_enable_data_studio_ssh" { type = bool }
variable "flag_limit_data_studio_ssh_to_some_workspaces" { type = bool }
variable "data_studio_ssh_eligible_workspaces" {
  type = string
  validation {
    condition     = var.data_studio_ssh_eligible_workspaces == "" || can(regex("^[0-9]+(,[0-9]+)*$", var.data_studio_ssh_eligible_workspaces))
    error_message = "data_studio_ssh_eligible_workspaces must be empty or a comma-separated list of numeric workspace IDs (e.g., \"123\" or \"123,456,789\")."
  }
}

variable "flag_studio_enable_path_routing" { type = bool }
variable "data_studio_path_routing_url" {
  type        = string
  description = "Domain where Connect Proxy is available."
}

variable "data_studio_options" {
  type = map(object({
    qualifier = string
    icon      = string
    tool      = optional(string)
    status    = optional(string)
    container = string
  }))
}

# Studios general behaviour (v26.1.0+)
variable "data_studio_default_lifespan" { type = string }
variable "flag_studio_private_by_default" { type = bool }
# Studios metrics (v26.1.0+)
variable "data_studio_metrics_eligible_workspaces" {
  type = string
  validation {
    condition     = var.data_studio_metrics_eligible_workspaces == "" || can(regex("^[0-9]+(,[0-9]+)*$", var.data_studio_metrics_eligible_workspaces))
    error_message = "data_studio_metrics_eligible_workspaces must be empty or a comma-separated list of numeric workspace IDs (e.g., \"123\" or \"123,456,789\")."
  }
}
# Studios Wave integration (v26.1.0+)
variable "data_studio_wave_disallowed_registries" { type = string }
variable "data_studio_wave_custom_image_registry" { type = string }
variable "data_studio_wave_custom_image_repository" { type = string }

# Connect proxy - server config (v0.11.0+)
variable "connect_management_port" { type = string }
variable "connect_management_auth_key" { type = string }
variable "connect_log_level" { type = string }



# ------------------------------------------------------------------------------------
# Data Lineage - Feature Gated (v26.1.0+)
# ------------------------------------------------------------------------------------

variable "flag_enable_data_lineage" {
  type        = bool
  description = "Enable Nextflow data lineage tracking (Platform v26.1.0+). When true, the EC2 instance role gains S3+SQS permissions (plus SNS on v26.2.0+) so Platform can auto-provision per-workspace lineage infrastructure. When false on v26.2.0+, tower.env sets TOWER_LINEAGE_ALLOWED_WORKSPACES=-1 to keep lineage off."
}

variable "data_lineage_options" {
  type = object({
    allowed_workspaces    = string
    store_prefix          = string
    sns_max_retries       = number
    sns_max_delay_seconds = number
    migrate_sqs_transport = bool
    global_search_enabled = bool
  })
  description = "Data lineage settings, rendered to tower.env when flag_enable_data_lineage = true. allowed_workspaces: comma-separated numeric workspace IDs; empty = all workspaces. The other keys apply to Platform v26.2.0+ only."
  validation {
    condition     = var.data_lineage_options.allowed_workspaces == "" || can(regex("^[0-9]+(,[0-9]+)*$", var.data_lineage_options.allowed_workspaces))
    error_message = "data_lineage_options.allowed_workspaces must be empty or a comma-separated list of numeric workspace IDs (e.g., \"123\" or \"123,456,789\")."
  }
}


# ------------------------------------------------------------------------------------
# Database (Generic)
# ------------------------------------------------------------------------------------

variable "db_database_name" { type = string }


# ------------------------------------------------------------------------------------
# Database (Container)
# ------------------------------------------------------------------------------------

variable "db_container_engine" { type = string }

variable "db_container_engine_version" {
  type = string
  validation {
    condition     = tonumber(regex("^[0-9]+", var.db_container_engine_version)) >= 8
    error_message = "db_container_engine_version must be MySQL 8.x or higher."
  }
}


# ------------------------------------------------------------------------------------
# Database (External)
# ------------------------------------------------------------------------------------

variable "db_engine" { type = string }

variable "db_engine_version" {
  type = string
  validation {
    condition     = tonumber(regex("^[0-9]+", var.db_engine_version)) >= 8
    error_message = "db_engine_version must be MySQL 8.x or higher."
  }
}
variable "db_param_group" { type = string }
variable "db_instance_class" { type = string }
variable "db_allocated_storage" { type = number }

variable "db_deletion_protection" { type = bool }
variable "skip_final_snapshot" { type = bool }

variable "db_backup_retention_period" { type = number }
variable "db_enable_storage_encrypted" { type = bool }


variable "wave_lite_db_engine" { type = string }
variable "wave_lite_db_engine_version" { type = string }
variable "wave_lite_db_param_group" { type = string }
variable "wave_lite_db_instance_class" { type = string }
variable "wave_lite_db_allocated_storage" { type = number }

variable "wave_lite_db_deletion_protection" { type = bool }
variable "wave_lite_skip_final_snapshot" { type = bool }
variable "wave_lite_db_backup_retention_period" { type = number }
variable "wave_lite_db_enable_storage_encrypted" { type = bool }


# ------------------------------------------------------------------------------------
# Elasicache (External)
# ------------------------------------------------------------------------------------

variable "platform_redis_elasticache" {
  type = object({
    node_type       = string
    num_cache_nodes = number
    engine_version  = string
    port            = number
  })
  description = "Configuration for the standalone Seqera Platform ElastiCache (Redis) cluster created when flag_create_external_redis is true."
}

variable "wave_lite_elasticache" {
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
      num_node_groups            = optional(number)
      replicas_per_node_group    = optional(number)
      parameter_group_name       = string
    })

    encryption = object({
      auth_token                 = optional(string)
      at_rest_encryption_enabled = bool
      transit_encryption_enabled = bool
      kms_key_id                 = optional(string)
    })
  })
  description = "Configuration for the Wave Elasticache instance including networking, clustering, and encryption settings"
}


# ------------------------------------------------------------------------------------
# IAM
# ------------------------------------------------------------------------------------

variable "flag_iam_use_prexisting_role_arn" { type = bool }
variable "iam_prexisting_instance_role_arn" { type = string }


# ------------------------------------------------------------------------------------
# EC2 Host
# ------------------------------------------------------------------------------------

variable "ec2_host_instance_type" { type = string }

variable "flag_encrypt_ebs" { type = bool }
variable "flag_use_kms_key" { type = bool }
variable "ec2_ebs_kms_key" { type = string }
variable "ec2_root_volume_size" { type = number }

variable "ec2_require_imds_token" { type = bool }

variable "ec2_update_ami_if_available" { type = bool }


# ------------------------------------------------------------------------------------
# ALB
# ------------------------------------------------------------------------------------

variable "alb_certificate_arn" { type = string }


# ------------------------------------------------------------------------------------
# TOWER CONFIGURATION
# ------------------------------------------------------------------------------------

variable "tower_server_url" {
  type = string
  validation {
    condition     = !startswith(var.tower_server_url, "http")
    error_message = "tower_server_url must not include a protocol prefix (e.g., \"http://\" or \"https://\"). Provide hostname only."
  }
}
variable "tower_contact_email" { type = string }
variable "tower_enable_platforms" { type = string }

variable "tower_db_url" {
  type = string
  validation {
    condition     = !startswith(var.tower_db_url, "jdbc:") && !startswith(var.tower_db_url, "mysql:")
    error_message = "tower_db_url must not include a protocol prefix. Start with hostname."
  }
}

variable "tower_db_driver" {
  type = string
  validation {
    condition     = var.tower_db_driver == "org.mariadb.jdbc.Driver"
    error_message = "tower_db_driver must be \"org.mariadb.jdbc.Driver\"."
  }
}

variable "tower_db_dialect" {
  type = string
  validation {
    condition     = var.tower_db_dialect == "io.seqera.util.MySQL55DialectCollateBin"
    error_message = "tower_db_dialect must be \"io.seqera.util.MySQL55DialectCollateBin\"."
  }
}
variable "tower_db_min_pool_size" { type = number }
variable "tower_db_max_pool_size" { type = number }
variable "tower_db_max_lifetime" { type = number }

variable "tower_smtp_host" { type = string }
variable "tower_smtp_port" { type = string }
variable "tower_smtp_auth" { type = bool }
variable "tower_smtp_starttls_enable" { type = bool }
variable "tower_smtp_starttls_required" { type = bool }
variable "tower_smtp_ssl_protocols" { type = string }

variable "tower_root_users" {
  type = string
  validation {
    condition     = !contains(["REPLACE_ME", ""], var.tower_root_users)
    error_message = "tower_root_users must be populated with at least one email address."
  }
}
variable "tower_email_trusted_orgs" { type = string }
variable "tower_email_trusted_users" { type = string }

variable "flag_tower_enable_participant_auto_create_user" { type = bool }
variable "flag_tower_enable_member_auto_create_user" { type = bool }

variable "tower_audit_retention_days" { type = number }

# Audit Log v2 (v26.1.0+) — bundled object with nested `cleanup` sub-object.
# Pre-v26.1 Platform versions ignore the emitted env vars; `check_configuration.py`
# emits a warning if `tower_container_version < v26.1.0`.
variable "tower_audit_log_v2" {
  type = object({
    write_mode              = optional(string, "dual")
    csv_export_max_logs     = optional(number, 500000)
    pre_post_change_enabled = optional(bool, false)
    cleanup = optional(object({
      enabled    = optional(bool, true)
      interval   = optional(string, "5m")
      delay      = optional(string, "10s")
      chunk_size = optional(number, 1000)
    }), {})
  })

  validation {
    condition     = contains(["v1", "v2", "dual"], var.tower_audit_log_v2.write_mode)
    error_message = "tower_audit_log_v2.write_mode must be one of: \"v1\", \"v2\", \"dual\"."
  }

  validation {
    condition     = can(regex("^[0-9]+(ms|s|m|h|d)$", var.tower_audit_log_v2.cleanup.interval))
    error_message = "tower_audit_log_v2.cleanup.interval must be a duration like \"5m\", \"30s\", \"1h\", \"1d\" (digits followed by ms|s|m|h|d)."
  }

  validation {
    condition     = can(regex("^[0-9]+(ms|s|m|h|d)$", var.tower_audit_log_v2.cleanup.delay))
    error_message = "tower_audit_log_v2.cleanup.delay must be a duration like \"10s\", \"5m\", \"1h\", \"1d\" (digits followed by ms|s|m|h|d)."
  }
}

variable "flag_enable_standard_telemetry" {
  type        = string
  description = "Platform telemetry (v26.2.0+). \"standard\": standard + basic telemetry. \"basic\": basic telemetry only. \"air-gapped\": standard + basic telemetry, plus usage metrics written to files on the instance (`/home/ec2-user/.tower/usage-metrics`)."

  validation {
    condition     = contains(["standard", "basic", "air-gapped"], var.flag_enable_standard_telemetry)
    error_message = "flag_enable_standard_telemetry must be one of: \"standard\", \"basic\", \"air-gapped\"."
  }
}

variable "flag_enable_preflight_checks" {
  type        = bool
  description = "Platform preflight checks (v26.2.0+). When true, Platform runs preflight checks and validates credentials before a pipeline launch (TOWER_PREFLIGHT_CHECK_ENABLED, TOWER_CREDENTIALS_VALIDATION_ENABLED). Upstream default: true."
}

variable "tower_aws_secrets_kms_key_id" {
  type        = string
  description = "Installation-wide customer-managed KMS key for pipeline secrets (v26.2.0+), written as TOWER_AWS_SECRETS_KMS_KEY_ID. Key ARN or key ID, not an alias. Empty uses the AWS-managed key. A compute environment's own key takes precedence."

  # Mirrors Platform's KMS_KEY_ARN_OR_ID_PATTERN (AwsHelper.groovy). Platform refuses to start on a value that fails it.
  validation {
    condition     = can(regex("^((arn:aws[a-z0-9-]*:kms:[a-z0-9-]+:[0-9]{12}:key/)?(mrk-[0-9a-f]{32}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}))?$", var.tower_aws_secrets_kms_key_id))
    error_message = "tower_aws_secrets_kms_key_id must be empty, a KMS key ARN (arn:aws:kms:<region>:<account-id>:key/<key-id>), or a key ID (lowercase UUID or mrk-<32 hex>). Aliases are not accepted."
  }
}

variable "tower_actions" {
  description = "Actions (v26.2.0+). Per-trigger workspace allow-lists (\"\" = all workspaces, \"0\" = off, or workspace IDs) for the bucket, schedule and pipeline-run triggers, plus the trigger rate limit. Platform turns all three triggers on everywhere by default."
  type = object({
    bucket_trigger_allowed_workspaces   = string
    cron_trigger_allowed_workspaces     = string
    pipeline_trigger_allowed_workspaces = string
    trigger_rate_max_per_window         = number
    trigger_rate_window                 = string
  })

  # "0" passes this check: it's how a trigger is turned off (no workspace has ID 0).
  validation {
    condition = alltrue([
      for v in [
        var.tower_actions.bucket_trigger_allowed_workspaces,
        var.tower_actions.cron_trigger_allowed_workspaces,
        var.tower_actions.pipeline_trigger_allowed_workspaces,
      ] : v == "" || can(regex("^[0-9]+(,[0-9]+)*$", v))
    ])
    error_message = "tower_actions.*_allowed_workspaces must be \"\" (all workspaces), \"0\" (off), or a comma-separated list of numeric workspace IDs (e.g. \"123,456\")."
  }

  validation {
    condition     = var.tower_actions.trigger_rate_max_per_window >= 1 && floor(var.tower_actions.trigger_rate_max_per_window) == var.tower_actions.trigger_rate_max_per_window
    error_message = "tower_actions.trigger_rate_max_per_window must be a whole number of 1 or more."
  }

  validation {
    condition     = can(regex("^[0-9]+(ms|s|m|h|d)$", var.tower_actions.trigger_rate_window))
    error_message = "tower_actions.trigger_rate_window must be a duration like \"30m\", \"1h\", \"1d\" (digits followed by ms|s|m|h|d)."
  }
}

variable "tower_workflow_cleanup_enabled" { type = bool }

# Compute environment cleanup (v26.1.0+) — bundled object.
# Pre-v26.1 Platform versions silently ignore the emitted env vars; `check_configuration.py`
# emits a warning if cleanup is enabled alongside a pre-v26.1 `tower_container_version`.
variable "tower_compute_env_cleanup" {
  type = object({
    enabled                = optional(bool, false)
    delay                  = optional(string, "1m")
    interval               = optional(string, "1h")
    batch_size             = optional(number, 10)
    time_offset            = optional(string, "60s")
    stuck_creating_timeout = optional(string, "1h")
    stuck_deleting_timeout = optional(string, "1h")
  })

  validation {
    condition     = can(regex("^[0-9]+(ms|s|m|h|d)$", var.tower_compute_env_cleanup.delay))
    error_message = "tower_compute_env_cleanup.delay must be a duration like \"1m\", \"30s\", \"1h\", \"1d\" (digits followed by ms|s|m|h|d)."
  }
  validation {
    condition     = can(regex("^[0-9]+(ms|s|m|h|d)$", var.tower_compute_env_cleanup.interval))
    error_message = "tower_compute_env_cleanup.interval must be a duration like \"1m\", \"30s\", \"1h\", \"1d\" (digits followed by ms|s|m|h|d)."
  }
  validation {
    condition     = can(regex("^[0-9]+(ms|s|m|h|d)$", var.tower_compute_env_cleanup.time_offset))
    error_message = "tower_compute_env_cleanup.time_offset must be a duration like \"1m\", \"30s\", \"1h\", \"1d\" (digits followed by ms|s|m|h|d)."
  }
  validation {
    condition     = can(regex("^[0-9]+(ms|s|m|h|d)$", var.tower_compute_env_cleanup.stuck_creating_timeout))
    error_message = "tower_compute_env_cleanup.stuck_creating_timeout must be a duration like \"1m\", \"30s\", \"1h\", \"1d\" (digits followed by ms|s|m|h|d)."
  }
  validation {
    condition     = can(regex("^[0-9]+(ms|s|m|h|d)$", var.tower_compute_env_cleanup.stuck_deleting_timeout))
    error_message = "tower_compute_env_cleanup.stuck_deleting_timeout must be a duration like \"1m\", \"30s\", \"1h\", \"1d\" (digits followed by ms|s|m|h|d)."
  }
}

variable "tower_enable_openapi" { type = bool }

variable "tower_enable_pipeline_versioning" { type = bool }
variable "pipeline_versioning_eligible_workspaces" {
  type = string
  validation {
    condition     = var.pipeline_versioning_eligible_workspaces == "" || can(regex("^[0-9]+(,[0-9]+)*$", var.pipeline_versioning_eligible_workspaces))
    error_message = "pipeline_versioning_eligible_workspaces must be empty or a comma-separated list of numeric workspace IDs (e.g., \"123\" or \"123,456,789\")."
  }
}

# ------------------------------------------------------------------------------------
# TOWER CONFIGURATION - OIDC
# ------------------------------------------------------------------------------------

variable "flag_oidc_use_generic" { type = bool }
variable "flag_oidc_use_google" { type = bool }
variable "flag_oidc_use_github" { type = bool }

variable "flag_disable_email_login" { type = bool }


# ------------------------------------------------------------------------------------
# TOWER CONFIGURATION - Credentials
# ------------------------------------------------------------------------------------

variable "flag_allow_aws_instance_credentials" { type = bool }


# ------------------------------------------------------------------------------------
# EC2 - Docker Configuration
# ------------------------------------------------------------------------------------

variable "flag_docker_logging_local" { type = bool }
variable "flag_docker_logging_journald" { type = bool }
variable "flag_docker_logging_jsonfile" { type = bool }

variable "docker_cidr_range" { type = string }


# ------------------------------------------------------------------------------------
# seqerakit
# ------------------------------------------------------------------------------------

variable "flag_run_seqerakit" { type = bool }

variable "seqerakit_org_name" { type = string }
variable "seqerakit_org_fullname" { type = string }
variable "seqerakit_org_url" { type = string }

variable "seqerakit_team_name" { type = string }
variable "seqerakit_team_members" { type = string }

variable "seqerakit_workspace_name" { type = string }
variable "seqerakit_workspace_fullname" { type = string }

variable "seqerakit_compute_env_name" { type = string }
variable "seqerakit_compute_env_region" { type = string }
variable "seqerakit_root_bucket" { type = string }
variable "seqerakit_workdir" { type = string }
variable "seqerakit_outdir" { type = string }

variable "seqerakit_aws_use_fusion_v2" { type = bool }
variable "seqerakit_aws_use_forge" { type = bool }
variable "seqerakit_aws_use_batch" { type = bool }

variable "seqerakit_aws_fusion_instances" { type = string }
variable "seqerakit_aws_normal_instances" { type = string }

variable "seqerakit_aws_manual_head_queue" { type = string }
variable "seqerakit_aws_manual_compute_queue" { type = string }

variable "seqerakit_flag_credential_create_aws" { type = bool }
variable "seqerakit_flag_credential_create_github" { type = bool }
variable "seqerakit_flag_credential_create_docker" { type = bool }
variable "seqerakit_flag_credential_create_codecommit" { type = bool }

variable "seqerakit_flag_credential_use_aws_role" { type = bool }
variable "seqerakit_flag_credential_use_codecommit_baseurl" { type = bool }
