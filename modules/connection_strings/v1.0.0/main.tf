# https://medium.com/@leslie.alldridge/terraform-external-data-source-using-custom-python-script-with-example-cea5e618d83e
# data "external" "generate_db_connection_string" {
#   program = ["python3", "${path.module}/.githooks/data_external/generate_db_connection_string.py"]
#   query = {
#     tower_container_version = var.tower_container_version
#     flag_use_container_db = var.flag_use_container_db
#     db_container_engine_version = var.db_container_engine_version
#     db_engine_version = var.db_engine_version
#   }
# }
data "external" "generate_db_connection_string" {
  program = ["python3", "${path.root}/scripts/installer/data_external/generate_db_connection_string.py"]
  query = {}
}


locals {
  

  # Control Flags
  # ---------------------------------------------------------------------------------------
  # If no HTTPS and no load-balancer, use `http://` and expose port in URL. Otherwise, use `https` prefix and no port.
  use_insecure_ec2 = var.flag_create_load_balancer == false && var.flag_do_not_use_https == true ? true : false

  # TOWER CORE
  # ---------------------------------------------------------------------------------------
  # Get the desired DNS name / IP from value user specified in terraform.tfvars 
  tower_base_url        = var.tower_server_url

  tower_url_secure      = "https://${var.tower_server_url}"
  tower_url_insecure    = "http://${var.tower_server_url}:9090"
  tower_server_url      = local.use_insecure_ec2 ? local.tower_url_insecure : local.tower_url_secure 

  tower_api_endpoint    = "${local.tower_server_url}/api"

  # Refactor: June 16,2025. Inverted logic to make cleaner (i.e. use supplied `var.tower_db_url` if not creating new DB).
  # TODO: June 16,2025. Rework how container DB value passed since this is default and has impact on Docker-Compose file.
  tower_db_root         = var.flag_create_external_db ? var.rds.db_instance_address : var.tower_db_url
  tower_db_url          = "${local.tower_db_root}/${var.db_database_name}${data.external.generate_db_connection_string.result.value}"

  # TODO: May 16/2025 -- This Redis is unsecured (unlike Wave). To be fixed in post-Wave-Lite Feature Release.
  # TBD: June 16/2025 -- Should I continue mirroring verbose tfvars keys for traceabilty or chop down for more compact code?
  tower_redis_local     = "redis://redis:6379"
  tower_redis_remote    = "redis://${var.aws_elasticache_redis.cache_nodes[0].address}:${var.aws_elasticache_redis.cache_nodes[0].port}"
  tower_redis_url       = var.flag_create_external_redis ? local.tower_redis_remote : local.tower_redis_local 


  # GROUNDSWELL
  # ---------------------------------------------------------------------------------------
  # Groundswell needs its own area of the core Tower database, but not Redis.
  swell_db_url          = "${local.tower_db_root}/${var.swell_database_name}${data.external.generate_db_connection_string.result.value}"

  
  # CONNECT (STUDIO)
  # ---------------------------------------------------------------------------------------
  # Connect needs Redis but not its own database.
  # DNS needs host-matching in the ALB (e.g.): studio.TOWER_DOMAIN, 123.TOWER_DOMAIN, 456.TOWER_DOMAIN
  tower_connect_dns           = "connect.${var.tower_server_url}"
  tower_connect_wildcard_dns  = "*.${var.tower_server_url}"
  
  connect_url_secure        = "https://${local.tower_server_url}"
  connect_url_insecure      = "http://${local.tower_server_url}:9090"
  tower_connect_server_url  = local.use_insecure_ec2 ? local.connect_url_insecure : local.connect_url_secure 


  #  Connect logic seems to append `redis://` as prefix. Breaks if we reuse `tower_redis_url`.
  # TODO: May 16/2025 -- post-Wave-Lite Feature Release, check if auto-appending behaviour still happening.
  connect_redis_local       = "redis:6379"
  connect_redis_remote      = "${var.aws_elasticache_redis.cache_nodes[0].address}:${var.aws_elasticache_redis.cache_nodes[0].port}" 
  tower_connect_redis_url   = var.flag_create_external_redis ? local.connect_redis_remote : local.connect_redis_local
  

  # WAVE-LITE
  # ---------------------------------------------------------------------------------------
  # NOTE: June 16/25 -- Removed var.flag_use_wave_lite check as it was irrelevant. We are just assigning a string here
  #                     The infra wont actually get created unless this flag is true.
  # TODO: June 16/25 -- Consider if `rediss://` hardcode aligns with how config is presented.
  # TODO: June 16/25 -- Consider if abbreviated variables make code more legible.
  tower_wave_url      = var.flag_use_wave_lite ? var.wave_lite_server_url : var.wave_server_url
  tower_wave_dns      = replace(local.tower_wave_url, "https://", "")

  # TODO: June 16/2025 -- Modify this to handle container paths and TF paths.
  wl_db_local         = "wave-db:5432"
  wl_db_remote        = var.rds_wave_lite.db_instance_address
  wave_lite_db_url    = var.flag_create_external_db ? local.wl_db_remote : local.wl_db_local

  wl_redis_local      = "redis://wave-redis:6379"
  wl_redis_remote     = "rediss://${var.elasticache_wave_lite[0].url}"
  wave_lite_redis_url = var.flag_create_external_redis ? local.wl_redis_remote : local.wl_redis_local
}