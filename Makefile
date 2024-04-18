.PHONY: verify plan apply

verify-full:
	@export PYTHONDONTWRITEBYTECODE=1
	@echo "Verifying 'terraform.tfvars'."
	@python3 .githooks/check_configuration.py
	@tfsec

verify:
	@export PYTHONDONTWRITEBYTECODE=1
	@echo "Verifying 'terraform.tfvars'."
	@python3 .githooks/check_configuration.py

plan: verify
	@echo "Invoking 'terraform plan'"
	@terraform plan


apply: verify
	@echo "Invoking 'terraform plan'"
	@terraform plan
