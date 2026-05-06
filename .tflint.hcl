config {
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

# Most variables are typed-only flags by convention; description requirement
# would be noise rather than signal here.
rule "terraform_documented_variables" {
  enabled = false
}
rule "terraform_documented_outputs" {
  enabled = false
}

# Modules are pinned via folder name (e.g. modules/connection_strings/v1.0.0/),
# not via a `version = ` argument.
rule "terraform_module_version" {
  enabled = false
}

