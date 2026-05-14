.PHONY: verify plan apply extract_hcl2json

# Phases 1+2 of #352: extract the hcl2json Go binary from the vendored container once at
# setup time and place it at HCL2JSON_BIN. `scripts/installer/utils/extractors.py:hcl_to_json`
# execs the binary directly on supported hosts (linux/amd64 + linux/arm64), avoiding ~1-2s of
# per-call Docker startup. Unsupported hosts (Darwin until Phase 3) keep the runtime
# `docker run` fallback, so this recipe is a no-op for them.
#
# HCL2JSON_DIR is a project-namespaced subdirectory under /tmp so that hosts running a
# bwrap sandbox can mount it into the jail (the default sandbox configuration isolates
# /tmp itself, which would hide the binary from pytest running inside the sandbox).
HCL2JSON_DIR := /tmp/cx-installer
HCL2JSON_BIN := $(HCL2JSON_DIR)/hcl2json
HCL2JSON_IMAGE := ghcr.io/seqeralabs/cx-field-tools-installer/hcl2json:0.6-vendored-multiarch@sha256:ef5c94eddaf8c364c171f50de7ff22477d68ab787d080e9c43d5c6e0be01af3c

extract_hcl2json:
	@arch="$$(uname -m)"; \
	if [ "$$(uname -s)" = "Linux" ] && { [ "$$arch" = "x86_64" ] || [ "$$arch" = "aarch64" ] || [ "$$arch" = "arm64" ]; }; then \
		if docker info >/dev/null 2>&1; then \
			echo "Extracting hcl2json binary to $(HCL2JSON_BIN)."; \
			mkdir -p $(HCL2JSON_DIR); \
			cid=$$(docker create $(HCL2JSON_IMAGE)); \
			docker cp $$cid:/hcl2json $(HCL2JSON_BIN) 2>/dev/null || docker cp $$cid:/usr/local/bin/hcl2json $(HCL2JSON_BIN); \
			docker rm $$cid > /dev/null; \
			chmod +x $(HCL2JSON_BIN); \
		elif [ -x "$(HCL2JSON_BIN)" ]; then \
			echo "extract_hcl2json: Docker unavailable; using existing binary at $(HCL2JSON_BIN)."; \
		else \
			echo "extract_hcl2json: Docker unavailable and no binary at $(HCL2JSON_BIN). Run 'make extract_hcl2json' from a host with Docker access first (the binary path can then be mounted into a sandbox)." >&2; \
			exit 1; \
		fi; \
	else \
		echo "extract_hcl2json: host $$(uname -s)/$$arch not covered by Phases 1-2; skipping (docker fallback will run at call time)."; \
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

purge_cached_console_outputs:
	@cd tests/ && rm -rf .console_cache

purge_cache:
	@echo "Purging testing caches"
	@$(MAKE) purge_cached_templatefiles
	@$(MAKE) purge_cached_plans
	@$(MAKE) purge_cached_console_outputs
