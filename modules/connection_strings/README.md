# Connection Strings Module

This module generates and manages connection strings for Tower, Groundswell, Connect, and Wave-Lite services.

## Features

- Generates PostgreSQL connection strings for Tower and Swell databases
- Generates Redis connection strings for Tower, Connect, and Wave-Lite
- Supports both container-based and external database/Redis configurations
- Handles connection string formatting based on container versions

## Requirements

- Terraform >= 1.1.0

## Usage

```hcl
module "connection_strings" {
  source = "./modules/connection_strings/v1.0.0"

  # Feature Flags
  flag_create_load_balancer = var.flag_create_load_balancer
  flag_do_not_use_https    = var.flag_do_not_use_https
  flag_create_external_db  = var.flag_create_external_db
  flag_create_external_redis = var.flag_create_external_redis
  flag_use_wave_lite      = var.flag_use_wave_lite

  # Tower Configuration
  tower_server_url = var.tower_server_url
  tower_db_url    = var.tower_db_url
  db_database_name = var.db_database_name

  # Groundswell Configuration
  swell_database_name = var.swell_database_name

  # Wave Configuration
  wave_server_url = var.wave_server_url
  wave_lite_server_url = var.wave_lite_server_url

  # External Resource References
  rds_wave_lite = module.rds-wave-lite
  aws_elasticache_redis = aws_elasticache_cluster.redis
  elasticache_wave_lite = module.elasticache_wave_lite
  rds = module.rds
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| flag_create_load_balancer | Whether to create a load balancer | `bool` | n/a | yes |
| flag_do_not_use_https | Whether to disable HTTPS | `bool` | n/a | yes |
| flag_create_external_db | Whether to create an external database | `bool` | n/a | yes |
| flag_create_external_redis | Whether to create external Redis | `bool` | n/a | yes |
| flag_use_wave_lite | Whether to use Wave-Lite | `bool` | n/a | yes |
| tower_server_url | The server URL for Tower | `string` | n/a | yes |
| tower_db_url | The database URL for Tower when not creating new DB | `string` | n/a | yes |
| db_database_name | The name of the Tower database | `string` | n/a | yes |
| swell_database_name | The name of the Groundswell database | `string` | n/a | yes |
| wave_server_url | The server URL for Wave | `string` | n/a | yes |
| wave_lite_server_url | The server URL for Wave-Lite | `string` | n/a | yes |
| elasticache_wave_lite | The elasticache_wave_lite module object containing Redis configuration | `any` | `null` | no |
| aws_elasticache_redis | The aws_elasticache_cluster.redis object containing Redis cluster configuration | `any` | `null` | no |
| rds | The rds module object containing Tower RDS configuration | `any` | `null` | no |
| rds_wave_lite | The rds-wave-lite module object containing RDS configuration | `any` | `null` | no |

## Outputs

| Name | Description |
|------|-------------|
| tower_server_url | The server URL for Tower |
| tower_db_url | The database URL for Tower |
| groundswell_db_url | The database URL for Groundswell |
| connect_db_url | The database URL for Connect |
| wave_lite_db_url | The database URL for Wave-Lite |
| wave_lite_redis_url | The Redis URL for Wave-Lite |

Note: Connection string outputs containing credentials are marked as sensitive and will not be displayed in logs.
