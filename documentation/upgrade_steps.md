# Upgrade Steps
Steps for existing implementations to follow when upgrading your current deployment to a new release (_current for Releases <= `1.6.1`_).


## Expected Filesystem Deployment
```bash
TODO: ADD diagram while doing real-world fix test
```


## Upgrade Cadence & Warning
When upgrading your Seqera Platform instance, please ensure you do not skip any [Major.Minor semantic versions](https://docs.seqera.io/changelog/tags/seqera-enterprise) (_only the largest patch version is generally required_).

If multiple jumps are needed to reach the most recent Seqera Platform release, your existing EBS volume may not be large enough to concurrently store all necessary image sets. In such cases, you will either need to:

1. SSH onto the host VM and purge no-longer-necessary image versions to ensure there is sufficient space for the next set.
2. Set the `ec2_root_volume_size` in `terraform.tfvars` to a larger size (_e.g. `16GB`_).


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
1. Run `terraform init -upgrade` to register new modules.
1. Run `terraform plan` and ensure no errors are thrown.
1. Run `terraform apply`.



