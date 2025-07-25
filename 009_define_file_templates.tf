## ------------------------------------------------------------------------------------
## Tower config files
## ------------------------------------------------------------------------------------
locals {
  tower_env = templatefile("assets/src/tower_config/tower.env.tpl",
    {
      tower_server_url       = module.connection_strings.tower_server_url,
      tower_contact_email    = var.tower_contact_email,
      tower_enable_platforms = replace(var.tower_enable_platforms, "/\\s+/", ""),

      tower_root_users = replace(var.tower_root_users, "/\\s+/", ""),

      flag_use_container_db = var.flag_use_container_db,
      db_engine_version     = var.db_engine_version,

      tower_db_url           = module.connection_strings.tower_db_url,
      tower_db_driver        = var.tower_db_driver,
      tower_db_dialect       = var.tower_db_dialect,
      tower_db_min_pool_size = var.tower_db_min_pool_size,
      tower_db_max_pool_size = var.tower_db_max_pool_size,
      tower_db_max_lifetime  = var.tower_db_max_lifetime,
      flyway_locations       = var.flyway_locations,

      tower_redis_url = module.connection_strings.tower_redis_url,

      flag_use_aws_ses_iam_integration = var.flag_use_aws_ses_iam_integration,
      flag_use_existing_smtp           = var.flag_use_existing_smtp,

      tower_smtp_host = var.tower_smtp_host,
      tower_smtp_port = var.tower_smtp_port,

      flag_do_not_use_https = var.flag_do_not_use_https,

      flag_use_wave           = local.wave_enabled,
      wave_server_url         = module.connection_strings.tower_wave_url,
      flag_enable_groundswell = var.flag_enable_groundswell,

      flag_data_explorer_enabled        = var.flag_data_explorer_enabled,
      data_explorer_disabled_workspaces = var.data_explorer_disabled_workspaces,

      tower_container_version = var.tower_container_version,

      flag_enable_data_studio                   = var.flag_enable_data_studio,
      flag_limit_data_studio_to_some_workspaces = var.flag_limit_data_studio_to_some_workspaces,
      data_studio_eligible_workspaces           = var.data_studio_eligible_workspaces,
      tower_connect_server_url                  = module.connection_strings.tower_connect_server_url,

      data_studio_options             = var.data_studio_options,
      flag_studio_enable_path_routing = var.flag_studio_enable_path_routing
    }
  )

  tower_yml = templatefile("assets/src/tower_config/tower.yml.tpl",
    {
      app_name                  = var.app_name,
      tower_root_users          = var.tower_root_users,
      tower_email_trusted_orgs  = replace(var.tower_email_trusted_orgs, "/\\s+/", ""),
      tower_email_trusted_users = replace(var.tower_email_trusted_users, "/\\s+/", ""),

      TOWER_CONTACT_EMAIL = "${local.dollar}${local.dollar}{TOWER_CONTACT_EMAIL}",
      TOWER_SMTP_HOST     = "${local.dollar}${local.dollar}{TOWER_SMTP_HOST}",
      TOWER_SMTP_PORT     = "${local.dollar}${local.dollar}{TOWER_SMTP_PORT}",
      TOWER_SMTP_USER     = "${local.dollar}${local.dollar}{TOWER_SMTP_USER}",
      TOWER_SMTP_PASSWORD = "${local.dollar}${local.dollar}{TOWER_SMTP_PASSWORD}",

      tower_smtp_auth               = var.tower_smtp_auth,
      tower_smtp_starttls_enable    = var.tower_smtp_starttls_enable,
      tower_smtp_starttles_required = var.tower_smtp_starttls_required,
      tower_smtp_ssl_protocols      = var.tower_smtp_ssl_protocols,

      flag_disable_email_login = var.flag_disable_email_login,

      flag_enable_data_studio                   = var.flag_enable_data_studio,
      flag_limit_data_studio_to_some_workspaces = var.flag_limit_data_studio_to_some_workspaces,

      tower_audit_retention_days = var.tower_audit_retention_days,

      flag_using_micronaut_4 = local.flag_using_micronaut_4,

    }
  )

  tower_sql = templatefile("assets/src/tower_config/tower.sql.tpl",
    {
      db_tower_user     = local.tower_secrets["TOWER_DB_USER"]["value"],
      db_tower_password = local.tower_secrets["TOWER_DB_PASSWORD"]["value"],
      db_database_name  = var.db_database_name
    }
  )

  groundswell_sql = templatefile("assets/src/groundswell_config/groundswell.sql.tpl",
    {
      db_tower_user     = local.tower_secrets["TOWER_DB_USER"]["value"],
      db_tower_password = local.tower_secrets["TOWER_DB_PASSWORD"]["value"],
      db_database_name  = var.db_database_name,

      swell_db_user       = local.groundswell_secrets["SWELL_DB_USER"]["value"],
      swell_db_password   = local.groundswell_secrets["SWELL_DB_PASSWORD"]["value"],
      swell_database_name = var.swell_database_name,
      db_database_name    = var.db_database_name,
    }
  )

  groundswell_env = templatefile("assets/src/groundswell_config/groundswell.env.tpl",
    {
      db_tower_user     = local.tower_secrets["TOWER_DB_USER"]["value"],
      db_tower_password = local.tower_secrets["TOWER_DB_PASSWORD"]["value"],
      db_database_name  = var.db_database_name,
      tower_db_url      = module.connection_strings.tower_db_url,

      swell_db_user     = local.groundswell_secrets["SWELL_DB_USER"]["value"],
      swell_db_password = local.groundswell_secrets["SWELL_DB_PASSWORD"]["value"],
      # swell_database_name                     = var.swell_database_name,
      swell_db_url = module.connection_strings.swell_db_url,

      flag_use_container_db = var.flag_use_container_db,
      db_engine_version     = var.db_engine_version
    }
  )

  data_studios_env = templatefile("assets/src/tower_config/data-studios.env.tpl",
    {
      tower_server_url         = module.connection_strings.tower_server_url,
      tower_redis_url          = module.connection_strings.tower_connect_redis_url,
      tower_connect_server_url = module.connection_strings.tower_connect_server_url,
      studio_uses_distroless   = local.studio_uses_distroless
    }
  )
}


## ------------------------------------------------------------------------------------
## Wave Lite config files
## ------------------------------------------------------------------------------------
locals {
  wave_lite_yml = templatefile("assets/src/wave_lite_config/wave-lite.yml.tpl",
    {
      tower_server_url = module.connection_strings.tower_server_url,
      wave_server_url  = module.connection_strings.tower_wave_url,

      wave_lite_db_master_user      = local.wave_lite_secrets["WAVE_LITE_DB_MASTER_USER"]["value"]
      wave_lite_db_master_password  = local.wave_lite_secrets["WAVE_LITE_DB_MASTER_PASSWORD"]["value"]
      wave_lite_db_limited_user     = local.wave_lite_secrets["WAVE_LITE_DB_LIMITED_USER"]["value"]
      wave_lite_db_limited_password = local.wave_lite_secrets["WAVE_LITE_DB_LIMITED_PASSWORD"]["value"]
      wave_lite_redis_auth          = local.wave_lite_secrets["WAVE_LITE_REDIS_AUTH"]["value"]

      wave_lite_db_url    = module.connection_strings.wave_lite_db_url,
      wave_lite_redis_url = module.connection_strings.wave_lite_redis_url,
      tower_contact_email = var.tower_contact_email,
    }
  )
}



## ------------------------------------------------------------------------------------
## Update Docker-Compose with Docker version
## ------------------------------------------------------------------------------------
locals {
  docker_compose = templatefile("assets/src/docker_compose/docker-compose.yml.tpl",
    {
      docker_version    = var.tower_container_version,
      oidc_consolidated = local.oidc_consolidated,

      db_database_name  = var.db_database_name
      db_tower_user     = local.tower_secrets["TOWER_DB_USER"]["value"],
      db_tower_password = local.tower_secrets["TOWER_DB_PASSWORD"]["value"],

      flag_use_container_db               = var.flag_use_container_db,
      flag_use_container_redis            = var.flag_use_container_redis,
      flag_use_custom_docker_compose_file = var.flag_use_custom_docker_compose_file,

      flag_enable_groundswell = var.flag_enable_groundswell,
      swell_container_version = var.swell_container_version,

      flag_new_enough_for_migrate_db = local.flag_new_enough_for_migrate_db,

      db_container_engine         = var.db_container_engine,
      db_container_engine_version = var.db_container_engine_version,

      flag_enable_data_studio       = var.flag_enable_data_studio,
      data_studio_container_version = var.data_studio_container_version,
      updated_redis_version         = tonumber(length(regexall("^v24.2.[0-9]", var.tower_container_version))) >= 1 || tonumber(length(regexall("^v2[5-9].[0-9].[0-9]", var.tower_container_version))) >= 1 ? true : false,
      studio_uses_distroless        = local.studio_uses_distroless,

      flag_use_wave_lite        = var.flag_use_wave_lite,
      num_wave_lite_replicas    = var.num_wave_lite_replicas,
      wave_lite_redis_container = local.wave_lite_redis_container,
      wave_lite_db_container    = local.wave_lite_db_container,

      wave_lite_db_master_user     = local.wave_lite_secrets["WAVE_LITE_DB_MASTER_USER"]["value"]
      wave_lite_db_master_password = local.wave_lite_secrets["WAVE_LITE_DB_MASTER_PASSWORD"]["value"],
      wave_lite_redis_auth         = local.wave_lite_secrets["WAVE_LITE_REDIS_AUTH"]["value"],

      private_ca_cert = local.private_ca_cert,
      private_ca_key  = local.private_ca_key
    }
  )
}

## ------------------------------------------------------------------------------------
## Seqerakit - Everything But Compute Environments
## ------------------------------------------------------------------------------------
locals {
  seqerakit_yml = templatefile("assets/src/seqerakit/setup.yml.tpl",
    {
      seqerakit_org_name     = var.seqerakit_org_name,
      seqerakit_org_fullname = var.seqerakit_org_fullname,
      seqerakit_org_url      = var.seqerakit_org_url,

      seqerakit_team_name    = var.seqerakit_team_name,
      seqerakit_team_members = replace(var.seqerakit_team_members, "/\\s+/", ""),

      seqerakit_workspace_name     = var.seqerakit_workspace_name,
      seqerakit_workspace_fullname = var.seqerakit_workspace_fullname,

      seqerakit_workdir          = var.seqerakit_workdir,
      seqerakit_outdir           = var.seqerakit_outdir,
      seqerakit_compute_env_name = var.seqerakit_compute_env_name,

      seqerakit_flag_credential_create_aws        = var.seqerakit_flag_credential_create_aws,
      seqerakit_flag_credential_create_github     = var.seqerakit_flag_credential_create_github,
      seqerakit_flag_credential_create_docker     = var.seqerakit_flag_credential_create_docker,
      seqerakit_flag_credential_create_codecommit = var.seqerakit_flag_credential_create_codecommit,

      seqerakit_flag_credential_use_aws_role           = var.seqerakit_flag_credential_use_aws_role
      seqerakit_flag_credential_use_codecommit_baseurl = var.seqerakit_flag_credential_use_codecommit_baseurl
    }
  )
}


## ------------------------------------------------------------------------------------
## Seqerakit - Compute Environments
## ------------------------------------------------------------------------------------
locals {
  aws_batch_manual = templatefile("assets/src/seqerakit/compute-envs/aws_batch_manual.yml.tpl",
    {
      aws_region = var.seqerakit_compute_env_region,

      seqerakit_org_name         = var.seqerakit_org_name,
      seqerakit_workspace_name   = var.seqerakit_workspace_name,
      seqerakit_workdir          = var.seqerakit_workdir,
      seqerakit_compute_env_name = var.seqerakit_compute_env_name,

      seqerakit_aws_manual_head_queue    = var.seqerakit_aws_manual_head_queue,
      seqerakit_aws_manual_compute_queue = var.seqerakit_aws_manual_compute_queue,

      use_fusion_v2    = var.seqerakit_aws_use_fusion_v2 == true ? "True" : "False",
      use_wave         = var.seqerakit_aws_use_fusion_v2 == true ? "True" : "False",
      use_fast_storage = var.seqerakit_aws_use_fusion_v2 == true ? "True" : "False"
    }
  )
}


locals {
  aws_batch_forge = templatefile("assets/src/seqerakit/compute-envs/aws_batch_forge.yml.tpl",
    {
      aws_region = var.seqerakit_compute_env_region,

      seqerakit_org_name         = var.seqerakit_org_name,
      seqerakit_workspace_name   = var.seqerakit_workspace_name,
      seqerakit_workdir          = var.seqerakit_workdir,
      seqerakit_compute_env_name = var.seqerakit_compute_env_name,

      vpc_id         = local.vpc_id,
      subnets        = module.subnet_collector.subnet_ids_ec2,
      securityGroups = [module.sg_batch.security_group_id], # local.sg_ec2_final,
      ec2KeyPair     = aws_key_pair.generated_key.key_name,

      use_fusion_v2    = var.seqerakit_aws_use_fusion_v2 == true ? "True" : "False",
      use_wave         = var.seqerakit_aws_use_fusion_v2 == true ? "True" : "False",
      use_fast_storage = var.seqerakit_aws_use_fusion_v2 == true ? "True" : "False",

      instance_types = (
        var.seqerakit_aws_use_fusion_v2 == true ?
        replace(var.seqerakit_aws_fusion_instances, "/\\s+/", "") :
        replace(var.seqerakit_aws_normal_instances, "/\\s+/", "")
      )
    }
  )
}


## ------------------------------------------------------------------------------------
## VM Configuration - Mandatory
## ------------------------------------------------------------------------------------
locals {
  cleanse_and_configure_host = templatefile(
    "assets/src/bash/remote/cleanse_and_configure_host.sh.tpl",
    {
      app_name = var.app_name,

      cacert_private_active = tostring(local.cacert_private_active),
      flag_do_not_use_https = tostring(var.flag_do_not_use_https),

      bucket_prefix_for_new_private_ca_cert = var.bucket_prefix_for_new_private_ca_cert,

      populate_external_db = local.populate_external_db,
      tower_db_url         = module.connection_strings.tower_db_root,
      db_database_name     = var.db_database_name,

      use_wave_lite    = var.flag_use_wave_lite,
      wave_lite_db_url = module.connection_strings.wave_lite_db_url,

      docker_compose_file = local.docker_compose_file,

      tower_base_url     = module.connection_strings.tower_base_url,
      tower_server_url   = module.connection_strings.tower_server_url,
      tower_api_endpoint = module.connection_strings.tower_api_endpoint,

      flag_create_hosts_file_entry = var.flag_create_hosts_file_entry

    }
  )
}


## ------------------------------------------------------------------------------------
## Ansible
## ------------------------------------------------------------------------------------
locals {
  ansible_02_update_file_configurations = templatefile("assets/src/ansible/02_update_file_configurations.yml.tpl",
    {
      app_name = var.app_name

      tower_base_url                        = module.connection_strings.tower_base_url,
      bucket_prefix_for_new_private_ca_cert = var.bucket_prefix_for_new_private_ca_cert
    }
  )

  ansible_03_pull_containers_and_run_tower = templatefile("assets/src/ansible/03_pull_containers_and_run_tower.yml.tpl",
    {
      app_name = var.app_name
    }
  )

  ansible_05_patch_groundswell = templatefile("assets/src/ansible/05_patch_groundswell.yml.tpl",
    {
      flag_enable_groundswell = tostring(var.flag_enable_groundswell)
      flag_use_container_db   = tostring(var.flag_use_container_db)
    }
  )

  ansible_06_run_seqerakit = templatefile("assets/src/ansible/06_run_seqerakit.yml.tpl",
    {
      app_name                                    = var.app_name,
      seqerakit_flag_credential_create_codecommit = var.seqerakit_flag_credential_create_codecommit
    }
  )

  codecommit_seqerakit = templatefile("assets/src/bash/remote/codecommit_set_workspace_id.sh.tpl",
    {
      seqerakit_org_name       = var.seqerakit_org_name,
      seqerakit_workspace_name = var.seqerakit_workspace_name
    }
  )

}


## ------------------------------------------------------------------------------------
## SSH Config
## ------------------------------------------------------------------------------------
locals {
  ssh_config = templatefile("assets/src/ssh/ssh_config.tpl",
    {
      node_id = aws_instance.ec2.id,
      user    = "ec2-user",
      pemfile = "${path.module}/${local.ssh_key_name}",
      region  = var.aws_region,

      flag_make_instance_public       = var.flag_make_instance_public,
      flag_private_tower_without_eice = var.flag_private_tower_without_eice,
      dns_instance_ip                 = local.dns_instance_ip

      app_name = var.app_name
      profile  = var.aws_profile
    }
  )
}


## ------------------------------------------------------------------------------------
## EC2 Docker Logging
## ------------------------------------------------------------------------------------
locals {
  docker_logging = templatefile("assets/src/docker_logging/daemon.json.tpl",
    {
      flag_docker_logging_local    = var.flag_docker_logging_local,
      flag_docker_logging_journald = var.flag_docker_logging_journald,
      flag_docker_logging_jsonfile = var.flag_docker_logging_jsonfile,

      docker_cidr_range = var.docker_cidr_range
    }
  )
}


## ------------------------------------------------------------------------------------
## Tower Connect
## ------------------------------------------------------------------------------------
resource "tls_private_key" "connect_pem" {
  algorithm = "RSA"
  rsa_bits  = 4096
}


## ------------------------------------------------------------------------------------
## Local Server With Private CA Config
## ------------------------------------------------------------------------------------
locals {
  private_ca_conf = templatefile("assets/src/customcerts/custom_default.conf.tpl",
    {
      flag_enable_data_studio = var.flag_enable_data_studio,
      flag_use_wave_lite      = var.flag_use_wave_lite,

      tower_base_url    = module.connection_strings.tower_base_url,
      tower_connect_dns = module.connection_strings.tower_connect_dns,
      tower_wave_dns    = module.connection_strings.tower_wave_dns,

      private_ca_cert = local.private_ca_cert,
      private_ca_key  = local.private_ca_key
    }
  )
}
