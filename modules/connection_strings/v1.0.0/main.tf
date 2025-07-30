# https://medium.com/@leslie.alldridge/terraform-external-data-source-using-custom-python-script-with-example-cea5e618d83e
data "external" "generate_db_connection_string" {
  program = ["python3", "${path.module}/../../../scripts/installer/data_external/generate_db_connection_string.py"]
  query   = {}

  # Example how to use:
  #   query = {
  #     tower_container_version = var.tower_container_version
  #     flag_use_container_db = var.flag_use_container_db
  #   }
}

locals {
  # Testing Mocks
  # ---------------------------------------------------------------------------------------
  # If use_mocks is true, we will mock the resources that would otherwise be created.
  # This is useful for testing the connection strings without having to create the resources.


  # Control Flags
  # ---------------------------------------------------------------------------------------
  # If no HTTPS and no load-balancer, use `http://` and expose port in URL. Otherwise, use `https` prefix and no port.
  use_insecure_ec2 = var.flag_create_load_balancer == false && var.flag_do_not_use_https == true ? true : false

  # TOWER CORE
  # ---------------------------------------------------------------------------------------
  # Get the desired DNS name / IP from value user specified in terraform.tfvars 
  tower_base_url = var.tower_server_url

  tower_url_secure   = "https://${var.tower_server_url}"
  tower_url_insecure = "http://${var.tower_server_url}:8000"
  tower_server_url   = local.use_insecure_ec2 ? local.tower_url_insecure : local.tower_url_secure

  tower_api_endpoint = "${local.tower_server_url}/api"

  # Dont try to be smart. Just calculate all strings and use the flags / module feed to control what comes in.
  # Two DB options should always be "" so we can smash together in a unified catch-all.
  tower_db_container         = var.flag_use_container_db ? "db" : ""
  tower_db_external_mock     = var.flag_create_external_db && var.use_mocks ? "mock.tower-db.com" : ""
  tower_db_external_new      = var.flag_create_external_db && !var.use_mocks ? var.rds_tower.db_instance_address : ""
  tower_db_external_existing = var.flag_use_existing_external_db ? var.tower_db_url : ""
  tower_db_dns               = join("", [local.tower_db_container, local.tower_db_external_mock, local.tower_db_external_new, local.tower_db_external_existing])
  tower_db_dns_with_port     = "${local.tower_db_dns}:3306"
  # NOTE! DO NOT ADD '?' -- already applied by data.external.generate_db_connection_string.result.value

  tower_db_url = format(
    "jdbc:mysql://%s/%s%s",
    local.tower_db_dns_with_port,
    var.db_database_name,
    data.external.generate_db_connection_string.result.value,
  )

  # TODO: May 16/2025 -- This Redis is unsecured (unlike Wave). To be fixed in post-Wave-Lite Feature Release.
  # NOTE: Connect has same logic. I've duplicated to better handle divergence risk.
  tower_redis_container     = var.flag_use_container_redis ? "redis" : ""
  tower_redis_external_mock = var.flag_create_external_redis && var.use_mocks ? "mock.tower-redis.com" : ""
  tower_redis_external_new  = var.flag_create_external_redis && !var.use_mocks ? "${var.elasticache_tower.cache_nodes[0].address}" : ""
  tower_redis_dns           = join("", [local.tower_redis_container, local.tower_redis_external_mock, local.tower_redis_external_new])

  tower_redis_dns_with_port = var.flag_create_external_redis && !var.use_mocks ? "${local.tower_redis_dns}:${var.elasticache_tower.cache_nodes[0].port}" : "${local.tower_redis_dns}:6379"
  tower_redis_url           = "redis://${local.tower_redis_dns_with_port}"


  # GROUNDSWELL
  # ---------------------------------------------------------------------------------------
  # Uses a separate compartment in same DB as Tower uses. Do not add connection string or else it breaks lightbulb icon in app.
  # Does not need Redis.
  swell_db_url = format("%s/%s", local.tower_db_dns_with_port, var.swell_database_name)


  # CONNECT (STUDIO)
  # ---------------------------------------------------------------------------------------
  # Connect relies on the Seqera Platform Redis. It does not rely on any database.
  # DNS needs host-matching in the ALB (e.g.): studio.TOWER_DOMAIN, 123.TOWER_DOMAIN, 456.TOWER_DOMAIN
  # NOTE: `tower_connect_wildcard_dns` is misleading now since one of the options isn't actually a wildcard, but it means no changes in downstream DNS & ALB rules.
  tower_connect_dns          = var.flag_studio_enable_path_routing ? "${var.data_studio_path_routing_url}" : "connect.${var.tower_server_url}"
  tower_connect_wildcard_dns = var.flag_studio_enable_path_routing ? "${var.data_studio_path_routing_url}" : "*.${var.tower_server_url}"

  connect_url_secure       = "https://${local.tower_connect_dns}"
  connect_url_insecure     = "http://${var.tower_server_url}:9090"
  tower_connect_server_url = local.use_insecure_ec2 ? local.connect_url_insecure : local.connect_url_secure


  # DONT append `redis://` as prefix here. Studios does this itself. Breaks if we reuse `tower_redis_url`.
  # DNS and URL will be the same but harmonizing them for consistency with other outputs and to be positioned for eventual Studios change.
  # Using same mock as tower redis to make tests more realistic.
  connect_redis_container     = var.flag_use_container_redis ? "redis" : ""
  connect_redis_external_mock = var.flag_create_external_redis && var.use_mocks ? "mock.tower-redis.com" : ""
  connect_redis_external_new  = var.flag_create_external_redis && !var.use_mocks ? "${var.elasticache_tower.cache_nodes[0].address}" : ""
  tower_connect_redis_dns     = var.flag_enable_data_studio ? join("", [local.connect_redis_container, local.connect_redis_external_mock, local.connect_redis_external_new]) : "N/A"

  connect_redis_dns_with_port = var.flag_create_external_redis && !var.use_mocks ? "${local.tower_connect_redis_dns}:${var.elasticache_tower.cache_nodes[0].port}" : "${local.tower_connect_redis_dns}:6379"
  tower_connect_redis_url     = var.flag_enable_data_studio ? "${local.connect_redis_dns_with_port}" : "N/A"

  # WAVE-LITE
  # ---------------------------------------------------------------------------------------
  # TODO: June 16/25 -- Consider if `rediss://` hardcode aligns with how config is presented.
  wave_enabled = var.flag_use_wave || var.flag_use_wave_lite ? true : false

  tower_wave_dns = local.wave_enabled ? var.wave_server_url : "N/A"
  tower_wave_url = local.wave_enabled ? "https://${local.tower_wave_dns}" : "N/A"

  # NOTE: Current as of July 29/25, Wave-Lite cannot be deployed to a pre-existing RDS Postgres instance.
  wl_db_container     = var.flag_use_container_db || var.flag_use_existing_external_db ? "wave-db" : ""
  wl_db_external_mock = var.flag_create_external_db && var.use_mocks ? "mock.wave-db.com" : ""
  wl_db_external_new  = var.flag_create_external_db && !var.use_mocks ? var.rds_wave_lite.db_instance_address : ""
  wave_lite_db_dns    = local.wave_enabled ? join("", [local.wl_db_container, local.wl_db_external_mock, local.wl_db_external_new]) : "N/A"
  wave_lite_db_url    = local.wave_enabled ? "jdbc:postgresql://${local.wave_lite_db_dns}:5432/wave" : "N/A"

  # NOTE: Current as of July 29/25, Wave-Lite container redis doesn't support SSL
  wl_redis_container     = var.flag_use_container_redis ? "wave-redis" : ""
  wl_redis_external_mock = var.flag_create_external_redis && var.use_mocks ? "mock.wave-redis.com" : ""
  wl_redis_external_new  = var.flag_create_external_redis && !var.use_mocks ? var.elasticache_wave_lite.url : ""
  wl_redis_prefixed      = var.flag_create_external_redis ? "rediss://${local.wave_lite_redis_dns}" : "redis://${local.wave_lite_redis_dns}"
  wave_lite_redis_dns    = local.wave_enabled ? join("", [local.wl_redis_container, local.wl_redis_external_mock, local.wl_redis_external_new]) : "N/A"
  wave_lite_redis_url    = local.wave_enabled ? "${local.wl_redis_prefixed}:6379" : "N/A"
}

