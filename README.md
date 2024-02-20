# Terraform Installer For Seqera Platform Enterprise (Docker-Compose)

To launch pipelines with Seqera Platform Enterprise, you first need to deploy a Platform instance. A successful deployment requires you to make decisions about networking, security posture, container orchestration, permissions, etc. These decisions can be overwhelming to a client administrator who just wants to get their users launching Nextflow pipelines from the platform. 

The Seqera CX team has developed a field tool to help simplify these initial efforts in two ways:

1. Reduce the infrastructure and configuration burden, so that a first-time deployment of Seqera Platform Enterprise requires less than 1 hour of work and only a few minutes for subsequent redeployments.

2. Provide an Infrastructure-As-Code (IaC) solution so activities are repeatable and artifacts can be checked into source-control.


## Disclaimer - Use at your own discretion!!

**This is an unofficial field tool.** 

The solution is delivered on a best-effort basis, but provides no guarantees of appropriateness for your specific scenario. Please conduct your due diligence prior to execution within your environment.

- Information about project structure, design decisions, and assumptions made can be found in [Design Decisions](documentation/design_decisions.md).
- Information on existing deficiencies and gotchas can be found in [Deficiencies & Gotchas](documentation/deficiencies_and_gotchas.md).



## Appropriateness criteria

The out-of-the-box solution depends on you meeting the following criteria: 

1. You are a client of Seqera Labs.
2. You will run Seqera Platform in AWS.
3. Your corporate policies allow you to store secrets in [AWS Systems Manager Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html) (SSM).
3. You have access to a local **Linux**-based terminal (_Mac supported, with caveats_).
4. You can use [Terraform](https://www.terraform.io/) to provision infrastructure.
5. You use OpenSSH and can maintain a `~/.ssh/config` file. 


## Tool dependencies

1. Install `terraform v1.3.7` or later:
   - [https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)

2. Install and configure the latest `aws cli` (version 2):
   - [https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

3. Install a modern version of `openssh`:
    - [https://www.openssh.com/](https://www.openssh.com/)


## Tool permissions

Please see [Permissions](documentation/permissions.md) for a full list of necessary AWS IAM permissions required to run the tool.


## Configuration steps

The tool relies on four core configuration files, all stored within the `templates` folder. These files must be prepared prior to project execution:

1. [`terraform.tfvars`](templates/TEMPLATE_terraform.tfvars)<br />Used to set flags and values that control how your infrastructure and the Seqera Platform Enterprise instance is built and configured.

    This file must be configured and stored in the project folder root.

2. [`ssm_sensitive_values_tower.json`](templates/ssm_sensitive_values_tower.json)<br />Used to define secrets like credentials and passwords which the Seqera Platform needs to fulfill its duties.

    This file exists to make SSM data population more convenient and **should not** be stored in source-control. 

3. [`ssm_sensitive_values_seqerakit.json`](templates/ssm_sensitive_values_seqerakit.json)  (Optional) <br />Used to define secrets like tokens and credentials which the [Seqerakit](https://github.com/seqeralabs/seqera-kit) tool needs to fulfill its duties.

    This file exists to make SSM data population more convenient and **should not** be stored in source-control. 

4. [`ssm_sensitive_values_groundswell.json`](templates/ssm_sensitive_values_groundswell.json)  (Optional) <br />Used to define credentials for the Groundswell optimization service.

    This file exists to make SSM data population more convenient and **should not** be stored in source-control. 


### Clone the repository

1. Download a copy of the repository to your local workstation:

    ```bash
    git clone <TODO_path_to_offical_repo> && cd <TODO_name_of_directory>
    ```

### Prepare secrets 

1. Select a name for your Seqera Platform application (default: `tower-dev`).
    
    This is a namespace isolator which prevents concurrent instances (_e.g., `dev` and `prod`_) from accidentally sharing configurations.

2. Modify the [`ssm_sensitive_values_tower.json`](templates/ssm_sensitive_values_tower.json) in the `templates` folder:

    1. Perform a find-and-replace on `tower-dev` if you select a different application name.

    2. Replace every instance of `CHANGE_ME` in the file with the values supplied to you during your Seqera onboarding.

    3. Replace every instance of `CHANGE_ME_SEE_SEQERA_DOCS` with your own values. Configuration value guidance can be found at [Seqera Platform Enterprise configuration](https://docs.seqera.io/platform/latest/enterprise/configuration/overview).

    4. Review each instance of `CHANGE_ME_IF_NECESSARY` and [replace as needed](https://docs.seqera.io/platform/latest/enterprise/configuration/authentication).

    **WARNING:** 
    1. Do not change `ssm_key` entries apart from the application name. Path changes will prevent the application from booting.
    2. SSM entries have a limit of 4096 characters. Very long client-supplied values may result in errors when you try to create the entry.

3. Modify the [`ssm_sensitive_values_seqerakit.json`](templates/ssm_sensitive_values_seqerakit.json) in the `templates` folder:

    1. Execute a find-and-replace on `tower-dev` if you select a different application name.

    2. Replace every instance of `CHANGE_ME` in the file with the [values appropriate for your organization](https://github.com/seqeralabs/nf-tower-aws).

    3. Review each instance of `CHANGE_ME_IF_NECESSARY` and [replace as needed]((https://docs.seqera.io/platform/23.3.0/credentials/overview)).

          An AWS credential set is a mandatory minimum. The `terraform.tfvars` file has flags that can enable/disable expectations regarding the AWS IAM role, Github credential, and Docker credential. 

        **WARNING:** 
        1. Do not change `ssm_key` entries apart from the application name. Path changes will prevent the application from booting.

4. Modify the [`ssm_sensitive_values_groundswell.json`](templates/ssm_sensitive_values_groundswell.json) in the `templates` folder:

    1. Execute a find-and-replace on `tower-dev` if you select a different application name.

    2. Replace default values if necessary.

5. Decide on the [AWS Parameter Store prefixes](https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-su-create.html) where you will store the payloads of your now-populated `ssm_*` files.

    Default values in `terraform.tfvars` are:
    - `/seqera/sensitive_values/tower_dev/tower`
    - `/seqera/sensitive_values/tower_dev/seqerakit`
    - `/seqera/sensitive_values/tower_dev/groundswell`

6. Create the entries and paste the appropriate JSON payload for each. Ensure that:

    1. **Type** is set to `SecureString`.
    2. **Data type** is `text`.


7. Remember your application name and SSM prefixes, as these need to be supplied during the configuration of the `terrform.tfvars` file.


### Prepare the `terraform.tfvars` file

**NOTE:** Fulsome field-level documentation exists inside the `terraform.tfvars` file. Consult there for details beyond the high-level instructions here.

1. Create a working copy of the [`terraform.tfvars`](templates/TEMPLATE_terraform.tfvars) file in the project root.

    ```bash
    # In project root
    cp templates/TEMPLATE_terraform.tfvars terraform.tfvars
    ```

2. Update the `app_name`, `secrets_bootstrap_tower`, `secrets_bootstrap_seqerakit`, and `secrets_bootstrap_groundswell` with the values you selected during the secrets preparation phase.

3. Replace every instance of `REPLACE_ME` with values appropriate for your organization.

4. Set `flag_*` variables to `true` / `false` to match your desired implementation architecture.

5. Review each instance of `REPLACE_ME_IF_NECESSARY` and modify as required (_these decisions will be driven by the flag activations_).

6. Review and modify placehoder values as necessary. Do not modify commented fields with `DO_NOT_UNCOMMENT_ME` values. These are in the file solely to provide a visual reminder that these keys are being set behind the scene via SSM secrets values.


### Create an AWS IAM Role with the necessary permissions

1. Modify the [`permissions.json`](templates/permissions.json) in the `templates` folder:

    1. Perform a find-and-replace on `tower-dev` if you select a different application name.
    
    2. Replace every `AWS_ACCOUNT_REPLACE_ME` instance with the id of the AWS Account which the Terraform installer will interact with.
    
    3. Create an AWS IAM Role / User and attach these permissions.

    4. Configure this identity into your AWS CLI and ensure it is active when executing the installer (specified  in `var.aws_profile`).


### Modify your OpenSSH config

During the installation process, a [SSH config file](https://man.openbsd.org/ssh_config) is created and used to connect to the EC2 instance hosting the Seqera Platform instance. To use the SSH config file successfully, you need a minor modification to your `openssh` configuration:

```bash
# Add the following entry AT THE TOP of your ~/.ssh/config file
Include /ABSOLUTE_PATH_TO_INSTALLER_PROJECT_ROOT/ssh_config

# NOTE: IF you intend to run multiple instances on the same host (e.g. dev and staging), add an Include to each project folder.
Include /ABSOLUTE_PATH_TO_INSTALLER_PROJECT_ROOT_DEV/ssh_config
Include /ABSOLUTE_PATH_TO_INSTALLER_PROJECT_ROOT_STAGING/ssh_config
```

### Review your Terraform state storage strategy

By default, the installer writes the Terraform state to a local folder (`<PROJECT_ROOT>/DONTDELETE`). This is convenient for initial testing but likely not a good long-term solution for most clients. 

You can change the state management strategy at the top of the `000-main.tf` file. We have provided a commented-out example that demonstrates how to write state to an S3 bucket.

**Note:** Bulletproof state management can become complex and is beyond the scope of this initiative. Consult Terraform's official docs on [Remote State](https://developer.hashicorp.com/terraform/language/state/remote) and modify your project as necessary to meet your organization's needs.


## Execution steps

### Deployment

1. Within your terminal, navigate to the project root and initialize the project:
    ```bash
    terraform init
    ```

10. Create and review an execution plan:
    ```bash
    terraform plan
    ```

11. Execute the actions reviewed in the Terraform plan:
    ```bash
    # You can append `--auto-append` to the end of the command to avoid the need to type 'yes' to approve the deployment.
    terraform apply
    ```

### Teardown

1. To destroy the infrastructure created via Terraform, execute the following command:
    ```bash
    terraform destroy
    ```

## WARNINGS

1. If a database (_regardless if container or RDS_) was created as part of the deployment, teardown **will destroy it and all data within**.<br />Prior to deletion, consider backing up your database if the data may be needed in future.

2. Terraform is not aware of actions executed within the Seqera Platform (_i.e., invocation of Tower Forge to create compute environments by users / automation tools like Seqerakit_). Executing `terraform destroy` without first conducting a purge of objects within Seqera Platform will result in orphaned assets in your AWS Account.


## Multiple Deployment Consideration

Given client environment variability, Seqera offers no official guidance re: how best to run multiple concurrent implementations (e.g. entirely separate repositories, different branches in a monorepo, Terraform workspaces, git submodules, etc). Each site must decide what is best for them and implement accordingly.

With that said, for design purposes, this tool assumes that multiple project instances will live in the same filesystem (_each within its own exclusive namespace_). Each project's `ssh_config` file uses an alias matching the unique `app_name` from your `tfvars` file, making it possible to add multiple non-conflicting `Include` statements in your `~/.ssh/config`.


## Terraform asset details

### Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](https://registry.terraform.io/providers/hashicorp/aws/5.12.0/docs) | 5.12.0 |
| <a name="provider_random"></a> [random](https://registry.terraform.io/providers/hashicorp/random/3.6.0) | 3.6.0 |
| <a name="provider_kubectl"></a> [null](https://registry.terraform.io/providers/hashicorp/null/3.2.2) | 3.2.2 |
| <a name="provider_kubernetes"></a> [tls](https://registry.terraform.io/providers/hashicorp/tls/4.0.5) | 4.0.5 |
| <a name="provider_random"></a> [template](https://registry.terraform.io/providers/hashicorp/template/2.2.0) | 2.2.0 |

### Modules
| Name | Source | Version |
|------|--------|---------|
| <a name="vpc"></a> [vpc](001-vpc.tf) | [terraform-aws-modules/s3-bucket/aws](https://registry.terraform.io/modules/terraform-aws-modules/vpc/aws/5.1.2) | 5.1.2 |
| <a name="tower_eice_ingress_sg"></a> [tower_eice_ingress_sg](002-security_groups.tf) | [terraform-aws-modules/security-group/aws](https://registry.terraform.io/modules/terraform-aws-modules/security-group/aws/5.1.0) | 5.1.0 |
| <a name="tower_eice_egress_sg"></a> [tower_eice_egress_sg](002-security_groups.tf) | [terraform-aws-modules/security-group/aws](https://registry.terraform.io/modules/terraform-aws-modules/security-group/aws/5.1.0) | 5.1.0 |
| <a name="tower_ec2_ssh_sg"></a> [tower_ec2_ssh_sg](002-security_groups.tf) | [terraform-aws-modules/security-group/aws](https://registry.terraform.io/modules/terraform-aws-modules/security-group/aws/5.1.0) | 5.1.0 |
| <a name="tower_ec2_egress_sg"></a> [tower_ec2_egress_sg](002-security_groups.tf) | [terraform-aws-modules/security-group/aws](https://registry.terraform.io/modules/terraform-aws-modules/security-group/aws/5.1.0) | 5.1.0 |
| <a name="tower_ec2_direct_sg"></a> [tower_ec2_direct_sg](002-security_groups.tf) | [terraform-aws-modules/security-group/aws](https://registry.terraform.io/modules/terraform-aws-modules/security-group/aws/5.1.0) | 5.1.0 |
| <a name="tower_alb_sg"></a> [tower_alb_sg](002-security_groups.tf) | [terraform-aws-modules/security-group/aws](https://registry.terraform.io/modules/terraform-aws-modules/security-group/aws/5.1.0) | 5.1.0 |
| <a name="tower_db_sg"></a> [tower_db_sg](002-security_groups.tf) | [terraform-aws-modules/security-group/aws](https://registry.terraform.io/modules/terraform-aws-modules/security-group/aws/5.1.0) | 5.1.0 |
| <a name="tower_batch_sg"></a> [tower_batch_sg](002-security_groups.tf) | [terraform-aws-modules/security-group/aws](https://registry.terraform.io/modules/terraform-aws-modules/security-group/aws/5.1.0) | 5.1.0 |
| <a name="rds"></a> [rds](003-database.tf) | [terraform-aws-modules/rds/aws](https://registry.terraform.io/modules/terraform-aws-modules/rds/aws/6.1.1) | 6.1.1 |
| <a name="alb"></a> [alb](007-load_balancer.tf) | [terraform-aws-modules/alb/aws](https://registry.terraform.io/modules/terraform-aws-modules/alb/aws/8.7.0) | 8.7.0 |

### Outputs

| Name | Description |
|------|-------------|
| <a name="aws_account_id"></a> [aws_account_id](011-outputs.tf) | AWS Account ID |
| <a name="aws_caller_arn"></a> [aws_caller_arn](011-outputs.tf) | Assumed role used to deploy the project |
| <a name="aws_caller_user"></a> [aws_caller_user](011-outputs.tf) | User used to deploy the project |
| <a name="ec2_ssh_key"></a> [ec2_ssh_key](011-outputs.tf) | SSH key attached to the EC2 instance |
| <a name="aws_ec2_private_ip"></a> [aws_ec2_private_ip](011-outputs.tf) | Private IP of the EC2 Instance |
| <a name="tower_server_url"></a> [tower_server_url](011-outputs.tf) | Platform  server URL |
| <a name="route53_record_status"></a> [route53_record_status](011-outputs.tf) | Status of Route53 record |
| <a name="tower_api_endpoint"></a> [tower_api_endpoint](011-outputs.tf) | Platform API endpoint |
| <a name="seqera_configuration"></a> [seqera_configuration](011-outputs.tf) | Path to the SeqeraKit setup file |
