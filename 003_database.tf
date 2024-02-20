## ------------------------------------------------------------------------------------
## Database Subnet Group
## ------------------------------------------------------------------------------------
resource "aws_db_subnet_group" "tower_db" {
  count                         = var.flag_create_external_db == true ? 1 : 0

  name                          = "${local.global_prefix}-tower-db"
  subnet_ids                    = local.subnet_ids_db

  tags = {
    Name                        = "${local.global_prefix}-tower-db"
  }
}


## ------------------------------------------------------------------------------------
## RDS - Create only if new external DB required
## ------------------------------------------------------------------------------------
module "rds" {
  source                        = "terraform-aws-modules/rds/aws"
  version                       = "6.1.1"
  
  count                         = var.flag_create_external_db == true ? 1 : 0

  identifier                    = "${local.global_prefix}-db"

  engine                        = var.db_engine
  engine_version                = var.db_engine_version
  instance_class                = var.db_instance_class
  allocated_storage             = var.db_allocated_storage

  manage_master_user_password   = false    # Don't use Secrets Manager to generate some random password.
  username                      = local.tower_secrets["TOWER_DB_MASTER_USER"]["value"]
  password                      = local.tower_secrets["TOWER_DB_MASTER_PASSWORD"]["value"]

  db_subnet_group_name          = aws_db_subnet_group.tower_db[0].name
  vpc_security_group_ids        = [module.tower_db_sg.security_group_id]
  #parameter_group_name         = aws_db_parameter_group.tower_db.name
  publicly_accessible           = true
  skip_final_snapshot           = true

  # Don't understand why I have to do this but the RDS module screams if I don't
  family                        = "${var.db_engine}${var.db_engine_version}"        # DB parameter group
  major_engine_version          = var.db_engine_version                             # DB option group
}


## ------------------------------------------------------------------------------------
## Elasticache
## ------------------------------------------------------------------------------------
resource "aws_elasticache_subnet_group" "redis" {
  count                 = var.flag_create_external_redis == true ? 1 : 0

  name                  = "${local.global_prefix}-redis"
  subnet_ids            = local.subnet_ids_db
}

resource "aws_elasticache_cluster" "redis" {
  count                 = var.flag_create_external_redis == true ? 1 : 0

  cluster_id           = "${local.global_prefix}-redis"
  engine               = "redis"
  node_type            = "cache.m4.xlarge"
  num_cache_nodes      = 1
  # parameter_group_name = "default.redis7.0.4"
  engine_version       = "7.0"
  port                 = 6379

  subnet_group_name    = aws_elasticache_subnet_group.redis[0].name
  security_group_ids   = [module.tower_redis_sg.security_group_id] 

  apply_immediately    = true
}