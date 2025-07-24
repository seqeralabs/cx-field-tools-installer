## ------------------------------------------------------------------------------------
## Create all templated files
## Note: Must use `null_resource` instead of `local_file` because `local_file generates
##       files every-other-time (due to state checking PRIOR to deletion)
## ------------------------------------------------------------------------------------
resource "null_resource" "generate_independent_config_files" {

  triggers = { always_run = "${timestamp()}" }

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

      # Generate Wave config files
      echo '${local.wave_lite_yml}' > ${path.module}/assets/target/wave_lite_config/wave-lite.yml

      # THIS IS A TOTAL HACK (Wave-Lite)
      # Using this technique so postgres can get config files with single quotes only.
      # Terraform templatefile (.tpl) abandoned and we use real SQL with placeholders-to-be-replaced-by-sed
      # NOTE: sed works differently on GNU vs Mac. This was messy to managed so it was replaced with platform-agnostic Python solution.

      cp ${path.module}/assets/src/wave_lite_config/wave-lite-container-1.sql ${path.module}/assets/target/wave_lite_config/wave-lite-container-1.sql
      cp ${path.module}/assets/src/wave_lite_config/wave-lite-container-2.sql ${path.module}/assets/target/wave_lite_config/wave-lite-container-2.sql
      cp ${path.module}/assets/src/wave_lite_config/wave-lite-rds.sql ${path.module}/assets/target/wave_lite_config/wave-lite-rds.sql
      cp ${path.module}/assets/src/wave_lite_config/nginx.conf ${path.module}/assets/target/wave_lite_config/nginx.conf

      export SALT=${path.module}/scripts/installer/utils/sedalternative.py
      python3 $SALT replace_me_wave_lite_db_limited_user     ${local.wave_lite_secrets["WAVE_LITE_DB_LIMITED_USER"]["value"]}     ${path.module}/assets/target/wave_lite_config/wave-lite-container-1.sql
      python3 $SALT replace_me_wave_lite_db_limited_user     ${local.wave_lite_secrets["WAVE_LITE_DB_LIMITED_USER"]["value"]}     ${path.module}/assets/target/wave_lite_config/wave-lite-container-2.sql
      python3 $SALT replace_me_wave_lite_db_limited_user     ${local.wave_lite_secrets["WAVE_LITE_DB_LIMITED_USER"]["value"]}     ${path.module}/assets/target/wave_lite_config/wave-lite-rds.sql

      python3 $SALT replace_me_wave_lite_db_limited_password ${local.wave_lite_secrets["WAVE_LITE_DB_LIMITED_PASSWORD"]["value"]} ${path.module}/assets/target/wave_lite_config/wave-lite-container-1.sql
      python3 $SALT replace_me_wave_lite_db_limited_password ${local.wave_lite_secrets["WAVE_LITE_DB_LIMITED_PASSWORD"]["value"]} ${path.module}/assets/target/wave_lite_config/wave-lite-container-2.sql
      python3 $SALT replace_me_wave_lite_db_limited_password ${local.wave_lite_secrets["WAVE_LITE_DB_LIMITED_PASSWORD"]["value"]} ${path.module}/assets/target/wave_lite_config/wave-lite-rds.sql

      # Generate Groundswell config files
      echo '${local.groundswell_env}' > ${path.module}/assets/target/groundswell_config/groundswell.env
      echo '${local.groundswell_sql}' > ${path.module}/assets/target/groundswell_config/groundswell.sql

      # Generate docker-compose files
      echo '${local.docker_compose}' > ${path.module}/assets/target/docker_compose/docker-compose.yml

      # Generate Seqerakit
      echo '${local.seqerakit_yml}' > ${path.module}/assets/target/seqerakit/setup.yml

      # Generate Tower Connect files
      echo '${local.data_studios_env}' > ${path.module}/assets/target/tower_config/data-studios.env
      echo '${tls_private_key.connect_pem.private_key_pem}' > ${path.module}/assets/target/tower_config/data-studios-rsa.pem

      # Generate Docker Logging Configuration
      echo '${local.docker_logging}' > ${path.module}/assets/target/docker_logging/daemon.json

      # Generate Ansible files
      echo '${local.ansible_02_update_file_configurations}' > ${path.module}/assets/target/ansible/02_update_file_configurations.yml
      echo '${local.ansible_03_pull_containers_and_run_tower}' > ${path.module}/assets/target/ansible/03_pull_containers_and_run_tower.yml
      echo '${local.ansible_05_patch_groundswell}' > ${path.module}/assets/target/ansible/05_patch_groundswell.yml
      echo '${local.ansible_06_run_seqerakit}' > ${path.module}/assets/target/ansible/06_run_seqerakit.yml
      echo '${local.codecommit_seqerakit}' > ${path.module}/assets/target/bash/remote/codecommit_set_workspace_id.sh

      # Generate EC2 PEM
      echo "${tls_private_key.ec2_ssh_key.private_key_pem}" > ${path.module}/${local.ssh_key_name}
      chmod 400 ${path.module}/${local.ssh_key_name}

      # Generate Bash files for remote execution
      echo '${local.cleanse_and_configure_host}' > ${path.module}/assets/target/bash/remote/cleanse_and_configure_host.sh

      # Emit customized custom cert config
      echo '${local.private_ca_conf}' > ${path.module}/assets/target/customcerts/custom_default.conf

    EOT
  }
}

resource "null_resource" "generate_config_files_with_dependencies" {

  # depends_on          = [ null_resource.purge_and_clone_local_target_folder ]
  depends_on = [
    aws_ec2_instance_connect_endpoint.example,
    null_resource.generate_independent_config_files
  ]
  triggers = { always_run = "${timestamp()}" }

  provisioner "local-exec" {
    working_dir = path.module
    command     = <<-EOT

      set -e

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

  triggers = { always_run = "${timestamp()}" }
  depends_on = [
    null_resource.generate_config_files_with_dependencies,
    null_resource.generate_independent_config_files
  ]

  provisioner "local-exec" {
    command     = <<-EOT
      echo '${local.aws_batch_manual}' >> ${path.module}/assets/target/seqerakit/setup.yml
    EOT
    interpreter = ["/bin/bash", "-c"]
  }
}


resource "null_resource" "aws_batch_forge" {
  count = var.seqerakit_aws_use_forge == true && var.seqerakit_aws_use_batch == true ? 1 : 0

  triggers = { always_run = "${timestamp()}" }
  depends_on = [
    null_resource.generate_config_files_with_dependencies,
    null_resource.generate_independent_config_files
  ]

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
    null_resource.generate_independent_config_files,
    null_resource.generate_config_files_with_dependencies,
    null_resource.aws_batch_manual,
    null_resource.aws_batch_forge,
  ]
}
