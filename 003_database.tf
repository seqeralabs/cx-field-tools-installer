## ------------------------------------------------------------------------------------
## Database Subnet Group
## ------------------------------------------------------------------------------------
resource "aws_db_subnet_group" "tower_db" {
  count = var.flag_create_external_db == true ? 1 : 0

  name       = "${local.global_prefix}-tower-db"
  subnet_ids = local.subnet_ids_db

  tags = {
    Name = "${local.global_prefix}-tower-db"
  }
}


resource "aws_db_subnet_group" "wave_lite_db" {
  count = (var.flag_create_external_db == true && var.flag_use_wave_lite == true) ? 1 : 0

  name       = "${local.global_prefix}-wave-lite-db"
  subnet_ids = local.subnet_ids_db

  tags = {
    Name = "${local.global_prefix}-wave-lite-db"
  }
}


## ------------------------------------------------------------------------------------
## RDS - Create only if new external DB required
## ------------------------------------------------------------------------------------
module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "6.1.1"

  count = var.flag_create_external_db == true ? 1 : 0

  identifier = "${local.global_prefix}-db"

  engine            = var.db_engine
  engine_version    = var.db_engine_version
  instance_class    = var.db_instance_class
  allocated_storage = var.db_allocated_storage

  manage_master_user_password = false # Don't use Secrets Manager to generate some random password.
  username                    = local.tower_secrets["TOWER_DB_MASTER_USER"]["value"]
  password                    = local.tower_secrets["TOWER_DB_MASTER_PASSWORD"]["value"]

  db_subnet_group_name   = aws_db_subnet_group.tower_db[0].name
  vpc_security_group_ids = [module.tower_db_sg.security_group_id]
  #parameter_group_name         = aws_db_parameter_group.tower_db.name

  publicly_accessible = false

  # Don't understand why I have to do this but the RDS module screams if I don't
  family               = "${var.db_engine}${var.db_engine_version}" # DB parameter group
  major_engine_version = var.db_engine_version                      # DB option group

  # Deletion protection
  deletion_protection = var.db_deletion_protection
  skip_final_snapshot = var.skip_final_snapshot

  # Backups
  backup_retention_period = var.db_backup_retention_period
  storage_encrypted = var.db_enable_storage_encrypted

  # Performance Insights enablement
  # Fixes tfsec warning. As per AWS documentation, 7 day retention has no cost implication for customer.
  # Explicitly setting the 7-day retention period. Can be changed by installations should they wish to pay for longer period.
  # https://aws.amazon.com/rds/performance-insights/pricing/
  performance_insights_enabled = true
  performance_insights_retention_period = 7
}


module "rds-wave-lite" {
  source  = "terraform-aws-modules/rds/aws"
  version = "6.1.1"

  count = (var.flag_create_external_db == true && var.flag_use_wave_lite == true) ? 1 : 0

  identifier = "${local.global_prefix}-db-wave-lite"

  engine            = var.wave_lite_db_engine
  engine_version    = var.wave_lite_db_engine_version
  instance_class    = var.wave_lite_db_instance_class
  allocated_storage = var.wave_lite_db_allocated_storage

  manage_master_user_password = false # Don't use Secrets Manager to generate some random password.
  username                    = local.wave_lite_secrets["WAVE_LITE_DB_MASTER_USER"]["value"]
  password                    = local.wave_lite_secrets["WAVE_LITE_DB_MASTER_PASSWORD"]["value"]

  db_subnet_group_name   = aws_db_subnet_group.wave_lite_db[0].name
  vpc_security_group_ids = [module.tower_db_sg.security_group_id]
  #parameter_group_name         = aws_db_parameter_group.tower_db.name

  publicly_accessible = false

  # Don't understand why I have to do this but the RDS module screams if I don't
  family               = "${var.wave_lite_db_engine}${var.wave_lite_db_engine_version}" # DB parameter group
  major_engine_version = var.wave_lite_db_engine_version                      # DB option group

  # Deletion protection
  deletion_protection = false  # var.db_deletion_protection
  skip_final_snapshot = true  # var.skip_final_snapshot

  # Backups
  # backup_retention_period = var.db_backup_retention_period
  storage_encrypted = true  # var.db_enable_storage_encrypted

  # Performance Insights enablement
  # Fixes tfsec warning. As per AWS documentation, 7 day retention has no cost implication for customer.
  # Explicitly setting the 7-day retention period. Can be changed by installations should they wish to pay for longer period.
  # https://aws.amazon.com/rds/performance-insights/pricing/
  performance_insights_enabled = true
  performance_insights_retention_period = 7
}


## ------------------------------------------------------------------------------------
## Elasticache
## ------------------------------------------------------------------------------------
resource "aws_elasticache_subnet_group" "redis" {
  count = var.flag_create_external_redis == true ? 1 : 0

  name       = "${local.global_prefix}-redis"
  subnet_ids = local.subnet_ids_db
}

resource "aws_elasticache_subnet_group" "wave-lite-redis" {
  count = (var.flag_create_external_redis == true && var.flag_use_wave_lite == true) ? 1 : 0

  name       = "${local.global_prefix}-wave-lite-redis"
  subnet_ids = local.subnet_ids_db
}

#tfsec:ignore:aws-elasticache-enable-backup-retention
resource "aws_elasticache_cluster" "redis" {
  count = var.flag_create_external_redis == true ? 1 : 0

  cluster_id      = "${local.global_prefix}-redis"
  engine          = "redis"
  node_type       = "cache.m4.xlarge"
  num_cache_nodes = 1
  # parameter_group_name = "default.redis7.0.4"
  engine_version = "7.0"
  port           = 6379

  subnet_group_name  = aws_elasticache_subnet_group.redis[0].name
  security_group_ids = [module.tower_redis_sg.security_group_id]

  apply_immediately = true
}

resource "aws_elasticache_cluster" "wave-lite-redis" {
  count = (var.flag_create_external_redis == true && var.flag_use_wave_lite == true) ? 1 : 0

  cluster_id      = "${local.global_prefix}-wave-lite-redis"
  engine          = "redis"
  node_type       = "cache.m4.xlarge"
  num_cache_nodes = 1
  # parameter_group_name = "default.redis7.0.4"
  engine_version = "7.0"
  port           = 6379

  subnet_group_name  = aws_elasticache_subnet_group.wave-lite-redis[0].name
  security_group_ids = [module.tower_redis_sg.security_group_id]

  apply_immediately = true
}
