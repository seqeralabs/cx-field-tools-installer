# Prepare OpenSSH Config
This page provides instructions on how configure your SSH settings so that they solution can interact with the EC2 instance hosting your Seqera Platform instance.

During the installation process, a [SSH config file](https://man.openbsd.org/ssh_config) is created in the project folder and leveraged via the tooling to launch necessary SSH sessions.


## WARNING
Ordering is **really** important when it comes to SSH `Include` statements. Make sure this entry is at the very top.


## STEPS

1. Modify the `openssh` configuration on the machine where your Terraform project is located:

    ```bash
    # Add the following entry AT THE TOP of your ~/.ssh/config file
    Include /ABSOLUTE_PATH_TO_INSTALLER_PROJECT_ROOT/ssh_config

    # NOTE: IF you intend to run multiple instances on the same host (e.g. dev and staging), add an Include to each project folder.
    Include /ABSOLUTE_PATH_TO_INSTALLER_PROJECT_ROOT_DEV/ssh_config
    Include /ABSOLUTE_PATH_TO_INSTALLER_PROJECT_ROOT_STAGING/ssh_config
    ```
