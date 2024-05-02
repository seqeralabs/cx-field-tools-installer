---
- hosts: localhost

  vars:
  become: yes
  become_user: root
  become_method: sudo

  tasks:
  - name: Patch groundswell in container db
    become: true
    become_user: ec2-user
    ansible.builtin.shell: |
      cd /home/ec2-user && source ~/.bashrc

      # If Groundswell is not enabled on first run, the swell db and user wot be created. 
      # init.sql will only be present if Groundswell has been activated in config
      # "or true" conditional logic for n+1 groundswell deployments

      if [[ "${flag_enable_groundswell}" == true ]] && [[ "${flag_use_container_db}" == true ]]; then
        echo "Patching container db with groundswell init script."
        docker exec ec2-user-db-1 /bin/sh -c "mysql --user=root < /docker-entrypoint-initdb.d/init.sql"  || true
      fi