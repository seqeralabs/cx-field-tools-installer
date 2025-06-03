# Tool Dependencies

The CX Installer solution requires access to the following local tools to fulfill its functions:

1. Install `terraform v1.3.7` or later:
   - [https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)

2. Install and configure the latest `aws cli` (version 2):
   - [https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

3. Install a modern version of `openssh`:
    - [https://www.openssh.com/](https://www.openssh.com/)

4. Install `git v2.25.1` or later.

5. Install `GNU Make 4.2.1` or later.

6. Install `python 3.8.10` or later.

7. **(New as of May 21, 2025)** Install a container runtime capable of running Docker containers (_e.g. [Docker Engine](https://docs.docker.com/engine/install/ubuntu/)). NOTE: If you install a non-docker option like Podman, please ensure it is aliased the `docker` keyword.
