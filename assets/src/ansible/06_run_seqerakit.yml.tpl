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

# In the event of any future instances of not-yet-natively-supported Seqera Platform objects (not supported by tw cli), a secondary task can be created as a workaround.
# Example of supporting codecommit creds before tw cli support in commit [9c3f961] (https://github.com/seqeralabs/cx-field-tools-installer/pull/117/commits/9c3f961fd989e083bdafde3df25d6087ae486a98)

  - name: Standard deployment
    become: true
    become_user: ec2-user
    ansible.builtin.shell: |
      cd /home/ec2-user/target/seqerakit && source ~/.bashrc

      # NOTE: Repetition happens because env vars wont pass between steps.
      # Some of these wont be present if not loaded into SSM secret.
      # This is handled by activation of flags in tfvars Seqerakit - Credentials section

      export SEQERAKIT_GITHUB_USER=$(aws ssm get-parameters --name "/seqera/${app_name}/seqerakit/github-user" --with-decryption --query "Parameters[*].{Value:Value}" --output text)
      export SEQERAKIT_GITHUB_TOKEN=$(aws ssm get-parameters --name "/seqera/${app_name}/seqerakit/github-token" --with-decryption --query "Parameters[*].{Value:Value}" --output text)
      export SEQERAKIT_DOCKER_USER=$(aws ssm get-parameters --name "/seqera/${app_name}/seqerakit/docker-user" --with-decryption --query "Parameters[*].{Value:Value}" --output text)
      export SEQERAKIT_DOCKER_PASSWORD=$(aws ssm get-parameters --name "/seqera/${app_name}/seqerakit/docker-token" --with-decryption --query "Parameters[*].{Value:Value}" --output text)
      export SEQERAKIT_AWS_ACCESS_KEY_ID=$(aws ssm get-parameters --name "/seqera/${app_name}/seqerakit/aws-user" --with-decryption --query "Parameters[*].{Value:Value}" --output text)
      export SEQERAKIT_AWS_SECRET_ACCESS_KEY=$(aws ssm get-parameters --name "/seqera/${app_name}/seqerakit/aws-password" --with-decryption --query "Parameters[*].{Value:Value}" --output text)
      export SEQERAKIT_AWS_ASSUME_ROLE_ARN=$(aws ssm get-parameters --name "/seqera/${app_name}/seqerakit/aws-role" --with-decryption --query "Parameters[*].{Value:Value}" --output text)
      export TOWER_CODECOMMIT_USER=$(aws ssm get-parameters --name "/seqera/${app_name}/seqerakit/codecommit-user" --with-decryption --query "Parameters[*].{Value:Value}" --output text)
      export TOWER_CODECOMMIT_PASSWORD=$(aws ssm get-parameters --name "/seqera/${app_name}/seqerakit/codecommit-password" --with-decryption --query "Parameters[*].{Value:Value}" --output text)
      export TOWER_CODECOMMIT_BASEURL=$(aws ssm get-parameters --name "/seqera/${app_name}/seqerakit/codecommit-baseurl" --with-decryption --query "Parameters[*].{Value:Value}" --output text)


      # Using true in both ifs because we do not want TF to fail if seqerakit fails.
%{ if flag_create_hosts_file_entry ~}
      echo "Seqerakit - Using hosts file."
      export TOWER_API_ENDPOINT="http://localhost:8000/api"
      seqerakit setup.yml --cli="--insecure" || true
%{ endif ~}

%{ if flag_do_not_use_https ~}
      echo "Seqerakit - Using insecure."
      seqerakit setup.yml --cli="--insecure" || true
%{ endif ~}

%{ if !flag_create_hosts_file_entry && !flag_do_not_use_https}
      # This is used by default if the other two edgecases arent true.
      echo "Seqerakit - Using truststore."
      seqerakit setup.yml --cli="-Djavax.net.ssl.trustStore=/usr/lib/jvm/java-17-amazon-corretto/lib/security/cacerts" || true
%{ endif ~}
