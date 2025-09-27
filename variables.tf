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
  description = "Harbor container version (i.e. tag: `v23.2.0`)"
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

variable "private_cacert_bucket_prefix" { type = string }


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
# ssmmessages,ec2messages,cloudwatch-monitoring,cloudwatch-logs,smtp-ses,
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
variable "flag_studio_enable_path_routing" { type = bool }
variable "data_studio_path_routing_url" {
  type        = string
  description = "Domain where Connect Proxy is available."
}
variable "data_studio_container_version" { type = string }

variable "flag_limit_data_studio_to_some_workspaces" { type = bool }
variable "data_studio_eligible_workspaces" { type = string }

variable "data_studio_options" {
  type = map(object({
    qualifier = string
    icon      = string
    tool      = optional(string)
    status    = optional(string)
    container = string
  }))
}


# ------------------------------------------------------------------------------------
# Database (Generic)
# ------------------------------------------------------------------------------------

variable "db_database_name" { type = string }


# ------------------------------------------------------------------------------------
# Database (Container)
# ------------------------------------------------------------------------------------

variable "db_container_engine" { type = string }
variable "db_container_engine_version" { type = string }


# ------------------------------------------------------------------------------------
# Database (External)
# ------------------------------------------------------------------------------------

variable "db_engine" { type = string }
variable "db_engine_version" { type = string }
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

# TODO: Add Seqera Platform core instance post Wave-Lite feature release.

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

variable "tower_server_url" { type = string }
variable "tower_server_port" { type = string } # TODO: Update SG-generation logic to use this value
variable "tower_contact_email" { type = string }
variable "tower_enable_platforms" { type = string }

variable "tower_db_url" { type = string }
variable "tower_db_driver" { type = string }
variable "tower_db_dialect" { type = string }
variable "tower_db_min_pool_size" { type = number }
variable "tower_db_max_pool_size" { type = number }
variable "tower_db_max_lifetime" { type = number }
variable "flyway_locations" { type = string }

variable "tower_smtp_host" { type = string }
variable "tower_smtp_port" { type = string }
variable "tower_smtp_auth" { type = bool }
variable "tower_smtp_starttls_enable" { type = bool }
variable "tower_smtp_starttls_required" { type = bool }
variable "tower_smtp_ssl_protocols" { type = string }

variable "tower_root_users" { type = string }
variable "tower_email_trusted_orgs" { type = string }
variable "tower_email_trusted_users" { type = string }

variable "tower_audit_retention_days" { type = number }


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

