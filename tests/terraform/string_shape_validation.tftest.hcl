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
