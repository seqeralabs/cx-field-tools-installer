/* NOTE
June 28/26: Collapsed the VM-side pipeline into ONE null_resource. Failure attribution
moves entirely to bracketed log markers — both at the local stages here (ssh_probe /
file_transfer / remote_orchestrator) and at the remote orchestrator (see
`assets/src/bash/remote/orchestrate.sh`).

The gate that decides whether the VM-side pipeline runs at all is
`var.flag_vm_copy_files_to_instance`. It is defined once, on
`null_resource.allow_file_copy_to_start` in 010_prepare_config_files.tf (the
asset-generation barrier). `configure_vm` copies it via `length(...)`.

See https://github.com/seqeralabs/cx-field-tools-installer/issues/410.
*/

## ------------------------------------------------------------------------------------
## VM-side pipeline — probe SSH, copy files, run remote orchestrator.
##
## Three local-side phases bracketed by STAGE START / STAGE OK markers (same
## convention as orchestrate.sh on the host):
##   1. ssh_probe          : poll the EC2 over SSH until reachable
##   2. file_transfer      : scp assets/target/ to /home/ec2-user/target on the host
##   3. remote_orchestrator: ssh + bash orchestrate.sh on the host (full Ansible reconcile)
##
## On failure, `set -e` aborts. The last STAGE START line without a matching
## STAGE OK identifies the failing phase. The remote orchestrator's own log at
## /home/ec2-user/tower-installer-logs/apply-*.log provides further detail for
## any failure that happens once it's running.
## ------------------------------------------------------------------------------------
resource "null_resource" "configure_vm" {
  # 1 when the gate in 010 is on, 0 when off. Keeps the gate in one place.
  count = length(null_resource.allow_file_copy_to_start)

  triggers   = { always_run = "${timestamp()}" }
  depends_on = [null_resource.allow_file_copy_to_start]

  provisioner "local-exec" {
    quiet       = false # let stage markers stream to terraform output
    command     = <<-EOT
      set -e

      # --- Phase 1: SSH connectivity probe ---
      echo "==== STAGE START: ssh_probe ===="
      mkdir -p ${path.module}/.ssh-control && chmod 700 ${path.module}/.ssh-control
      counter=0
      until ssh -T ${var.app_name} || [ $counter -gt 60 ]; do
        echo "[$(date)] Waiting for SSH connection to be available."
        sleep 5
        counter=$((counter+5))
      done

      # cloud-init adds ec2-user to the `docker` group (launch_template_ec2.tpl). Wait for it to
      # finish (max 10 min), then close the ControlMaster so the next SSH session picks up the group.
      # `cloud-init status` exit codes: 0 = done, 2 = done with non-fatal warnings, 124 = timeout.
      ssh -T ${var.app_name} '
        timeout 600 cloud-init status --wait > /dev/null; rc=$?
        if [ $rc -ne 0 ] && [ $rc -ne 2 ]; then
          echo "cloud-init did not finish cleanly (exit=$rc)"; cloud-init status --long; exit 1
        fi'
      ssh -O exit ${var.app_name} 2>/dev/null || true
      echo "==== STAGE OK:    ssh_probe ===="

      # --- Phase 2: File transfer ---
      echo "==== STAGE START: file_transfer ===="
      ssh -T ${var.app_name} 'cd /home/ec2-user && rm -rf target || true'
      scp -r assets/target ${var.app_name}:/home/ec2-user/target
      echo "==== STAGE OK:    file_transfer ===="

      # --- Phase 3: Remote orchestrator ---
      echo "==== STAGE START: remote_orchestrator ===="
      ssh -T ${var.app_name} 'RUN_SEQERAKIT=${var.flag_run_seqerakit} bash /home/ec2-user/target/bash/remote/orchestrate.sh'
      echo "==== STAGE OK:    remote_orchestrator ===="
    EOT
    interpreter = ["/bin/bash", "-c"]
  }
}
