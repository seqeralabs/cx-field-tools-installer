## Cross-variable validation rules: only-one-of-N flag groups and
## conditional-dependency requirements.

mock_provider "aws" {}

# Each SSM payload is jsondecode'd by the root locals, which then look up specific
# keys (and an inner `ssm_key` field) — so the stub JSON has to mirror that shape.

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

run "rejects_two_vpc_sources_true" {
  command = plan

  variables {
    flag_create_new_vpc   = true
    flag_use_existing_vpc = true
  }

  expect_failures = [var.flag_create_new_vpc]
}

run "rejects_zero_vpc_sources_true" {
  command = plan

  variables {
    flag_create_new_vpc   = false
    flag_use_existing_vpc = false
  }

  expect_failures = [var.flag_create_new_vpc]
}

run "rejects_two_db_sources_true" {
  command = plan

  variables {
    flag_create_external_db       = true
    flag_use_existing_external_db = true
    flag_use_container_db         = false
  }

  expect_failures = [var.flag_create_external_db]
}

run "rejects_two_redis_sources_true" {
  command = plan

  variables {
    flag_create_external_redis = true
    flag_use_container_redis   = true
  }

  expect_failures = [var.flag_create_external_redis]
}

run "rejects_two_endpoint_modes_true" {
  command = plan

  variables {
    flag_create_load_balancer = true
    flag_use_private_cacert   = true
    flag_do_not_use_https     = false
  }

  expect_failures = [var.flag_create_load_balancer]
}

run "rejects_both_smtp_modes_true" {
  command = plan

  variables {
    flag_use_aws_ses_iam_integration = true
    flag_use_existing_smtp           = true
  }

  expect_failures = [var.flag_use_aws_ses_iam_integration]
}

# ----- conditional-dependency rules ---------------------------------------------------

run "rejects_existing_vpc_without_id" {
  command = plan

  variables {
    flag_use_existing_vpc = true
    flag_create_new_vpc   = false
    vpc_existing_id       = "REPLACE_ME"
  }

  expect_failures = [var.vpc_existing_id]
}

run "rejects_alb_creation_without_cert_arn" {
  command = plan

  variables {
    flag_create_load_balancer = true
    flag_use_private_cacert   = false
    flag_do_not_use_https     = false
    alb_certificate_arn       = "REPLACE_ME"
  }

  expect_failures = [var.alb_certificate_arn]
}

run "rejects_route53_private_zone_without_name" {
  command = plan

  variables {
    flag_create_route53_private_zone = true
    new_route53_private_zone_name    = "REPLACE_ME"
  }

  expect_failures = [var.new_route53_private_zone_name]
}

run "rejects_existing_public_zone_without_name" {
  command = plan

  variables {
    flag_use_existing_route53_public_zone = true
    existing_route53_public_zone_name     = "REPLACE_ME"
  }

  expect_failures = [var.existing_route53_public_zone_name]
}

run "rejects_existing_private_zone_without_name" {
  command = plan

  variables {
    flag_use_existing_route53_private_zone = true
    existing_route53_private_zone_name     = "REPLACE_ME"
  }

  expect_failures = [var.existing_route53_private_zone_name]
}
