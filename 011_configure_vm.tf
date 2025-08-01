/* NOTE
July 28/25: This was originally a monolithic resource, with all Bash commands stored within for convenience.

While useful from an administrative view, had coarse runtime granularity -- you could not easily see 
what command was executing and stack traces from failed executions.

Accepting repetitive boilerplate in return for finer granularity and more visibility.
*/

## ------------------------------------------------------------------------------------
## SSH Connectivity Check
## ------------------------------------------------------------------------------------
resource "null_resource" "ssh_connectivity_check" {
  count = var.flag_vm_copy_files_to_instance == true ? 1 : 0

  triggers   = { always_run = "${timestamp()}" }
  depends_on = [null_resource.allow_file_copy_to_start]

  provisioner "local-exec" {
    command     = <<-EOT
      set -e
      echo "[$(date)] Starting SSH connectivity check for ${var.app_name}"
      
      counter=0
      until ssh ${var.app_name} || [ $counter -gt 60 ]; do
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
## File Transfer
## ------------------------------------------------------------------------------------
resource "null_resource" "file_transfer" {
  count = var.flag_vm_copy_files_to_instance == true ? 1 : 0

  triggers   = { always_run = "${timestamp()}" }
  depends_on = [null_resource.ssh_connectivity_check]

  provisioner "local-exec" {
    command     = <<-EOT
      set -e
      echo "[$(date)] Starting file transfer to ${var.app_name}"
      echo "[$(date)] Purging old target folder on remote VM"
      ssh ${var.app_name} 'cd /home/ec2-user && rm -rf target || true'

      echo "[$(date)] Transferring new target folder"
      scp -r assets/target ${var.app_name}:/home/ec2-user/target
      echo "[$(date)] File transfer completed successfully"
    EOT
    interpreter = ["/bin/bash", "-c"]
  }
}

## ------------------------------------------------------------------------------------
## Host Configuration
## ------------------------------------------------------------------------------------
resource "null_resource" "host_configuration" {
  count = var.flag_vm_copy_files_to_instance == true ? 1 : 0

  triggers   = { always_run = "${timestamp()}" }
  depends_on = [null_resource.file_transfer]

  provisioner "local-exec" {
    command     = <<-EOT
      set -e
      echo "[$(date)] Starting host configuration for ${var.app_name}"
      ssh ${var.app_name} '/bin/bash /home/ec2-user/target/bash/remote/cleanse_and_configure_host.sh'
      echo "[$(date)] Host configuration completed successfully"
    EOT
    interpreter = ["/bin/bash", "-c"]
  }
}

## ------------------------------------------------------------------------------------
## Ansible Setup
## ------------------------------------------------------------------------------------
resource "null_resource" "ansible_setup" {
  count = var.flag_vm_copy_files_to_instance == true ? 1 : 0

  triggers   = { always_run = "${timestamp()}" }
  depends_on = [null_resource.host_configuration]

  provisioner "local-exec" {
    command     = <<-EOT
      set -e
      echo "[$(date)] Waiting for Ansible to be ready on ${var.app_name}"
      ssh ${var.app_name} 'cd ${local.playbook_dir} && chmod u+x 00_wait_for_ansible.sh && ./00_wait_for_ansible.sh'
      echo "[$(date)] Ansible setup completed successfully"
    EOT
    interpreter = ["/bin/bash", "-c"]
  }
}

## ------------------------------------------------------------------------------------
## System Packages Installation
## ------------------------------------------------------------------------------------
resource "null_resource" "system_packages" {
  count = var.flag_vm_copy_files_to_instance == true ? 1 : 0

  triggers   = { always_run = "${timestamp()}" }
  depends_on = [null_resource.ansible_setup]

  provisioner "local-exec" {
    command     = <<-EOT
      set -e
      echo "[$(date)] Loading System Packages on ${var.app_name}"
      ssh ${var.app_name} 'set -e && cd ${local.playbook_dir} && ansible-playbook -i inventory.ini 01_load_system_packages.yml'
      echo "[$(date)] System packages installation completed successfully"
    EOT
    interpreter = ["/bin/bash", "-c"]
  }
}

## ------------------------------------------------------------------------------------
## Update Configuration Files
## ------------------------------------------------------------------------------------
resource "null_resource" "update_configuration_files" {
  count = var.flag_vm_copy_files_to_instance == true ? 1 : 0

  triggers   = { always_run = "${timestamp()}" }
  depends_on = [null_resource.system_packages]

  provisioner "local-exec" {
    command     = <<-EOT
      set -e
      echo "[$(date)] Updating Configuration Files on ${var.app_name}"
      ssh ${var.app_name} 'cd ${local.playbook_dir} && ansible-playbook -i inventory.ini  02_update_file_configurations.yml'
      echo "[$(date)] Configuration files updated successfully"
    EOT
    interpreter = ["/bin/bash", "-c"]
  }
}

## ------------------------------------------------------------------------------------
## Pull Containers and Run Tower
## ------------------------------------------------------------------------------------
resource "null_resource" "pull_containers_run_tower" {
  count = var.flag_vm_copy_files_to_instance == true ? 1 : 0

  triggers   = { always_run = "${timestamp()}" }
  depends_on = [null_resource.update_configuration_files]

  provisioner "local-exec" {
    command     = <<-EOT
      set -e
      echo "[$(date)] Pulling containers and running Tower on ${var.app_name}"
      ssh ${var.app_name} 'cd ${local.playbook_dir} && ansible-playbook -i inventory.ini 03_pull_containers_and_run_tower.yml'
      echo "[$(date)] Containers pulled and Tower started successfully"
    EOT
    interpreter = ["/bin/bash", "-c"]
  }
}

## ------------------------------------------------------------------------------------
## Wait for Tower Containers
## ------------------------------------------------------------------------------------
resource "null_resource" "wait_for_tower" {
  count = var.flag_vm_copy_files_to_instance == true ? 1 : 0

  triggers   = { always_run = "${timestamp()}" }
  depends_on = [null_resource.pull_containers_run_tower]

  provisioner "local-exec" {
    command     = <<-EOT
      set -e
      echo "[$(date)] Waiting for Tower containers to be ready on ${var.app_name}"
      ssh ${var.app_name} 'cd ${local.playbook_dir} && ansible-playbook -i inventory.ini 04_wait_for_tower.yml'
      echo "[$(date)] Tower containers are ready successfully"
    EOT
    interpreter = ["/bin/bash", "-c"]
  }
}

## ------------------------------------------------------------------------------------
## Patch Groundswell
## ------------------------------------------------------------------------------------
resource "null_resource" "patch_groundswell" {
  count = var.flag_vm_copy_files_to_instance == true ? 1 : 0

  triggers   = { always_run = "${timestamp()}" }
  depends_on = [null_resource.wait_for_tower]

  provisioner "local-exec" {
    command     = <<-EOT
      set -e
      echo "[$(date)] Patching Groundswell (if necessary) on ${var.app_name}"
      ssh ${var.app_name} 'cd ${local.playbook_dir} && ansible-playbook -i inventory.ini  05_patch_groundswell.yml'
      echo "[$(date)] Groundswell patching completed successfully"
    EOT
    interpreter = ["/bin/bash", "-c"]
  }
}


## ------------------------------------------------------------------------------------
## Run Seqerakit (if allowed)
## ------------------------------------------------------------------------------------
resource "null_resource" "run_seqerkit" {
  count = var.flag_vm_copy_files_to_instance == true && var.flag_run_seqerakit == true ? 1 : 0

  triggers   = { always_run = "${timestamp()}" }
  depends_on = [null_resource.patch_groundswell]

  provisioner "local-exec" {
    command     = <<-EOT

      set -e

      echo "Running Seqerakit"
      ssh ${var.app_name} 'cd ${local.playbook_dir} && ansible-playbook -i inventory.ini  06_run_seqerakit.yml'

    EOT
    interpreter = ["/bin/bash", "-c"]
  }
}
