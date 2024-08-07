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

test-plan-generateplan:
	@if [ ! -f tests/resources/tf_plan/myplan.plan ]; then\
	  terraform plan -out=tests/resources/tf_plan/myplan.plan;\
	fi
	
	@if [ ! -f tests/resources/tf_plan/plan.json ]; then\
	  terraform show -json tests/resources/tf_plan/myplan.plan > tests/resources/tf_plan/plan.json;\
	fi

# BE CAREFUL WHEN TESTING THIS -- START WITH GARBAGE SECRETS TO MAKE SURE NOTHING LEAKS PRIOR TO USING 
# REAL VALUES.
test-plan-local: test-plan-generateplan
	# @terraform plan -out=tests/resources/tf_plan/myplan.plan
	# @terraform show -json tests/resources/tf_plan/myplan.plan > tests/resources/tf_plan/plan.json
	@pytest -rA tests/pytesttest/
	# @rm tests/resources/tf_plan/myplan.plan || true
	# @rm tests/resources/tf_plan/plan.json || true

test-plan-purge: test-plan-local
	@rm tests/resources/tf_plan/myplan.plan || true
	@rm tests/resources/tf_plan/plan.json || true

test-all:
	pytest -rA