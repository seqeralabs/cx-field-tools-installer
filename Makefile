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

# TESTING
generate_json_plan:
	@echo "Generating JSON representation of plan"
	@rm tfplan || true >           /dev/null 2>&1
	@rm tfplan.json || true>       /dev/null 2>&1
	@terraform plan -out=tfplan >  /dev/null 2>&1
	@terraform show -json tfplan | jq . > tfplan.json

test_plan_only:
	@echo "Testing plan values only."
	@./tests/run_tests.sh

test_deployed_infrastructure:
	@echo "Testing deployed infrastructure."