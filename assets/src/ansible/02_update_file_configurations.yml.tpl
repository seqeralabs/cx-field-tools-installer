---
- hosts: localhost

  vars:
  become: yes
  become_user: root
  become_method: sudo

  tasks:
  - name: Purge old files
    become: true
    become_user: ec2-user
    ansible.builtin.shell: |
      cd /home/ec2-user && source ~/.bashrc

      # Purge any testing files which are lingering.
      rm tower.yml || true
      rm tower.env || true
      rm groundswell.env || true
      rm docker-compose.yml || true
      rm data-studios.env || true

      # Generate fresh tower config files from upload package.
      cp target/tower_config/tower.yml tower.yml
      cp target/tower_config/tower.env tower.env
      cp target/tower_config/data-studios.env data-studios.env

      # Generate fresh groundswell config files from upload package.
      cp target/groundswell_config/groundswell.env groundswell.env

      # Generate proper docker-compose file
      cp target/docker_compose/docker-compose.yml docker-compose.yml

      # Chown files
      chown ec2-user:ec2-user tower.env
      chown ec2-user:ec2-user tower.yml
      chown ec2-user:ec2-user groundswell.env
      chown ec2-user:ec2-user docker-compose.yml
      chown ec2-user:ec2-user data-studios.env


  - name: Purge old files
    become: true
    become_user: ec2-user
    # TO DO: Remove this step when migration script can pull directly from SSM.
    # Consider abstracting the SSM prefixes to an environment variable for cleaner maintenance.
    ansible.builtin.shell: |
      cd /home/ec2-user && source ~/.bashrc

      export TOWER_DB_USER=$(aws ssm get-parameters --name "/config/${app_name}/datasources/default/username" --with-decryption --query "Parameters[*].{Value:Value}" --output text)
      export TOWER_DB_PASSWORD=$(aws ssm get-parameters --name "/config/${app_name}/datasources/default/password" --with-decryption --query "Parameters[*].{Value:Value}" --output text)

      echo "TOWER_DB_USER=$TOWER_DB_USER" >> tower.env
      echo "TOWER_DB_PASSWORD=$TOWER_DB_PASSWORD" >> tower.env


  - name: Populate RDS
    become: true
    become_user: ec2-user
    ansible.builtin.shell: |
      cd /home/ec2-user && source ~/.bashrc

      if [[ $DB_POPULATE_EXTERNAL_INSTANCE == true ]]; then
        echo "Populating external DB"

        export db_master_user=$(aws ssm get-parameters --name "/seqera/${app_name}/db-master-user" --with-decryption --query "Parameters[*].{Value:Value}" --output text)
        export db_master_password=$(aws ssm get-parameters --name "/seqera/${app_name}/db-master-password" --with-decryption --query "Parameters[*].{Value:Value}" --output text)

        mysql --host $DB_URL --port=3306 --user=$db_master_user --password=$db_master_password < target/tower_config/tower.sql  || true
      fi

  - name: Populate Groundswell
    become: true
    become_user: ec2-user
    # Handles both RDS or container
    ansible.builtin.shell: |
      cd /home/ec2-user && source ~/.bashrc

      if [[ $DB_POPULATE_EXTERNAL_INSTANCE == true ]]; then
        echo "Populating external DB with Groundswell"

        export db_master_user=$(aws ssm get-parameters --name "/seqera/${app_name}/db-master-user" --with-decryption --query "Parameters[*].{Value:Value}" --output text)
        export db_master_password=$(aws ssm get-parameters --name "/seqera/${app_name}/db-master-password" --with-decryption --query "Parameters[*].{Value:Value}" --output text)

        mysql --host $DB_URL --port=3306 --user=$db_master_user --password=$db_master_password < target/groundswell_config/groundswell.sql  || true
      fi

  - name: Generate PrivateCA artefacts if necessary
    become: true
    become_user: ec2-user
    # This step only runs if we need a private CA
    ansible.builtin.shell: |
      cd /home/ec2-user/target/customcerts && source ~/.bashrc

      if [[ $CACERT_GENERATE_PRIVATE == "true" ]]; then 

        echo "Generating Private CA cert"

        # Clean-up prior to regeneration
        rm *.crt || true
        rm *.csr || true
        rm *.key || true
        rm cert.conf  || true

        chmod u+x create_self_signed_cert.sh
        ./create_self_signed_cert.sh $TOWER_BASE_URL

        sleep 5

        # Write root cert out and push to S3 bucket for programmatic retrieval
        cat rootCA.crt >> "$TOWER_BASE_URL.crt"
        aws s3 cp rootCA.crt $CACERT_S3_PREFIX/rootCA.crt

      fi


  - name: Add custom cert to EC2 instance truststore if necessary (for tw use later)
    # Unix socket error for some reason
    become: true
    become_user: ec2-user
    ansible.builtin.shell: |
      cd /home/ec2-user/target/customcerts && source ~/.bashrc

      if [[ $CACERT_GENERATE_PRIVATE == "true" || $CACERT_USE_EXISTING_PRIVATE == "true" ]]; then

        echo "Adding custom cert to EC2 truststore"
        env | grep -i TOWER

        export crt=".crt"
        export tower_cert=$TOWER_BASE_URL$crt
        echo $tower_cert

        sudo keytool -import -trustcacerts -cacerts -storepass changeit -noprompt -alias TARGET_ALIAS -file $tower_cert
        sudo cp $tower_cert /etc/pki/ca-trust/source/anchors/$tower_cert
        sudo update-ca-trust

      fi


  - name: Patch docker-compose reverseproxy if custom cert being served up by instance.
    become: true
    become_user: ec2-user
    ansible.builtin.shell: |
      cd /home/ec2-user/target/customcerts && source ~/.bashrc

      if [[ $CACERT_GENERATE_PRIVATE == "true" ]]; then

        # New CA, use the domain name as the file name.

        export CACERT_NEW_CRT="$TOWER_BASE_URL.crt"
        export CACERT_NEW_KEY="$TOWER_BASE_URL.key"

        sed -i "s/REPLACE_TOWER_URL/$TOWER_BASE_URL/g" custom_default.conf
        sed -i "s/PLACEHOLDER_CRT/$CACERT_NEW_CRT/g" custom_default.conf
        sed -i "s/PLACEHOLDER_KEY/$CACERT_NEW_KEY/g" custom_default.conf

        sed -i "s/REPLACE_CUSTOM_CRT/$CACERT_NEW_CRT/g" /home/ec2-user/docker-compose.yml
        sed -i "s/REPLACE_CUSTOM_KEY/$CACERT_NEW_KEY/g" /home/ec2-user/docker-compose.yml

      fi


      if [[ $CACERT_USE_EXISTING_PRIVATE == "true" ]]; then

        # Using environment variables pushed to ~/.bashrc via Terraform

        sed -i "s/REPLACE_TOWER_URL/$TOWER_BASE_URL/g" custom_default.conf
        sed -i "s/PLACEHOLDER_CRT/$CACERT_EXISTING_CA_CRT/g" custom_default.conf
        sed -i "s/PLACEHOLDER_KEY/$CACERT_EXISTING_CA_KEY/g" custom_default.conf

        sed -i "s/REPLACE_CUSTOM_CRT/$CACERT_EXISTING_CA_CRT/g" /home/ec2-user/docker-compose.yml
        sed -i "s/REPLACE_CUSTOM_KEY/$CACERT_EXISTING_CA_KEY/g" /home/ec2-user/docker-compose.yml

      fi


  - name: Update seqerakit prerun script to pull private cert if active.
    become: true
    become_user: ec2-user
    ansible.builtin.shell: |
      cd /home/ec2-user/target/seqerakit && source ~/.bashrc

      if [[ $CACERT_GENERATE_PRIVATE == "true" || $CACERT_USE_EXISTING_PRIVATE == "true" ]]; then

        # Update the seqerakit pre-run script to pull the cert from the server
        # https://help.tower.nf/23.2/enterprise/configuration/ssl_tls/
        # Note: This approach works for most clients but there can be occasional problems due to chains.

        {
          echo -e "\n"

          echo "keytool -printcert -rfc -sslserver $TOWER_BASE_URL:443  >  /PRIVATE_CERT.pem"
          echo "keytool -import -trustcacerts -cacerts -storepass changeit -noprompt -alias TARGET_ALIAS -file /PRIVATE_CERT.pem"
          echo "cp /PRIVATE_CERT.pem /etc/pki/ca-trust/source/anchors/PRIVATE_CERT.pem"
          echo "update-ca-trust"

        } >> pipelines/pre_run.txt

      fi

  - name: Switch primary group to docker to avoid need to logout.
    # https://stackoverflow.com/questions/49434650/how-to-add-a-user-to-a-group-without-logout-login-bash-script
    become: true
    become_user: ec2-user
    ansible.builtin.shell: |
      newgrp docker


  - name: Reinstall Ansible community docker package
    become: true
    become_user: ec2-user
    # Force reinstall the docker.community plugin since Ansible complains if we dont.
    # Cant be in the 03-series because Ansible will complain about the docker_compose_v2 modules when only 3.4.11 is present.
    ansible.builtin.shell: |
      cd /home/ec2-user && source ~/.bashrc

      ansible-galaxy collection install community.docker:==3.7.0