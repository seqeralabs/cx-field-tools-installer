## ------------------------------------------------------------------------------------
## Create all templated files
## Note: Must use `null_resource` instead of `local_file` because `local_file generates
##       files every-other-time (due to state checking PRIOR to deletion)
## ------------------------------------------------------------------------------------
resource "null_resource" "regenerate_config_files_from_data" {

  # depends_on          = [ null_resource.purge_and_clone_local_target_folder ]
  depends_on          = [ aws_ec2_instance_connect_endpoint.example ]
  triggers            = { always_run = "${timestamp()}" }

  provisioner "local-exec" {
    working_dir       = "${path.module}"
    command           = <<-EOT

      set -e

      # Purge local folder before recreating
      ${path.module}/assets/src/bash/local/purge_local_target.sh

      # Generate Tower config files
      echo '${data.template_file.tower_env.rendered}' > ${path.module}/assets/target/tower_config/tower.env
      echo '${data.template_file.tower_yml.rendered}' > ${path.module}/assets/target/tower_config/tower.yml
      echo '${data.template_file.tower_sql.rendered}' > ${path.module}/assets/target/tower_config/tower.sql

      # Generate Groundswell config files
      echo '${data.template_file.groundswell_env.rendered}' > ${path.module}/assets/target/groundswell_config/groundswell.env
      echo '${data.template_file.groundswell_sql.rendered}' > ${path.module}/assets/target/groundswell_config/groundswell.sql

      # Generate docker-compose files
      echo '${data.template_file.docker_compose.rendered}' > ${path.module}/assets/target/docker_compose/docker-compose.yml

      # Generate Seqerakit
      echo '${data.template_file.seqerakit_yml.rendered}' > ${path.module}/assets/target/seqerakit/setup.yml

      # Generate Bash files for remote execution
      echo '${data.template_file.cleanse_and_configure_host.rendered}' > ${path.module}/assets/target/bash/remote/cleanse_and_configure_host.sh

      # Generate Ansible files
      echo '${data.template_file.ansible_02_update_file_configurations.rendered}' > ${path.module}/assets/target/ansible/02_update_file_configurations.yml
      echo '${data.template_file.ansible_03_pull_containers_and_run_tower.rendered}' > ${path.module}/assets/target/ansible/03_pull_containers_and_run_tower.yml
      echo '${data.template_file.ansible_05_run_seqerakit.rendered}' > ${path.module}/assets/target/ansible/05_run_seqerakit.yml

      # Generate SSH_Config
      echo '${data.template_file.ssh_config.rendered}' > ${path.module}/ssh_config
      
    EOT
    interpreter       = ["/bin/bash", "-c"]
  }
}


## ------------------------------------------------------------------------------------
## Seqerakit - Compute Environments
##   NOTE: This part messy. 
##         Generation is conditional and I append the CEs to the setup.yml. 
##         Use count and local shell rather than local_file resource.
## ------------------------------------------------------------------------------------
resource "null_resource" "aws_batch_manual" {
  count               = var.seqerakit_aws_use_forge == false && var.seqerakit_aws_use_batch == true ? 1 : 0

  triggers            = { always_run = "${timestamp()}"  }
  depends_on          = [ null_resource.regenerate_config_files_from_data ]

  provisioner "local-exec" {
    command           = <<-EOT
      echo '${data.template_file.aws_batch_manual.rendered}' >> ${path.module}/assets/target/seqerakit/setup.yml
    EOT
    interpreter       = ["/bin/bash", "-c"]
  }
}


resource "null_resource" "aws_batch_forge" {
  count               = var.seqerakit_aws_use_forge == true && var.seqerakit_aws_use_batch == true ? 1 : 0

  triggers            = { always_run = "${timestamp()}"  }
  depends_on          = [ null_resource.regenerate_config_files_from_data ]

  provisioner "local-exec" {
    command           = <<-EOT
      echo '${data.template_file.aws_batch_forge.rendered}' >> ${path.module}/assets/target/seqerakit/setup.yml
    EOT
    interpreter       = ["/bin/bash", "-c"]
  }
}


## ------------------------------------------------------------------------------------
## Flag for file transfer to start
# -------------------------------------------------------------------------------------
resource "null_resource" "allow_file_copy_to_start" {
  triggers            = { always_run = "${timestamp()}"  }

  depends_on          = [ 
    null_resource.regenerate_config_files_from_data,
    null_resource.aws_batch_manual,
    null_resource.aws_batch_forge,
  ]
}