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
      set -euo pipefail

      exec > >(tee /var/log/tower-forge.log|logger -t TowerForge -s 2>/dev/console) 2>&1

      # Pre-create docker group and add ec2-user before anything else so that
      # any SSH session — including the ControlMaster opened by Terraform's
      # provisioners — inherits the docker group at auth time. Docker (installed
      # later by Ansible) reuses the existing group. See issue #XYZ.
      groupadd -f docker
      usermod -aG docker ec2-user

      ## Install packages
      yum update -y
      yum install -y nano ec2-instance-connect tree dnsutils traceroute

      # Install pip via the system package manager.
      #
      # OLD: bootstrapped pip via `curl https://bootstrap.pypa.io/get-pip.py | python3`,
      # with a download-retry loop. Upstream `get-pip.py` now requires Python >= 3.10,
      # but Amazon Linux 2023 ships with Python 3.9 as the system default — the
      # bootstrap script aborts on that interpreter. `yum install -y python3-pip`
      # gives us a pip that tracks the system Python version and avoids the network
      # round-trip to bootstrap.pypa.io entirely.
      yum install -y python3-pip

      python3 -m pip install ansible-core
      echo "$(ansible --version)"

runcmd:
  - bash /root/tower-forge.sh

--//--
