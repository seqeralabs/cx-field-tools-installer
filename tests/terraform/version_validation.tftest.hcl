## tower_container_version validation rules: floor + tag-shape.
## See tests/terraform/README.md for how to run.

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

run "rejects_v25_below_floor" {
  command = plan

  variables {
    tower_container_version = "v25.3.0"
  }

  expect_failures = [var.tower_container_version]
}

run "rejects_v23_below_floor" {
  command = plan

  variables {
    tower_container_version = "v23.4.5"
  }

  expect_failures = [var.tower_container_version]
}

run "rejects_missing_v_prefix" {
  command = plan

  variables {
    tower_container_version = "26.1.0"
  }

  expect_failures = [var.tower_container_version]
}

run "rejects_non_semver_tag" {
  command = plan

  variables {
    tower_container_version = "vlatest"
  }

  expect_failures = [var.tower_container_version]
}

run "accepts_v26_1_0" {
  command = plan

  variables {
    tower_container_version = "v26.1.0"
  }

  # No expect_failures — plan is expected to proceed past variable validation.
  # Other validations / cross-variable Python checks may still fail downstream;
  # this test only asserts the floor passes.
}
