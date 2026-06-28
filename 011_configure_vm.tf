/* NOTE
June 28/26: Re-monolithised the mid-pipeline stages back into a single null_resource
that delegates to `assets/src/bash/remote/orchestrate.sh` on the host. The orchestrator
wraps each stage in bracketed log markers (STAGE START / OK / FAILED), so failure
attribution survives despite the collapse — the original reason for atomising into
8 null_resources is now solved at the script level instead of the Terraform level.

The first two null_resources (ssh_connectivity_check, file_transfer) remain as
separate Terraform-side steps: they're local-side prerequisites that can't be folded
into a remote orchestrator (the orchestrator script doesn't exist on the host until
file_transfer completes).

See https://github.com/seqeralabs/cx-field-tools-installer/issues/410.

Historical note (July 28/25): the original monolithic resource was split into 10
sequential null_resources to improve failure attribution. That trade-off is now
unnecessary because orchestrate.sh emits structured stage markers — see the
on-host log at /home/ec2-user/tower-installer-logs/apply-*.log for forensics.
*/

## ------------------------------------------------------------------------------------
## SSH Connectivity Check (local-side prerequisite)
## ------------------------------------------------------------------------------------
resource "null_resource" "ssh_connectivity_check" {
  count = var.flag_vm_copy_files_to_instance == true ? 1 : 0

  triggers   = { always_run = "${timestamp()}" }
  depends_on = [null_resource.allow_file_copy_to_start]

  provisioner "local-exec" {
    quiet       = true
    command     = <<-EOT
      set -e

      echo "[$(date)] Ensuring .ssh-control folder exists."
      mkdir -p ${path.module}/.ssh-control && chmod 700 ${path.module}/.ssh-control

      echo "[$(date)] Starting SSH connectivity check for ${var.app_name}"
      counter=0
      until ssh -T ${var.app_name} || [ $counter -gt 60 ]; do
        echo "[$(date)] Waiting for SSH connection to be available."
        sleep 5
        counter=$((counter+5))
      done

      echo "[$(date)] SSH connectivity established successfully"
    EOT
    interpreter = ["/bin/bash", "-c"]
  }
}

## ------------------------------------------------------------------------------------
## File Transfer (local-side prerequisite — ships assets/target/ including orchestrate.sh)
## ------------------------------------------------------------------------------------
resource "null_resource" "file_transfer" {
  count = var.flag_vm_copy_files_to_instance == true ? 1 : 0

  triggers   = { always_run = "${timestamp()}" }
  depends_on = [null_resource.ssh_connectivity_check]

  provisioner "local-exec" {
    quiet       = true
    command     = <<-EOT
      set -e
      echo "[$(date)] Starting file transfer to ${var.app_name}"
      echo "[$(date)] Purging old target folder on remote VM"
      ssh -T ${var.app_name} 'cd /home/ec2-user && rm -rf target || true'

      echo "[$(date)] Transferring new target folder"
      scp -r assets/target ${var.app_name}:/home/ec2-user/target
      echo "[$(date)] File transfer completed successfully"
    EOT
    interpreter = ["/bin/bash", "-c"]
  }
}

## ------------------------------------------------------------------------------------
## Configure VM — single remote orchestrator step
##
## Replaces the previous chain of host_configuration, ansible_setup, system_packages,
## update_configuration_files, pull_containers_run_tower, wait_for_tower,
## patch_groundswell, run_seqerkit.
##
## The remote orchestrate.sh script prints per-stage markers to stdout and to a
## persistent log file at /home/ec2-user/tower-installer-logs/apply-<UTC>.log. If a
## stage fails, the last "STAGE FAILED" line names the failing stage and exit code.
## ------------------------------------------------------------------------------------
resource "null_resource" "configure_vm" {
  count = var.flag_vm_copy_files_to_instance == true ? 1 : 0

  triggers   = { always_run = "${timestamp()}" }
  depends_on = [null_resource.file_transfer]

  provisioner "local-exec" {
    quiet       = false # let orchestrate.sh's stage markers stream to terraform output
    command     = <<-EOT
      set -e
      echo "[$(date)] Invoking remote orchestrator on ${var.app_name}"
      ssh -T ${var.app_name} 'RUN_SEQERAKIT=${var.flag_run_seqerakit} bash /home/ec2-user/target/bash/remote/orchestrate.sh'
      echo "[$(date)] Remote orchestrator completed successfully"
    EOT
    interpreter = ["/bin/bash", "-c"]
  }
}
