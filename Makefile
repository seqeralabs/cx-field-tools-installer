.PHONY: verify plan apply extract_hcl2json

# Phase 1 of #352: extract the hcl2json Go binary from the vendored container once at
# setup time and place it at HCL2JSON_BIN. `scripts/installer/utils/extractors.py:hcl_to_json`
# execs the binary directly on supported hosts (linux/amd64), avoiding ~1-2s of per-call
# Docker startup. Unsupported hosts (Darwin until Phase 3) keep the runtime `docker run`
# fallback, so this recipe is a no-op for them.
#
# HCL2JSON_DIR is a project-namespaced subdirectory under /tmp so that hosts running a
# bwrap sandbox can mount it into the jail (the default sandbox configuration isolates
# /tmp itself, which would hide the binary from pytest running inside the sandbox).
HCL2JSON_DIR := /tmp/cx-installer
HCL2JSON_BIN := $(HCL2JSON_DIR)/hcl2json
HCL2JSON_IMAGE := ghcr.io/seqeralabs/cx-field-tools-installer/hcl2json@sha256:48af2029d19d824ba1bd1662c008e691c04d5adcb055464e07b2dc04980dcbf5

extract_hcl2json:
	@if [ "$$(uname -s)" = "Linux" ] && [ "$$(uname -m)" = "x86_64" ]; then \
		echo "Extracting hcl2json binary to $(HCL2JSON_BIN)."; \
		mkdir -p $(HCL2JSON_DIR); \
		cid=$$(docker create $(HCL2JSON_IMAGE)); \
		docker cp $$cid:/hcl2json $(HCL2JSON_BIN) 2>/dev/null || docker cp $$cid:/usr/local/bin/hcl2json $(HCL2JSON_BIN); \
		docker rm $$cid > /dev/null; \
		chmod +x $(HCL2JSON_BIN); \
	else \
		echo "extract_hcl2json: host $$(uname -s)/$$(uname -m) not covered by Phase 1; skipping (docker fallback will run at call time)."; \
	fi

verify: extract_hcl2json
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

run_tests_all: extract_hcl2json
	@pytest -c tests/pytest.ini tests/

run_tests_core_only: extract_hcl2json
	@pytest -c tests/pytest.ini tests/ -m "not testcontainer and not variable_validation"

run_tests_containers_only: extract_hcl2json
	@pytest -c tests/pytest.ini tests/ -m "testcontainer"

run_tests_variables_only: extract_hcl2json
	@pytest -c tests/pytest.ini tests/ -m "variable_validation"

run_tests_core_and_containers: extract_hcl2json
	@pytest -c tests/pytest.ini tests/ -m "not variable_validation"

run_tests_core_and_variables: extract_hcl2json
	@pytest -c tests/pytest.ini tests/ -m "not testcontainer"

purge_cached_plans:
	@cd tests/ && rm -rf .plan_cache

purge_cached_templatefiles:
	@cd tests/ && rm -rf .templatefile_cache

purge_cache:
	@echo "Purging testing caches"
	@$(MAKE) purge_cached_templatefiles
	@$(MAKE) purge_cached_plans
