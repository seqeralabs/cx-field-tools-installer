## ------------------------------------------------------------------------------------
## Negative tests for string-shape variable validations (variables.tf).
##
## See version_validation.tftest.hcl for the baseline-tfvars convention.
##
## Variables exercised:
##   - tower_server_url: rejects http(s):// scheme prefixes
##   - tower_root_users: rejects empty / "REPLACE_ME"
##   - alb_certificate_arn: ACM ARN shape (REPLACE_ME passthrough allowed)
##   - private_cacert_bucket_prefix: s3:// shape (REPLACE_ME passthrough allowed)
##   - db_engine_version, db_container_engine_version: MySQL 8.x floor
## ------------------------------------------------------------------------------------

mock_provider "aws" {}

# 000_main.tf jsondecodes each SSM payload and downstream locals look up specific
# keys (TOWER_DB_USER, SWELL_DB_USER, WAVE_LITE_REDIS_AUTH, etc.). Provide stub
# JSON per data source so plan can complete and the variable-validation diagnostics
# can surface. Keep this in sync with any new SSM key references in the .tf files.

override_data {
  target = data.aws_ssm_parameter.tower_secrets
  values = {
    value = "{\"TOWER_DB_USER\":{\"value\":\"stub\",\"ssm_key\":\"/stub/TOWER_DB_USER\"},\"TOWER_DB_PASSWORD\":{\"value\":\"stub\",\"ssm_key\":\"/stub/TOWER_DB_PASSWORD\"},\"TOWER_DB_MASTER_USER\":{\"value\":\"stub\",\"ssm_key\":\"/stub/TOWER_DB_MASTER_USER\"},\"TOWER_DB_MASTER_PASSWORD\":{\"value\":\"stub\",\"ssm_key\":\"/stub/TOWER_DB_MASTER_PASSWORD\"}}"
  }
}

override_data {
  target = data.aws_ssm_parameter.seqerakit_secrets
  values = {
    value = "{\"TOWER_AWS_ROLE\":{\"value\":\"stub\",\"ssm_key\":\"/stub/TOWER_AWS_ROLE\"}}"
  }
}

override_data {
  target = data.aws_ssm_parameter.groundswell_secrets
  values = {
    value = "{\"SWELL_DB_USER\":{\"value\":\"stub\",\"ssm_key\":\"/stub/SWELL_DB_USER\"},\"SWELL_DB_PASSWORD\":{\"value\":\"stub\",\"ssm_key\":\"/stub/SWELL_DB_PASSWORD\"}}"
  }
}

override_data {
  target = data.aws_ssm_parameter.wave_lite_secrets
  values = {
    value = "{\"WAVE_LITE_DB_MASTER_USER\":{\"value\":\"stub\",\"ssm_key\":\"/stub/WAVE_LITE_DB_MASTER_USER\"},\"WAVE_LITE_DB_MASTER_PASSWORD\":{\"value\":\"stub\",\"ssm_key\":\"/stub/WAVE_LITE_DB_MASTER_PASSWORD\"},\"WAVE_LITE_DB_LIMITED_USER\":{\"value\":\"stub\",\"ssm_key\":\"/stub/WAVE_LITE_DB_LIMITED_USER\"},\"WAVE_LITE_DB_LIMITED_PASSWORD\":{\"value\":\"stub\",\"ssm_key\":\"/stub/WAVE_LITE_DB_LIMITED_PASSWORD\"},\"WAVE_LITE_REDIS_AUTH\":{\"value\":\"stub\",\"ssm_key\":\"/stub/WAVE_LITE_REDIS_AUTH\"}}"
  }
}

override_data {
  target = module.connection_strings.data.external.generate_db_connection_string
  values = {
    result = {
      status = "0"
      value  = "?permitMysqlScheme=true"
    }
  }
}

run "rejects_http_prefix_on_tower_server_url" {
  command = plan

  variables {
    tower_server_url = "http://tower.example.com"
  }

  expect_failures = [var.tower_server_url]
}

run "rejects_https_prefix_on_tower_server_url" {
  command = plan

  variables {
    tower_server_url = "https://tower.example.com"
  }

  expect_failures = [var.tower_server_url]
}

run "rejects_unset_tower_root_users" {
  command = plan

  variables {
    tower_root_users = "REPLACE_ME"
  }

  expect_failures = [var.tower_root_users]
}

run "rejects_empty_tower_root_users" {
  command = plan

  variables {
    tower_root_users = "   "
  }

  expect_failures = [var.tower_root_users]
}

run "rejects_malformed_alb_certificate_arn" {
  command = plan

  variables {
    alb_certificate_arn = "not-an-arn"
  }

  expect_failures = [var.alb_certificate_arn]
}

run "rejects_non_s3_private_cacert_bucket_prefix" {
  command = plan

  variables {
    private_cacert_bucket_prefix = "https://my-bucket.s3.amazonaws.com"
  }

  expect_failures = [var.private_cacert_bucket_prefix]
}

run "rejects_mysql_5_7_db_engine_version" {
  command = plan

  variables {
    db_engine_version = "5.7"
  }

  expect_failures = [var.db_engine_version]
}

run "rejects_mysql_5_7_db_container_engine_version" {
  command = plan

  variables {
    db_container_engine_version = "5.7"
  }

  expect_failures = [var.db_container_engine_version]
}

run "rejects_mysql_5_6_db_engine_version" {
  command = plan

  variables {
    db_engine_version = "5.6"
  }

  expect_failures = [var.db_engine_version]
}
