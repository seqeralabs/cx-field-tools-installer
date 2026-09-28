#!/usr/bin/env bash
# Stage orchestrator for Tower installer remote configuration.
#
# Replaces the 8 mid-pipeline null_resource steps that previously ran one
# Ansible playbook each, in sequence, each over its own SSH session. The
# `stage()` wrapper provides bracketed log markers so per-stage failure
# attribution survives despite the collapse — search the on-host log for
# "STAGE FAILED" to find the failure point.
#
# Invocation (from Terraform via SSH, see 011_configure_vm.tf):
#   ssh -T <host> 'RUN_SEQERAKIT=<true|false> bash /home/ec2-user/target/bash/remote/orchestrate.sh'
#
# Logs persist on the host at /home/ec2-user/tower-installer-logs/apply-<UTC>.log.
# Operators can clean old logs with:
#   find /home/ec2-user/tower-installer-logs -mtime +30 -delete

set -euo pipefail

LOG_DIR=/home/ec2-user/tower-installer-logs
LOG="${LOG_DIR}/apply-$(date -u +%Y%m%dT%H%M%SZ).log"
mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG") 2>&1

CURRENT_STAGE=""

# trap fires whenever set -e would terminate the script (i.e. any command
# returns non-zero outside of conditional contexts). The "STAGE FAILED" line
# is the load-bearing diagnostic — `grep "STAGE FAILED" <log>` pinpoints the
# failure regardless of what tool produced the error.
# shellcheck disable=SC2154  # `rc` is assigned in the same statement; shellcheck doesn't follow it.
trap 'rc=$?; [[ -n "$CURRENT_STAGE" ]] && echo "==== STAGE FAILED: $CURRENT_STAGE (exit=$rc) ===="' ERR

stage() {
  CURRENT_STAGE=$1
  shift
  local start
  start=$(date +%s)
  echo "==== STAGE START: $CURRENT_STAGE  $(date -u +%FT%TZ) ===="
  "$@"
  local end
  end=$(date +%s)
  echo "==== STAGE OK:    $CURRENT_STAGE  ($((end - start))s) ===="
  CURRENT_STAGE=""
}

cd /home/ec2-user

# --- pipeline ---
# Mirrors the order of the original 011_configure_vm.tf chain (host_configuration
# through run_seqerakit). Path conventions match the original `cd ${playbook_dir}`
# style (everything is under /home/ec2-user/target/...).

stage host_configuration  bash target/bash/remote/cleanse_and_configure_host.sh
stage ansible_wait        bash target/ansible/00_wait_for_ansible.sh
stage system_packages     ansible-playbook -i target/ansible/inventory.ini target/ansible/01_load_system_packages.yml
stage update_configs      ansible-playbook -i target/ansible/inventory.ini target/ansible/02_update_file_configurations.yml
stage pull_containers     ansible-playbook -i target/ansible/inventory.ini target/ansible/03_pull_containers_and_run_tower.yml
stage wait_for_tower      ansible-playbook -i target/ansible/inventory.ini target/ansible/04_wait_for_tower.yml
stage patch_groundswell   ansible-playbook -i target/ansible/inventory.ini target/ansible/05_patch_groundswell.yml

# Conditional final stage — gated on flag_run_seqerakit from tfvars, passed in
# as an env var to avoid re-rendering the script per-scenario.
if [[ "${RUN_SEQERAKIT:-false}" == "true" ]]; then
  stage seqerakit         ansible-playbook -i target/ansible/inventory.ini target/ansible/06_run_seqerakit.yml
fi

echo "==== ORCHESTRATOR COMPLETE ===="
