---
- hosts: localhost

  vars:
  become: yes
  become_user: root
  become_method: sudo

  tasks:
    - name: Placeholder for Groundswell Container Patching
      become: true
      become_user: ec2-user
      ansible.builtin.shell: |
        echo "This is placeholder step related to Groundswell container patching (if necessary)."

%{ if flag_enable_groundswell && flag_use_container_db  ~}
    - name: Patch groundswell in container db
      become: true
      become_user: ec2-user
      ansible.builtin.shell: |
        cd /home/ec2-user/target/ && source ~/.bashrc

        echo "Patching container db with groundswell init script."

        # If Groundswell is not enabled on first run, the swell db and user wont be created. 
        # Patch here in order to ensure it will always work.
        docker exec ec2-user-db-1 /bin/sh -c "mysql --user=root < /docker-entrypoint-initdb.d/init.sql"  || true
%{ endif ~}
