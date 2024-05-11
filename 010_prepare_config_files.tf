## ------------------------------------------------------------------------------------
## Create all templated files
## Note: Must use `null_resource` instead of `local_file` because `local_file generates
##       files every-other-time (due to state checking PRIOR to deletion)
## ------------------------------------------------------------------------------------
resource "null_resource" "regenerate_config_files_from_data" {

  # depends_on          = [ null_resource.purge_and_clone_local_target_folder ]
  depends_on = [aws_ec2_instance_connect_endpoint.example]
  triggers   = { always_run = "${timestamp()}" }

  provisioner "local-exec" {
    working_dir = path.module
    command     = <<-EOT

      set -e

      # Purge local folder before recreating
      ${path.module}/assets/src/bash/local/purge_local_target.sh

      # Generate Tower config files
      echo '${local.tower_env}' > ${path.module}/assets/target/tower_config/tower.env
      echo '${local.tower_yml}' > ${path.module}/assets/target/tower_config/tower.yml
      echo '${local.tower_sql}' > ${path.module}/assets/target/tower_config/tower.sql

      # Generate Groundswell config files
      echo '${local.groundswell_env}' > ${path.module}/assets/target/groundswell_config/groundswell.env
      echo '${local.groundswell_sql}' > ${path.module}/assets/target/groundswell_config/groundswell.sql

      # Generate docker-compose files
      echo '${local.docker_compose}' > ${path.module}/assets/target/docker_compose/docker-compose.yml

      # Generate Seqerakit
      echo '${local.seqerakit_yml}' > ${path.module}/assets/target/seqerakit/setup.yml

      # Generate Bash files for remote execution
      echo '${local.cleanse_and_configure_host}' > ${path.module}/assets/target/bash/remote/cleanse_and_configure_host.sh

      # Generate Ansible files
      echo '${local.ansible_02_update_file_configurations}' > ${path.module}/assets/target/ansible/02_update_file_configurations.yml
      echo '${local.ansible_03_pull_containers_and_run_tower}' > ${path.module}/assets/target/ansible/03_pull_containers_and_run_tower.yml
      echo '${local.ansible_05_patch_groundswell}' > ${path.module}/assets/target/ansible/05_patch_groundswell.yml
      echo '${local.ansible_06_run_seqerakit}' > ${path.module}/assets/target/ansible/06_run_seqerakit.yml
      echo '${local.codecommit_seqerakit}' > ${path.module}/assets/target/bash/remote/codecommit_set_workspace_id.sh

      # Generate SSH_Config
      echo '${local.ssh_config}' > ${path.module}/ssh_config
      chmod 644 ${path.module}/ssh_config

    EOT
    interpreter = ["/bin/bash", "-c"]
  }
}


## ------------------------------------------------------------------------------------
## Seqerakit - Compute Environments
##   NOTE: This part messy.
##         Generation is conditional and I append the CEs to the setup.yml.
##         Use count and local shell rather than local_file resource.
## ------------------------------------------------------------------------------------
resource "null_resource" "aws_batch_manual" {
  count = var.seqerakit_aws_use_forge == false && var.seqerakit_aws_use_batch == true ? 1 : 0

  triggers   = { always_run = "${timestamp()}" }
  depends_on = [null_resource.regenerate_config_files_from_data]

  provisioner "local-exec" {
    command     = <<-EOT
      echo '${local.aws_batch_manual}' >> ${path.module}/assets/target/seqerakit/setup.yml
    EOT
    interpreter = ["/bin/bash", "-c"]
  }
}


resource "null_resource" "aws_batch_forge" {
  count = var.seqerakit_aws_use_forge == true && var.seqerakit_aws_use_batch == true ? 1 : 0

  triggers   = { always_run = "${timestamp()}" }
  depends_on = [null_resource.regenerate_config_files_from_data]

  provisioner "local-exec" {
    command     = <<-EOT
      echo '${local.aws_batch_forge}' >> ${path.module}/assets/target/seqerakit/setup.yml
    EOT
    interpreter = ["/bin/bash", "-c"]
  }
}


## ------------------------------------------------------------------------------------
## Flag for file transfer to start
# -------------------------------------------------------------------------------------
resource "null_resource" "allow_file_copy_to_start" {
  triggers = { always_run = "${timestamp()}" }

  depends_on = [
    null_resource.regenerate_config_files_from_data,
    null_resource.aws_batch_manual,
    null_resource.aws_batch_forge,
  ]
}
