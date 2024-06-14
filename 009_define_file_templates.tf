## ------------------------------------------------------------------------------------
## Tower config files
## ------------------------------------------------------------------------------------
locals {
  tower_env = templatefile("assets/src/tower_config/tower.env.tpl",
    {
      tower_server_url       = local.tower_server_url,
      tower_contact_email    = var.tower_contact_email,
      tower_enable_platforms = replace(var.tower_enable_platforms, "/\\s+/", ""),

      tower_root_users = replace(var.tower_root_users, "/\\s+/", ""),

      flag_use_container_db = var.flag_use_container_db,
      db_engine_version     = var.db_engine_version,

      tower_db_url           = local.tower_db_url,
      tower_db_driver        = var.tower_db_driver,
      tower_db_dialect       = var.tower_db_dialect,
      tower_db_min_pool_size = var.tower_db_min_pool_size,
      tower_db_max_pool_size = var.tower_db_max_pool_size,
      tower_db_max_lifetime  = var.tower_db_max_lifetime,
      flyway_locations       = var.flyway_locations,

      tower_redis_url = local.tower_redis_url,

      flag_use_aws_ses_iam_integration = var.flag_use_aws_ses_iam_integration,
      flag_use_existing_smtp           = var.flag_use_existing_smtp,

      tower_smtp_host = var.tower_smtp_host,
      tower_smtp_port = var.tower_smtp_port,

      flag_do_not_use_https = var.flag_do_not_use_https,

      flag_use_wave           = var.flag_use_wave,
      wave_server_url         = var.wave_server_url,
      flag_enable_groundswell = var.flag_enable_groundswell,

      flag_data_explorer_enabled        = var.flag_data_explorer_enabled,
      data_explorer_disabled_workspaces = var.data_explorer_disabled_workspaces

      tower_container_version = var.tower_container_version
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
      swell_database_name = var.swell_database_name
    }
  )

  groundswell_env = templatefile("assets/src/groundswell_config/groundswell.env.tpl",
    {
      db_tower_user     = local.tower_secrets["TOWER_DB_USER"]["value"],
      db_tower_password = local.tower_secrets["TOWER_DB_PASSWORD"]["value"],
      db_database_name  = var.db_database_name,
      tower_db_url      = local.tower_db_url,

      swell_db_user       = local.groundswell_secrets["SWELL_DB_USER"]["value"],
      swell_db_password   = local.groundswell_secrets["SWELL_DB_PASSWORD"]["value"],
      swell_database_name = var.swell_database_name,

      flag_use_container_db = var.flag_use_container_db,
      db_engine_version     = var.db_engine_version
    }
  )
}




## ------------------------------------------------------------------------------------
## Update Docker-Compose with Docker version
## ------------------------------------------------------------------------------------
locals {
  docker_compose = templatefile("assets/src/docker_compose/docker-compose.yml.tpl",
    {
      docker_version = var.tower_container_version,
      auth_oidc      = local.oidc_auth,
      auth_github    = local.oidc_github,

      db_database_name  = var.db_database_name
      db_tower_user     = local.tower_secrets["TOWER_DB_USER"]["value"],
      db_tower_password = local.tower_secrets["TOWER_DB_PASSWORD"]["value"],

      flag_use_container_db               = var.flag_use_container_db,
      flag_use_container_redis            = var.flag_use_container_redis,
      flag_use_custom_docker_compose_file = var.flag_use_custom_docker_compose_file,

      flag_enable_groundswell = var.flag_enable_groundswell,
      swell_container_version = var.swell_container_version,

      flag_new_enough_for_migrate_db = local.flag_new_enough_for_migrate_db,

      db_container_engine = var.db_container_engine,
      db_container_engine_version = var.db_container_engine_version
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

      seqerakit_flag_credential_create_aws    = var.seqerakit_flag_credential_create_aws,
      seqerakit_flag_credential_create_github = var.seqerakit_flag_credential_create_github,
      seqerakit_flag_credential_create_docker = var.seqerakit_flag_credential_create_docker,
      seqerakit_flag_credential_create_codecommit = var.seqerakit_flag_credential_create_codecommit,

      seqerakit_flag_credential_use_aws_role = var.seqerakit_flag_credential_use_aws_role
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
      subnets        = local.subnet_ids_ec2,
      securityGroups = [module.tower_batch_sg.security_group_id], # local.ec2_sg_final,
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
      app_name = var.app_name

      flag_generate_private_cacert     = tostring(var.flag_generate_private_cacert)
      flag_use_existing_private_cacert = tostring(var.flag_use_existing_private_cacert)
      flag_do_not_use_https            = tostring(var.flag_do_not_use_https)

      bucket_prefix_for_new_private_ca_cert = var.bucket_prefix_for_new_private_ca_cert
      existing_ca_cert_file                 = var.existing_ca_cert_file
      existing_ca_key_file                  = var.existing_ca_key_file

      populate_external_db = local.populate_external_db
      tower_db_url         = local.tower_db_url
      db_database_name     = var.db_database_name

      docker_compose_file = local.docker_compose_file

      tower_base_url     = local.tower_base_url
      tower_server_url   = local.tower_server_url
      tower_api_endpoint = local.tower_api_endpoint

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
      app_name          = var.app_name
      db_tower_user     = local.tower_secrets["TOWER_DB_USER"]["value"]
      db_tower_password = local.tower_secrets["TOWER_DB_PASSWORD"]["value"]
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
      flag_use_container_db = tostring(var.flag_use_container_db)
    }
  )

  ansible_06_run_seqerakit = templatefile("assets/src/ansible/06_run_seqerakit.yml.tpl",
    {
      app_name = var.app_name,
      seqerakit_flag_credential_create_codecommit = var.seqerakit_flag_credential_create_codecommit
    }
  )

  codecommit_seqerakit = templatefile("assets/src/bash/remote/codecommit_set_workspace_id.sh.tpl",
  {
    seqerakit_org_name = var.seqerakit_org_name,
    seqerakit_workspace_name =  var.seqerakit_workspace_name
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
      flag_docker_logging_local = var.flag_docker_logging_local,
      flag_docker_logging_journald = var.flag_docker_logging_journald,
      flag_docker_logging_jsonfile = var.flag_docker_logging_jsonfile
    }
  )
}
