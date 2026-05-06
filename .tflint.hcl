# tflint configuration for cx-field-tools-installer.
# Initial baseline — strict on terraform-language hygiene, plus the AWS ruleset
# for the provider this project uses. Tighten over time.

config {
  # Use module = false: we are linting only the root module, not pulling in
  # every transitive child. The repo's child modules are simple and fine to
  # lint individually if needed.
  call_module_type = "local"
  force            = false
}

plugin "terraform" {
  enabled = true
  preset  = "recommended"
}

plugin "aws" {
  enabled = true
  version = "0.42.0"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}

# Comment-style rules we explicitly want off — these fire on legit patterns in
# this codebase (e.g. typed variables without descriptions are intentional for
# many of the bool flag groups). Re-enable per file once we do a docs pass.
rule "terraform_documented_variables" {
  enabled = false
}

rule "terraform_documented_outputs" {
  enabled = false
}

# The repo deliberately pins module versions via folder names (e.g.
# modules/connection_strings/v1.0.0/), not via `version = ` arguments. The
# version-required rule fires false-positives on this convention.
rule "terraform_module_version" {
  enabled = false
}

