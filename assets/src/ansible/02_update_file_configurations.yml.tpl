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
        rm data-studios-rsa.pem || true

        # Generate fresh tower config files from upload package.
        cp target/tower_config/tower.yml tower.yml
        cp target/tower_config/tower.env tower.env

        # Move data-studios file (if applicable)
        cp target/tower_config/data-studios.env data-studios.env
        cp target/tower_config/data-studios-rsa.pem data-studios-rsa.pem

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
        chown ec2-user:ec2-user data-studios-rsa.pem

    - name: Populate SP env file with DB connection variables.
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

          # https://unix.stackexchange.com/questions/205180/how-to-pass-password-to-mysql-command-line
          docker run --rm -t -v $(pwd)/target/tower_config/tower.sql:/tower.sql -e \
          MYSQL_PWD=$db_master_password --entrypoint /bin/bash mysql:8.0 \
          -c "mysql --host $DB_URL --port=3306 --user=$db_master_user < tower.sql" || true

        fi

    - name: Populate Wave Lite Postgres
      become: true
      become_user: ec2-user
      ansible.builtin.shell: |
        cd /home/ec2-user && source ~/.bashrc

        if [[ $WAVE_LITE_ACTIVATED == true && $DB_POPULATE_EXTERNAL_INSTANCE == true ]]; then
          echo "Populating Wave Lite Postgres"

          export wave_lite_master_user=$(aws ssm get-parameters --name "/seqera/${app_name}/wave-lite/db-master-user" --with-decryption --query "Parameters[*].{Value:Value}" --output text)
          export wave_lite_master_password=$(aws ssm get-parameters --name "/seqera/${app_name}/wave-lite/db-master-password" --with-decryption --query "Parameters[*].{Value:Value}" --output text)

          docker run --rm -t -v $(pwd)/target/wave_lite_config/wave-lite-rds.sql:/tmp/wave.sql -e \
          POSTGRES_PASSWORD=$wave_lite_master_password --entrypoint /bin/bash postgres:latest \
          -c "PGPASSWORD=$wave_lite_master_password psql -h $WAVE_LITE_DB_URL -p 5432 -U $wave_lite_master_user -d postgres < /tmp/wave.sql"

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

          docker run --rm -t -v $(pwd)/target/groundswell_config/groundswell.sql:/groundswell.sql -e \
          MYSQL_PWD=$db_master_password --entrypoint /bin/bash mysql:8.0 \
          -c "mysql --host $DB_URL --port=3306 --user=$db_master_user < groundswell.sql" || true

        fi

    - name: Update entities dependent on private CA cert
      become: true
      become_user: ec2-user
      ansible.builtin.shell: |
        # Pull pre-loaded certificates from S3 Bucket and stash in necessary locations.
        # Only do so if rootCA.crt is not yet present in trust anchors

        if [[ $CACERT_PRIVATE_ACTIVE == true ]]; then

          if [[ ! -f "/etc/pki/ca-trust/source/anchors/rootCA.crt" ]]; then

            # Add root CA cert to EC2 instance truststore. 
            # ASSUMPTION -- Root CA cert (new or existing) is called rootCA.crt
            cd /tmp
            aws s3 cp ${bucket_prefix_for_new_private_ca_cert}/rootCA.crt .
            
            sudo keytool -import -trustcacerts -cacerts -storepass changeit -noprompt -alias TARGET_ALIAS -file rootCA.crt
            sudo cp rootCA.crt /etc/pki/ca-trust/source/anchors/
            sudo update-ca-trust

            rm rootCA.crt
          fi

          # Grab leaf cert and stash in target/ folder
          cd /home/ec2-user/target/customcerts
          aws s3 cp ${bucket_prefix_for_new_private_ca_cert}/${tower_base_url}.crt ${tower_base_url}.crt 
          aws s3 cp ${bucket_prefix_for_new_private_ca_cert}/${tower_base_url}.key ${tower_base_url}.key

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

    - name: Create Studio 0.8.2 data folder.
      become: true
      become_user: ec2-user
      # DEPENDENCY: July 22/25 -- remove when fixed upstream in Studios in a later release.
      ansible.builtin.shell: |
        mkdir -p /home/ec2-user/.tower/connect
        sudo chmod 777 /home/ec2-user/.tower/connect
