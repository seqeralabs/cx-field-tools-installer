## ------------------------------------------------------------------------------------
## Negative tests for the comma-separated-integer workspace-ID list variables.
## See version_validation.tftest.hcl for the baseline-tfvars convention.
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

run "rejects_non_numeric_data_studio_eligible_workspaces" {
  command = plan

  variables {
    data_studio_eligible_workspaces = "abc,def"
  }

  expect_failures = [var.data_studio_eligible_workspaces]
}

run "rejects_trailing_comma_data_studio_eligible_workspaces" {
  command = plan

  variables {
    data_studio_eligible_workspaces = "123,456,"
  }

  expect_failures = [var.data_studio_eligible_workspaces]
}

run "accepts_empty_data_studio_eligible_workspaces" {
  command = plan

  variables {
    data_studio_eligible_workspaces = ""
  }
}

run "accepts_single_id_data_studio_eligible_workspaces" {
  command = plan

  variables {
    data_studio_eligible_workspaces = "123"
  }
}

run "accepts_multiple_ids_data_studio_eligible_workspaces" {
  command = plan

  variables {
    data_studio_eligible_workspaces = "123,456,789"
  }
}

run "rejects_space_separated_data_studio_ssh_eligible_workspaces" {
  command = plan

  variables {
    data_studio_ssh_eligible_workspaces = "123 456"
  }

  expect_failures = [var.data_studio_ssh_eligible_workspaces]
}

run "rejects_non_numeric_pipeline_versioning_eligible_workspaces" {
  command = plan

  variables {
    pipeline_versioning_eligible_workspaces = "1,two,3"
  }

  expect_failures = [var.pipeline_versioning_eligible_workspaces]
}
