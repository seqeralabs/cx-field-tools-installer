MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="//"

--//
Content-Type: text/cloud-config; charset="us-ascii"

#cloud-config
write_files:
  - path: /root/tower-forge.sh
    permissions: 0744
    owner: root
    content: |
      #!/usr/bin/env bash
      exec > >(tee /var/log/tower-forge.log|logger -t TowerForge -s 2>/dev/console) 2>&1

      ## Install packages
      yum update
      yum install -y nano ec2-instance-connect tree dnsutils traceroute

      # Amazon Linux 2023 already has Python3.9 so we just need to install Ansible:
      # https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html
      USER=/home/ec2-user
      cd /home/ec2-user

      counter=0
      while [ ! -f get-pip.py ] && [ $counter -lt 10 ]; do 
        echo "File not found, retrying download..."
        curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
        sleep 1
        counter=$((counter+1))
      done
      if [ $counter -eq 10 ]; then
        echo "Failed to download file after 10 attempts."
      fi

      python3 get-pip.py 
      python3 -m pip install ansible
      echo "$(ansible --version)"
      rm get-pip.py

runcmd:
  - bash /root/tower-forge.sh

--//--