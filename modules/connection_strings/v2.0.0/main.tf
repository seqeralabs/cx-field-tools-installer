locals {
  # Testing Mocks
  # ---------------------------------------------------------------------------------------
  # - If use_mocks is true, we will mock the resources that would otherwise be created.
  # - Useful for testing the connection strings without having to create the resources.

  # Lookup Objects
  # ---------------------------------------------------------------------------------------
  # - If insecure, use "http://" and set port. If secure, "use https://" and dont set port.
  platform_urls = {
    secure = {
      base_dns = var.tower_server_url
      app_url  = "https://${var.tower_server_url}"
      api_url  = "https://${var.tower_server_url}/api"
    }
    insecure = {
      base_dns = var.tower_server_url
      app_url  = "http://${var.tower_server_url}:8000"
      api_url  = "http://${var.tower_server_url}:8000/api"
    }
  }

  platform_db_dns_options = {
    container = "db:3306"
    new       = "${var.rds_tower.db_instance_address}:3306"
    existing  = var.tower_db_url
    mock      = "mock.tower-db.com:3306"
  }

  platform_redis_dns_options = {
    container = "redis:6379"
    new       = "${var.elasticache_tower.cache_nodes[0].address}:${var.elasticache_tower.cache_nodes[0].port}"
    mock      = "mock.tower-redis.com:6379"
  }

  studio_dns_options = {
    subdomain = {
      dns      = "connect.${var.tower_server_url}"
      wildcard = "*.${var.tower_server_url}"
      app_url  = "https://connect.${var.tower_server_url}"
    }
    path = {
      dns      = var.data_studio_path_routing_url
      wildcard = var.data_studio_path_routing_url
      app_url  = "${local.platform_urls["secure"]["app_url"]}"
    }
    disabled = {
      dns      = "N/A"
      wildcard = "N/A"
    }
  }


  # Platform Core
  # ---------------------------------------------------------------------------------------
  tower_base_url     = local.platform_urls[var.platform_security_mode]["base_dns"]
  tower_server_url   = local.platform_urls[var.platform_security_mode]["app_url"]
  tower_api_endpoint = local.platform_urls[var.platform_security_mode]["api_url"]

  # IDEA: Consider using different port for extra testing?
  platform_db_dns        = local.platform_db_dns_options[var.platform_db_mode]
  platform_db_connstring = startswith(var.platform_db_engine, "8.") ? "?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true" : ""
  tower_db_url           = "jdbc:mysql://${local.platform_db_dns}/${var.platform_db_schema_name}${local.platform_db_connstring}"

  # TODO: May 16/2025 -- This Redis is unsecured (unlike Wave). Convert to secure rediss.
  platform_redis_dns = local.platform_redis_dns_options[var.platform_redis_mode]
  tower_redis_url    = "redis://${local.platform_redis_dns}"


  # CONNECT (STUDIO)
  # ---------------------------------------------------------------------------------------
  # Connect relies on the Seqera Platform Redis. It does not rely on any database.
  # DNS needs host-matching in the ALB (e.g.): studio.TOWER_DOMAIN, 123.TOWER_DOMAIN, 456.TOWER_DOMAIN
  # NOTE: `tower_connect_wildcard_dns` is misleading now since one of the options isn't actually a wildcard, but it means no changes in downstream DNS & ALB rules.
  # TODO: Add validation on variables so that var.flag_enable_data_studio cant be true if var.flag_do_no_use_https is false.
  connect_dns              = local.studio_dns_options[var.studio_mode]["dns"]
  connect_wildcard         = local.studio_dns_options[var.studio_mode]["wildcard"]
  tower_connect_server_url = local.studio_dns_options[var.studio_mode]["app_url"]

  # DONT append `redis://` as prefix here. Studios does this itself. Breaks if we reuse `tower_redis_url`.
  # DNS and URL will be the same but harmonizing them for consistency with other outputs and to be positioned for eventual Studios change.
  # Using same mock as tower redis to make tests more realistic.
  connect_redis_url = 
  ct_redis_container      = var.flag_use_container_redis ? "redis" : ""
  ct_redis_external_mock  = var.flag_create_external_redis && var.use_mocks ? "mock.tower-redis.com" : ""
  ct_redis_external_new   = var.flag_create_external_redis && !var.use_mocks ? "${var.elasticache_tower.cache_nodes[0].address}" : ""
  ct_redis_dns            = var.flag_enable_data_studio ? join("", [local.ct_redis_container, local.ct_redis_external_mock, local.ct_redis_external_new]) : "N/A"
  tower_connect_redis_dns = local.connect_enabled ? local.ct_redis_dns : "N/A"

  ct_redis_dns_with_port  = var.flag_create_external_redis && !var.use_mocks ? "${local.tower_connect_redis_dns}:${var.elasticache_tower.cache_nodes[0].port}" : "${local.tower_connect_redis_dns}:6379"
  tower_connect_redis_url = var.flag_enable_data_studio && !var.flag_do_not_use_https ? "${local.ct_redis_dns_with_port}" : "N/A"

  # CONNECT SSH
  # ---------------------------------------------------------------------------------------
  connect_ssh_enabled   = var.flag_enable_data_studio_ssh ? true : false
  tower_connect_ssh_dns = local.connect_ssh_enabled ? "connect-ssh.${var.tower_server_url}" : "N/A"
  tower_connect_ssh_url = local.connect_ssh_enabled ? "https://${local.tower_connect_ssh_dns}" : "N/A"


  # WAVE-LITE
  # ---------------------------------------------------------------------------------------
  # TODO: June 16/25 -- Consider if `rediss://` hardcode aligns with how config is presented.
  wave_lite_enabled = var.flag_use_wave_lite && !var.flag_do_not_use_https ? true : false
  wave_enabled      = var.flag_use_wave || local.wave_lite_enabled ? true : false

  tower_wave_dns = local.wave_enabled ? var.wave_server_url : "N/A"
  tower_wave_url = local.wave_enabled ? "https://${local.tower_wave_dns}" : "N/A"

  # NOTE: Current as of July 29/25, Wave-Lite cannot be deployed to a pre-existing RDS Postgres instance.
  wl_db_container     = var.flag_use_container_db || var.flag_use_existing_external_db ? "wave-db" : ""
  wl_db_external_mock = var.flag_create_external_db && local.wave_lite_enabled && var.use_mocks ? "mock.wave-db.com" : ""
  wl_db_external_new  = var.flag_create_external_db && local.wave_lite_enabled && !var.use_mocks ? var.rds_wave_lite.db_instance_address : ""
  wave_lite_db_dns    = local.wave_lite_enabled ? join("", [local.wl_db_container, local.wl_db_external_mock, local.wl_db_external_new]) : "N/A"
  wave_lite_db_url    = local.wave_lite_enabled ? "jdbc:postgresql://${local.wave_lite_db_dns}:5432/wave" : "N/A"

  # NOTE: Current as of July 29/25, Wave-Lite container redis doesn't support SSL. Also can't use existing redis (not an option).
  wl_redis_container     = var.flag_use_container_redis ? "wave-redis" : ""
  wl_redis_external_mock = var.flag_create_external_redis && local.wave_lite_enabled && var.use_mocks ? "mock.wave-redis.com" : ""
  wl_redis_external_new  = var.flag_create_external_redis && local.wave_lite_enabled && !var.use_mocks ? var.elasticache_wave_lite.dns : ""
  wl_redis_prefixed      = var.flag_create_external_redis ? "rediss://${local.wave_lite_redis_dns}" : "redis://${local.wave_lite_redis_dns}"
  wave_lite_redis_dns    = local.wave_lite_enabled ? join("", [local.wl_redis_container, local.wl_redis_external_mock, local.wl_redis_external_new]) : "N/A"
  wave_lite_redis_url    = local.wave_lite_enabled ? "${local.wl_redis_prefixed}:6379" : "N/A"



  # GROUNDSWELL
  # ---------------------------------------------------------------------------------------
  # - Uses a separate schema in Platform DB. Do not add connection string or else it breaks lightbulb icon in app. Does not need Redis.
  swell_db_dns = var.flag_enable_groundswell ? local.platform_db_dns : "N/A"
  swell_db_url = var.flag_enable_groundswell ? "mysql://${platform_db_dns}/${var.swell_database_name}" : "N/A"
}
