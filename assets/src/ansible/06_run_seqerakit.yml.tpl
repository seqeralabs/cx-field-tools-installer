---
- hosts: localhost

  vars:
  # Only run this if TF seqerakit flag set to true.
  become: yes
  become_user: root
  become_method: sudo

  tasks:
  - name: Get Tower PAT
    # Get PAT. URL used will vary depending on what was added to VM ~/.bashrc
    become: true
    become_user: ec2-user
    ansible.builtin.shell: |
      cd /home/ec2-user/target/python && source ~/.bashrc

      python3 get_access_token.py


  - name: Get secrets and install Tower objects
    become: true
    become_user: ec2-user
    ansible.builtin.shell: |
      cd /home/ec2-user/target/seqerakit && source ~/.bashrc

      # Some of these wont be present if not loaded into SSM secret.
      # This is handled by activation of flags in tfvars Seqerakit - Credentials section

      export SEQERAKIT_GITHUB_USER=$(aws ssm get-parameters --name "/seqera/${app_name}/seqerakit/github-user" --with-decryption --query "Parameters[*].{Value:Value}" --output text)
      export SEQERAKIT_GITHUB_TOKEN=$(aws ssm get-parameters --name "/seqera/${app_name}/seqerakit/github-token" --with-decryption --query "Parameters[*].{Value:Value}" --output text)
      export SEQERAKIT_DOCKER_USER=$(aws ssm get-parameters --name "/seqera/${app_name}/seqerakit/docker-user" --with-decryption --query "Parameters[*].{Value:Value}" --output text)
      export SEQERAKIT_DOCKER_PASSWORD=$(aws ssm get-parameters --name "/seqera/${app_name}/seqerakit/docker-token" --with-decryption --query "Parameters[*].{Value:Value}" --output text)
      export SEQERAKIT_AWS_ACCESS_KEY_ID=$(aws ssm get-parameters --name "/seqera/${app_name}/seqerakit/aws-user" --with-decryption --query "Parameters[*].{Value:Value}" --output text)
      export SEQERAKIT_AWS_SECRET_ACCESS_KEY=$(aws ssm get-parameters --name "/seqera/${app_name}/seqerakit/aws-password" --with-decryption --query "Parameters[*].{Value:Value}" --output text)
      export SEQERAKIT_AWS_ASSUME_ROLE_ARN=$(aws ssm get-parameters --name "/seqera/${app_name}/seqerakit/aws-role" --with-decryption --query "Parameters[*].{Value:Value}" --output text)

      if [[ "${seqerakit_flag_credential_create_codecommit}" == "true"]]; then
        export SEQERAKIT_CODECOMMIT_USER=$(aws ssm get-parameters --name "/seqera/${app_name}/seqerakit/codecommit-user" --with-decryption --query "Parameters[*].{Value:Value}" --output text)
        export SEQERAKIT_CODECOMMIT_PASSWORD=$(aws ssm get-parameters --name "/seqera/${app_name}/seqerakit/codecommit-password" --with-decryption --query "Parameters[*].{Value:Value}" --output text)
      fi


  - name: Standard deployment with a CodeCommit credential
    become: true
    become_user: ec2-user
    ansible.builtin.shell: |
      cd /home/ec2-user/target/seqerakit && source ~/.bashrc

      # Using true in both ifs because we do not want TF to fail if seqerakit fails.
      if [[ "${seqerakit_flag_credential_create_codecommit}" != "true"]]; then

        if [[ $SEQERAKIT_USE_HOSTS_FILE == "true" ]]; then
          export TOWER_API_ENDPOINT="http://localhost:8000/api"
          seqerakit setup.yml --cli="--insecure" || true

        elif [[ $CACERT_DO_NOT_USE_HTTPS == "true" ]]; then
          seqerakit setup.yml --cli="--insecure" || true

        else
          seqerakit setup.yml --cli="-Djavax.net.ssl.trustStore=/usr/lib/jvm/java-17-amazon-corretto/lib/security/cacerts" || true
        fi
      
      fi