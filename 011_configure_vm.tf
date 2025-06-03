## ------------------------------------------------------------------------------------
## File transfer (if allowed)
## ------------------------------------------------------------------------------------
resource "null_resource" "copy_files_to_vm" {
  count = var.flag_vm_copy_files_to_instance == true ? 1 : 0

  triggers   = { always_run = "${timestamp()}" }
  depends_on = [null_resource.allow_file_copy_to_start]

  provisioner "local-exec" {
    command     = <<-EOT

      set -e

      # SSH on host can be slow to initially respond. Attempt connection for 1 minute.
      counter=0
      until ssh ${var.app_name} || [ $counter -gt 60 ]; do
        echo "Waiting for SSH connection to be available."
        sleep 5
        counter=$((counter+5))
      done

      # On remote VM, purge old target folder & transfer new target folder
      ssh ${var.app_name} 'cd /home/ec2-user && rm -rf target || true'
      scp -r assets/target ${var.app_name}:/home/ec2-user/target

      # Once new target folder copied, replace all remaining Tower-related files.
      ssh ${var.app_name} '/bin/bash /home/ec2-user/target/bash/remote/cleanse_and_configure_host.sh'

      echo "Waiting for Ansible to be ready"
      ssh ${var.app_name} 'cd /home/ec2-user/target/ansible && chmod u+x 00_wait_for_ansible.sh && ./00_wait_for_ansible.sh'

      echo "Loading System Packages"
      ssh ${var.app_name} 'set -e && cd /home/ec2-user/target/ansible && ansible-playbook 01_load_system_packages.yml'

      echo "Updating Configuration Files"
      ssh ${var.app_name} 'cd /home/ec2-user/target/ansible && ansible-playbook 02_update_file_configurations.yml'

      echo "Pulling containers and running Tower"
      ssh ${var.app_name} 'cd /home/ec2-user/target/ansible && ansible-playbook 03_pull_containers_and_run_tower.yml'

      echo "Wait for Tower containers to be ready"
      ssh ${var.app_name} 'cd /home/ec2-user/target/ansible && ansible-playbook 04_wait_for_tower.yml'

      echo "Patching Groundswell (if necessary)"
      ssh ${var.app_name} 'cd /home/ec2-user/target/ansible && ansible-playbook 05_patch_groundswell.yml'

    EOT
    interpreter = ["/bin/bash", "-c"]
  }
}


## ------------------------------------------------------------------------------------
## Custom CA edge-case
## ------------------------------------------------------------------------------------
# If new private CA on VM, get generated CA cert back to local machine for local browser use.
resource "null_resource" "copy_private_ca_cert" {
  count = var.flag_generate_private_cacert == true ? 1 : 0

  triggers   = { always_run = "${timestamp()}" }
  depends_on = [null_resource.copy_files_to_vm]

  provisioner "local-exec" {
    command     = <<-EOT
      rm assets/target/customcerts/rootCA.crt || true
      aws s3 cp ${var.bucket_prefix_for_new_private_ca_cert}/rootCA.crt assets/target/customcerts/rootCA.crt || true
      chmod 777 assets/target/customcerts/rootCA.crt || true
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
  depends_on = [null_resource.copy_files_to_vm]

  provisioner "local-exec" {
    command     = <<-EOT

      set -e

      echo "Running Seqerakit"
      ssh ${var.app_name} 'cd /home/ec2-user/target/ansible && ansible-playbook 06_run_seqerakit.yml'

    EOT
    interpreter = ["/bin/bash", "-c"]
  }
}
