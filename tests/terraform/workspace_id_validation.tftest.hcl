## ------------------------------------------------------------------------------------
## Negative tests for the comma-separated-integer workspace-ID list variables.
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
