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

## =============================================================================================================
## TESTING
## =============================================================================================================
# If this stage fails with exit status 2, renew AWS SSO credentials.
# MAKE_TF_QUALIFIER is used to pass a qualifier to the plan command (eg. target specific resource or variable)
generate_json_plan:
	@echo "\nGenerating JSON representation of plan."
	@rm -f tfplan
	@rm -f tfplan.json
	@terraform plan ${MAKE_TF_QUALIFIER} -out=tfplan >  /dev/null 2>&1
	@terraform show -json tfplan | jq . > tfplan.json

test_cleanse:
	@rm tests/datafiles/base-overrides.auto.tfvars
	@rm tests/datafiles/terraform.tfvars
	@rm tests/datafiles/secrets/*.json 

generate_test_data:
	@echo "Generating test data."
	@cp templates/TEMPLATE_terraform.tfvars tests/datafiles/terraform.tfvars
	@cd tests/datafiles && ./generate_core_data.sh

run_tests:
	@pytest -c tests/pytest.ini tests/

terraform_test:
	@echo "Running terraform test (variable validations) — see tests/terraform/README.md"
	@if [ ! -f tests/datafiles/terraform.tfvars ]; then \
		echo "tests/datafiles/terraform.tfvars not found. Run 'make generate_test_data' first."; \
		exit 1; \
	fi
	@# scripts/installer/data_external/*.py reads terraform.tfvars from the project
	@# root by hard-coded path, so we have to materialise it there for the test run.
	@cp tests/datafiles/terraform.tfvars terraform.tfvars
	@cp tests/datafiles/base-overrides.auto.tfvars base-overrides.auto.tfvars 2>/dev/null || true
	@trap "rm -f terraform.tfvars base-overrides.auto.tfvars" EXIT; \
		terraform test -test-directory=tests/terraform

purge_cached_plans:
	@cd tests/ && rm -rf .plan_cache

purge_cached_templatefiles:
	@cd tests/ && rm -rf .templatefile_cache

purge_cache:
	@echo "Purging testing caches"
	@$(MAKE) purge_cached_templatefiles
	@$(MAKE) purge_cached_plans




