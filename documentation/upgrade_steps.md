# Upgrade Steps
Steps for existing implementations to follow when upgrading your current deployment to a new release (_current for Releases <= `1.6.1`_).

## Expected Filesystem Deployment
```bash
TODO: ADD diagram while doing real-world fix test
```

## Steps
1. Back up your existing implementation's database prior to making any changes.
1. Download the new Release as a **peer folder** to your existing deployment.
1. Copy the following existing implementation assets into the new folder:
    1. Local Terraform state folder (_if state is stored locally_).
    1. Remote Terraform state configuration (_if state is stored remotely; settings defined at the top of `000_main.tf`).
    1. Your `terraform.tfvars` file.
1. [Update your `~/.ssh/config`](../documentation/setup/prepare_openssh.md) to point to the new release folder.
1. Update your `terraform.tfvars` & SSM secrets as per guidance in [CHANGELOG](../CHANGELOG.md#configuration-file-changes).
1. [OPTIONAL] Re-implement any customizations you've added to your current deployment.
1. Run `terraform plan` and ensure no errors are thrown.
1. Run `terraform apply`.



