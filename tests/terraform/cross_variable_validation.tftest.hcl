## ------------------------------------------------------------------------------------
## Negative tests for the cross-variable `validation {}` rules in variables.tf.
##
## These rules replace the verify_only_one_true_set and verify_tfvars_config_dependencies
## groups previously implemented in scripts/installer/validation/check_configuration.py.
## See version_validation.tftest.hcl for the baseline-tfvars convention.
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

# ----- only-one-of-N flag groups ------------------------------------------------------

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
