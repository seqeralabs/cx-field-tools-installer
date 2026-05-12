---
- hosts: localhost

  vars:
  become: yes
  become_user: root
  become_method: sudo

  tasks:
  - name: Docker Compose Down
    become: true
    become_user: ec2-user
    community.docker.docker_compose_v2:
      project_src: /home/ec2-user/
      state: absent
      remove_orphans: true


  - name: Replace docker logging config & restart
    ansible.builtin.shell: |
      cd /home/ec2-user && source ~/.bashrc

      # Purge and replace existing logging configuration
      rm -f /etc/docker/daemon.json || true
      cp /home/ec2-user/target/docker_logging/daemon.json /etc/docker/daemon.json

      # Restart docker service to pick up change
      systemctl restart docker


  - name: Log in to Harbor
    become: true
    become_user: ec2-user
    ansible.builtin.shell: |
      cd /home/ec2-user && source ~/.bashrc

      # Retrieve creds and log int to cr.seqera.io
      export docker_user=$(aws ssm get-parameters --name "/seqera/${app_name}/scr-username" --with-decryption --query "Parameters[*].{Value:Value}" --output text)
      export docker_password=$(aws ssm get-parameters --name "/seqera/${app_name}/scr-password" --with-decryption --query "Parameters[*].{Value:Value}" --output text)

      echo $docker_password | docker login https://cr.seqera.io --username $docker_user --password-stdin


  - name: Docker Compose Up
    become: true
    become_user: ec2-user
    community.docker.docker_compose_v2:
      project_src: /home/ec2-user/
      state: present
