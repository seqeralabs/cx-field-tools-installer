.PHONY: verify plan apply

verify:
	@echo "Verifying 'terraform.tfvars'."
	@python3 scripts/installer/validation/check_configuration.py

verify-full: verify
	@echo "Verifying with tfsec."
	@tfsec

plan: verify
	@echo "Invoking 'terraform plan'"
	@terraform plan

apply: verify
	@echo "Invoking 'terraform apply'"
	@terraform apply

destroy: 
	@python3 .githooks/check_destroy.py
	@terraform destroy


# test-sensitive:
# 	@generate sensitive file
# 	@run scripts
# 	@destroy file

test-unit-local:
	pytest -rA scripts/tests/local

test-unit-remote:
	pytest -rA scripts/tests/remote

test-unit-all: test-unit-local test-unit-remote
	@echo pass > /dev/null

test-all:
	pytest -rA