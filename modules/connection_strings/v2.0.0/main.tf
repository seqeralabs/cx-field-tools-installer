locals {
  # ═════════════════════════════════════════════════════════════════════════════
  # Three sections, each with a single role:
  #   1. Dispatch tables — pure data, one table per independent decision
  #   2. Resolved values — single [mode] dispatch per resource (no logic)
  #   3. Composed values — glue resolved values + literal strings into final URLs
  #
  # TODO markers indicate inputs/concepts that should be promoted from
  # inferred-from-existing-flag to dedicated module variables in a later pass.
  # ═════════════════════════════════════════════════════════════════════════════


  # ─────────────────────────────────────────────────────────────────────────────
  # SECTION 1 — Dispatch tables (pure data, no cross-references)
  # ─────────────────────────────────────────────────────────────────────────────

  platform_url_options = {
    secure   = { app_url = "https://${var.tower_server_url}", api_url = "https://${var.tower_server_url}/api", base_dns = var.tower_server_url }
    insecure = { app_url = "http://${var.tower_server_url}:8000", api_url = "http://${var.tower_server_url}:8000/api", base_dns = var.tower_server_url }
  }

  # DNS entries are HOST-ONLY (no port). URL composition appends the port. This keeps the
  # tower_db_dns / tower_redis_dns outputs clean (just hostname) while URLs include the port.
  platform_db_dns_options = {
    container = "db"
    new       = var.use_mocks ? "mock.tower-db.com" : try(var.rds_tower.db_instance_address, "")
    existing  = var.platform_existing_db_url
  }

  platform_db_connstring_options = {
    "8" = "?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true"
    "5" = ""
  }

  platform_redis_dns_options = {
    container = "redis"
    new       = var.use_mocks ? "mock.tower-redis.com" : try(var.elasticache_tower.cache_nodes[0].address, "")
  }

  platform_redis_prefix_options = {
    secure   = "rediss://"
    insecure = "redis://"
    none     = ""
  }

  studio_options = {
    subdomain = { app_dns = "connect.${var.tower_server_url}", wildcard_dns = "*.${var.tower_server_url}", app_url = "https://connect.${var.tower_server_url}" }
    path      = { app_dns = var.data_studio_path_routing_url, wildcard_dns = var.data_studio_path_routing_url, app_url = "https://${var.data_studio_path_routing_url}" }
    disabled  = { app_dns = "N/A", wildcard_dns = "N/A", app_url = "N/A" }
  }

  studio_ssh_options = {
    enabled  = { app_dns = "connect-ssh.${var.tower_server_url}", app_url = "https://connect-ssh.${var.tower_server_url}" }
    disabled = { app_dns = "N/A", app_url = "N/A" }
  }

  wave_options = {
    "wave-lite" = { app_dns = var.wave_server_url, app_url = "https://${var.wave_server_url}" }
    wave        = { app_dns = var.wave_server_url, app_url = "https://${var.wave_server_url}" }
    disabled    = { app_dns = "N/A", app_url = "N/A" }
  }

  wave_lite_db_dns_options = {
    container = "wave-db"
    new       = var.use_mocks ? "mock.wave-db.com" : try(var.rds_wave_lite.db_instance_address, "")
    existing  = "wave-db"
  }

  wave_lite_redis_dns_options = {
    container = "wave-redis"
    new       = var.use_mocks ? "mock.wave-redis.com" : try(var.elasticache_wave_lite.dns, "")
  }


  # ─────────────────────────────────────────────────────────────────────────────
  # SECTION 2 — Resolved values (single [mode] dispatch per resource)
  # ─────────────────────────────────────────────────────────────────────────────

  # Inferred mode strings derived from existing flags. TODO: promote each to a dedicated module variable.
  studio_ssh_mode              = var.flag_enable_data_studio_ssh ? "enabled" : "disabled" # TODO: var.studio_ssh_mode
  groundswell_mode             = var.flag_enable_groundswell ? "enabled" : "disabled"     # TODO: var.groundswell_mode
  redis_security_mode_inferred = "insecure"                                               # TODO: var.platform_redis_security_mode (then add "secure" support)
  platform_db_engine_key       = startswith(var.platform_db_engine, "8.") ? "8" : "5"

  # Pure dispatch — table[mode]. One step per resource, no composition.
  resolved_platform_config        = local.platform_url_options[var.platform_security_mode]
  resolved_platform_db_dns        = local.platform_db_dns_options[var.platform_db_deployment]
  resolved_platform_db_connstring = local.platform_db_connstring_options[local.platform_db_engine_key]
  resolved_platform_redis_dns     = local.platform_redis_dns_options[var.platform_redis_deployment]
  resolved_platform_redis_prefix  = local.platform_redis_prefix_options[local.redis_security_mode_inferred]
  resolved_studio_config          = local.studio_options[var.studio_mode]
  resolved_studio_ssh_config      = local.studio_ssh_options[local.studio_ssh_mode]
  resolved_wave_config            = local.wave_options[var.wave_mode]
  resolved_wave_lite_db_dns       = local.wave_lite_db_dns_options[var.platform_db_deployment]       # TODO: var.wave_lite_db_deployment (decouple from platform)
  resolved_wave_lite_redis_dns    = local.wave_lite_redis_dns_options[var.platform_redis_deployment] # TODO: var.wave_lite_redis_deployment


  # ─────────────────────────────────────────────────────────────────────────────
  # SECTION 3 — Composed values (final URL/DNS forms; per-resource composition rules)
  # ─────────────────────────────────────────────────────────────────────────────

  # Tower core
  composed_tower_base_url     = local.resolved_platform_config.base_dns
  composed_tower_server_url   = local.resolved_platform_config.app_url
  composed_tower_api_endpoint = local.resolved_platform_config.api_url

  # Tower DB — DNS is host-only; URL appends :3306
  composed_tower_db_url = "jdbc:mysql://${local.resolved_platform_db_dns}:3306/${var.platform_db_schema_name}${local.resolved_platform_db_connstring}"

  # Tower Redis — DNS is host-only; URL appends :6379
  composed_tower_redis_url = "${local.resolved_platform_redis_prefix}${local.resolved_platform_redis_dns}:6379"

  # Studio (Connect)
  composed_tower_connect_dns          = local.resolved_studio_config.app_dns
  composed_tower_connect_wildcard_dns = local.resolved_studio_config.wildcard_dns
  composed_tower_connect_server_url   = local.resolved_studio_config.app_url
  # Studios shares Platform Redis but prepends its own scheme; output is host:port only.
  # Gated on studio_mode == "disabled" so disabled deployments return N/A.
  composed_tower_connect_redis_dns = var.studio_mode == "disabled" ? "N/A" : local.resolved_platform_redis_dns
  composed_tower_connect_redis_url = var.studio_mode == "disabled" ? "N/A" : "${local.resolved_platform_redis_dns}:6379"

  # Studio SSH
  composed_tower_connect_ssh_dns = local.resolved_studio_ssh_config.app_dns
  composed_tower_connect_ssh_url = local.resolved_studio_ssh_config.app_url

  # Wave / Wave-Lite
  composed_tower_wave_dns = local.resolved_wave_config.app_dns
  composed_tower_wave_url = local.resolved_wave_config.app_url

  # Wave-Lite outputs gated on wave_mode (deployment is keyed on platform's mode but only valid for wave-lite)
  composed_wave_lite_db_dns = var.wave_mode != "wave-lite" ? "N/A" : local.resolved_wave_lite_db_dns
  composed_wave_lite_db_url = var.wave_mode != "wave-lite" ? "N/A" : "jdbc:postgresql://${local.resolved_wave_lite_db_dns}:5432/wave"

  composed_wave_lite_redis_dns = var.wave_mode != "wave-lite" ? "N/A" : local.resolved_wave_lite_redis_dns
  # Wave-Lite redis: rediss:// when deployment is "new" (real ElastiCache supports TLS), else redis://.
  # Coupling rule lives at the use site rather than in a dispatch table — different rule per resource.
  composed_wave_lite_redis_url = (
    var.wave_mode != "wave-lite" ? "N/A" :
    var.platform_redis_deployment == "new" ? "rediss://${local.resolved_wave_lite_redis_dns}:6379" :
    "redis://${local.resolved_wave_lite_redis_dns}:6379"
  )

  # Groundswell — uses Platform DB schema; no connstring suffix (breaks Groundswell's SQL connection)
  composed_swell_db_dns = local.groundswell_mode == "disabled" ? "N/A" : local.resolved_platform_db_dns
  composed_swell_db_url = local.groundswell_mode == "disabled" ? "N/A" : "mysql://${local.resolved_platform_db_dns}:3306/${var.swell_database_name}"
}
