locals {
  # Testing Mocks
  # ---------------------------------------------------------------------------------------
  # - If use_mocks is true, we will mock the resources that would otherwise be created.
  # - Useful for testing the connection strings without having to create the resources.

  # Lookup Objects
  # ---------------------------------------------------------------------------------------
  # - If insecure, use "http://" and set port. If secure, "use https://" and dont set port.

  platform_config = var.platform_security_mode == "secure" ? {
    api_url  = "https://${var.tower_server_url}/api"
    app_url  = "https://${var.tower_server_url}"
    base_dns = var.tower_server_url
    } : {
    api_url  = "http://${var.tower_server_url}:8000/api"
    app_url  = "http://${var.tower_server_url}:8000"
    base_dns = var.tower_server_url
  }

  platform_db_dns = {
    container = "db:3306"
    new       = try("${var.rds_tower.db_instance_address}:3306", "")
    existing  = var.platform_existing_db_url
    mock      = "mock.tower-db.com:3306" # IDEA: Consider using different port for extra testing?
  }

  platform_db_connstring = (startswith(var.platform_db_engine, "8.") ?
    "?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true" : ""
  )

  platform_redis_dns = {
    container = "redis:6379"
    new       = try("${var.elasticache_tower.cache_nodes[0].address}:${var.elasticache_tower.cache_nodes[0].port}", "")
    mock      = "mock.tower-redis.com:6379"
  }

  # TODO: Convert to secure rediss.
  platform_redis_url = {
    # secure = "rediss://${local.platform_redis_dns[var.platform_redis_deployment]}"  # Not currently supported
    insecure = "redis://${local.platform_redis_dns[var.platform_redis_deployment]}"
  }

  studio_config = {
    subdomain = {
      app_dns      = "connect.${var.tower_server_url}"
      wildcard_dns = "*.${var.tower_server_url}"
      app_url      = "https://connect.${var.tower_server_url}"
    }
    path = {
      app_dns      = var.data_studio_path_routing_url
      wildcard_dns = var.data_studio_path_routing_url
      app_url      = "${local.platform_config["app_url"]}"
    }
    disabled = {
      app_dns      = "N/A"
      wildcard_dns = "N/A"
      app_url      = "N/A"
    }
  }

  # DONT append `redis://` as prefix here. Studios does this itself. Breaks if we reuse `tower_redis_url`.
  # TODO figure out implications if I make Platform redis secure.
  studio_redis_url = {
    # secure = trimprefix(local.platform_redis_url["secure"], "rediss://")  # Not currently supported
    insecure = trimprefix(local.platform_redis_url.insecure, "redis://")
  }

  studio_ssh_url = var.flag_enable_data_studio_ssh ? {
    app_dns = "connect-ssh.${var.tower_server_url}"
    app_url = "https://connect-ssh.${var.tower_server_url}"
    } : {
    app_dns = "N/A"
    app_url = "N/A"
  }

  # NOTE (May 10/26) - wave-lite and wave-mirror each other for now. I could hardcode the 'wave' entry to avoid user
  # error, but I need to retain this flexibility for internal testing (where we point to staging, not prod).
  wave_config = {
    wave-lite = {
      app_dns = var.wave_server_url
      app_url = "https://${var.wave_server_url}"
    }
    wave = {
      app_dns = var.wave_server_url
      app_url = "https://${var.wave_server_url}"
    }
    disabled = {
      app_dns = "N/A"
      app_url = "N/A"
    }
  }

  # Emulates `var.platform_db_deployment`, but Wave-Lite is optional so set a "disabled" value too.
  wave_lite_db_dns_options = {
    container = "wave-db"
    new       = var.rds_wave_lite.db_instance_address
    existing  = "wave-db"
    mock      = "mock.wave-db.com" # IDEA: Consider using different port for extra testing?
    disabled  = "N/A"
  }

  # NOTE: Current as of July 29/25, Wave-Lite cannot be deployed to a pre-existing RDS Postgres instance.
  # If Platform deploys and is told to use an existing DB, solution will use a containerized DB. 
  # TODO: Add option for Wave to use existing postgres DB.
  wave_lite_db_config = var.wave_mode == "wave-lite" ? {
    app_dns = local.wave_lite_db_dns_options[var.platform_db_deployment]
    app_url = "jdbc:postgresql://${local.wave_lite_db_dns_options[var.platform_db_deployment]}:5432/wave"
    } : {
    app_dns = local.wave_lite_db_dns_options.disabled
    app_url = local.wave_lite_db_dns_options.disabled
  }

  wave_lite_redis_dns_options = {
    container = "wave-redis:6379"
    new       = var.elasticache_wave_lite.dns
    mock      = "mock.wave-redis.com:6379"
    disabled  = "N/A"
  }

  # TODO: New instances use secure redis. Container uses insecure.
  # TODO: Align logic so all wave redis deployments are secure only.
  wave_lite_redis_url_options = var.platform_redis_deployment == "new" ? {
    app_url = "rediss://${local.wave_lite_redis_dns_options[var.platform_redis_deployment]}:6379"
    } : {
    app_url = "redis://${local.wave_lite_redis_dns_options[var.platform_redis_deployment]}:6379"
  }

  groundswell_config = var.flag_enable_groundswell ? {
    app_dns = local.platform_db_dns[var.platform_db_deployment]
    app_url = "mysql://${local.platform_db_dns[var.platform_db_deployment]}/${var.swell_database_name}"
    } : {
    app_dns = "N/A"
    app_url = "N/A"
  }


  # Platform Core
  # ---------------------------------------------------------------------------------------
  tower_db_url = format(
    "jdbc:mysql://%s/%s%s",
    local.platform_db_dns[var.platform_db_deployment],
    var.platform_db_schema_name,
    local.platform_db_connstring
  )

  # TODO: Convert to secure rediss.
  tower_redis_url = local.platform_redis_url["insecure"]


  # CONNECT (STUDIO)
  # ---------------------------------------------------------------------------------------
  # Connect relies on the Seqera Platform Redis. It does not rely on any database.
  # DNS needs host-matching in the ALB (e.g.): studio.TOWER_DOMAIN, 123.TOWER_DOMAIN, 456.TOWER_DOMAIN
  # TODO: Add validation on variables so that var.flag_enable_data_studio cant be true if var.flag_do_no_use_https is false.
  tower_connect_redis_url = local.studio_redis_url["insecure"]

  tower_connect_ssh_dns = local.studio_ssh_url.app_dns
  tower_connect_ssh_url = local.studio_ssh_url.app_url


  # WAVE / WAVE-LITE
  # ---------------------------------------------------------------------------------------
  # TODO: June 16/25 -- Consider if `rediss://` hardcode aligns with how config is presented.
  # TODO: Add tf validation so var.flag_use_wave_lite cant be true if var.flag_do_not_use_https is false.
  tower_wave_dns = local.wave_config[var.wave_mode]["app_dns"]
  tower_wave_url = local.wave_config[var.wave_mode]["app_url"]

  wave_lite_db_url = local.wave_lite_db_config["app_url"]

  # NOTE: Current as of July 29/25, Wave-Lite container redis doesn't support SSL. Also can't use existing redis (not an option).
  wave_lite_redis_url = var.wave_mode == "wave-lite" ? local.wave_lite_redis_url_options["app_url"] : "N/A"

  # GROUNDSWELL
  # ---------------------------------------------------------------------------------------
  # - Uses a separate schema in Platform DB. Do not add connection string or else it breaks lightbulb icon in app. Does not need Redis.
  swell_db_dns = local.groundswell_config["app_dns"]
  swell_db_url = local.groundswell_config["app_url"]
}
