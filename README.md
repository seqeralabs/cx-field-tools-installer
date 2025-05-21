# Terraform Installer For Seqera Platform Enterprise (Docker-Compose)

A successful Seqera Platforn deployment requires many decisions about networking, security posture, container orchestration, permissions, etc. which can sometimes be overwhelming to a client administrator who just wants to get their users onboarded and using the features offered by the Platform. 

The Seqera CX team has developed a field tool to simplify deployment in two ways:

1. Reduce the infrastructure and configuration burden, so that a first-time deployment of Seqera Platform Enterprise requires less than 1 hour of work and only a few minutes for subsequent redeployments.

2. Provide an Infrastructure-As-Code (IaC) solution so activities are repeatable and artifacts can be checked into source-control.


## Disclaimer - Use at your own discretion!!

**This is an unofficial field tool.** 

The solution is delivered on a best-effort basis, but provides no guarantees of appropriateness for your specific scenario. Please conduct your due diligence prior to execution within your environment.

For further information on how the project is managed, please see:

- [Design Decisions](documentation/design_decisions.md)

    Information about project structure, design decisions, and assumptions made.

- [Security Scanning](documentation/security.md)

    How we scan for / mitigate security vulnerabilities found within the solution.

- [Deficiencies & Gotchas](documentation/deficiencies_and_gotchas.md)

    Information on existing deficiencies and gotchas.


## Appropriateness Criteria
You must meet the following criteria to use this solution successfully.

1. You are a client of Seqera Labs.
2. You will run Seqera Platform in AWS.
3. Your corporate policies allow you to store secrets in [AWS Systems Manager Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html) (SSM).
4. You have access to a local **Linux**-based terminal (_Mac supported, with caveats_).
5. You can use [Terraform](https://www.terraform.io/) to provision infrastructure.
6. You use OpenSSH and can maintain a `~/.ssh/config` file. 
7. **(New as of May 21, 2025)** You have access to a local container runtime (_e.g. [Docker](https://www.docker.com/ _).


## Pre-Requisites
### Tool Dependencies
See [Tool Dependencies](./documentation/setup/install_tools.md) for pre-requisite installation instructions.


### AWS IAM Permissions
See [Permissions](./documentation/setup/permissions.md) for the necessary AWS IAM permissions required.


## Configuration Steps
See [Configuration Files](./documentation/setup/configuration_files.md) for details on the files you'll interact with.


### 01 - Clone the repository

1. Download a copy of the repository to your local workstation:

    ```bash
    git clone <path_to_offical_repo> && cd <name_of_local_directory>
    ```

### 02 - Prepare Configuration Files

1. Select a name for your Seqera Platform application (default: `tower-dev`).
    
    This is a namespace isolator which prevents concurrent instances (_e.g., `dev` and `prod`_) from accidentally sharing configurations. 

    Remember this value because you will need it to modify the templated configuration files in the next step.

#### 02A - Prepare secrets 

1. Follow the instructions in [Prepare Secrets](./documentation/setup/prepare_secrets.md) and then return here.


2. Decide on the [AWS Parameter Store prefixes](https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-su-create.html) to store the payloads of your now-populated `ssm_*` files.

    Default values in `terraform.tfvars` are:
    - `/seqera/sensitive_values/tower_dev/tower`
    - `/seqera/sensitive_values/tower_dev/seqerakit`
    - `/seqera/sensitive_values/tower_dev/groundswell`
    - `/seqera/sensitive_values/tower_dev/wave-lite`


3. Create the entries and paste the appropriate JSON payload for each. Ensure that:

    1. **Type** is set to `SecureString`.
    2. **Data type** is `text`.


Remember your application name and SSM prefixes, as these need to be supplied during the configuration of the `terrform.tfvars` file.


### 03 - Prepare the `terraform.tfvars` file

1. Follow the instructions in [Prepare TFvars](./documentation/setup/prepare_tfvars.md) and then return here.




### 04 - Create an AWS IAM Role with the necessary permissions

1. Modify the [JSON block](documentation/setup/permissions.md) in the `documentation` folder:

    1. Perform a find-and-replace on `APP_NAME_REPLACE_ME` (_suggested default is `tower-dev`_).

    2. Replace every `AWS_REGION_REPLACE_ME` with your desired AWS region.
    
    3. Replace every `AWS_ACCOUNT_REPLACE_ME` instance with the id of the AWS Account which the Terraform installer will interact with.
    
2. Create an AWS IAM Role / User and attach these permissions.

3. Configure this identity into your AWS CLI and ensure it is active when executing the installer (specified  in `var.aws_profile`).


### 05 - Modify your OpenSSH config

During the installation process, a [SSH config file](https://man.openbsd.org/ssh_config) is created and used to connect to the EC2 instance hosting the Seqera Platform instance. To use the SSH config file successfully, you need a minor modification to your `openssh` configuration:

```bash
# Add the following entry AT THE TOP of your ~/.ssh/config file
Include /ABSOLUTE_PATH_TO_INSTALLER_PROJECT_ROOT/ssh_config

# NOTE: IF you intend to run multiple instances on the same host (e.g. dev and staging), add an Include to each project folder.
Include /ABSOLUTE_PATH_TO_INSTALLER_PROJECT_ROOT_DEV/ssh_config
Include /ABSOLUTE_PATH_TO_INSTALLER_PROJECT_ROOT_STAGING/ssh_config
```


### 06 - Update your Git repo settings

The project ships with a `.githooks` folder, which contains a Python script that wil scan your `terraform.tfvars` file for configuration mismatches which cause your deployment to fail.

To automatically invoke the script prior to a commit to your git repository, execute the following in the root of your project: `git config core.hooksPath .githooks`.


### 07 - Review your Terraform state storage strategy

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
    # Recommended approach. Execute the Seqera-supplied Python script to check your `terraform.tfvars` file for known configuration conflicts prior to terraform binary invocation.
    make plan

    # Alternative approach to execute plan without Python script verification execution.
    terraform plan
    ```

11. Execute the actions reviewed in the Terraform plan:
    ```bash
    # Recommended approach. Execute the Seqera-supplied Python script to check your  `terraform.tfvars` file for known configuration conflicts prior to terraform binary invocation.
    make apply

    # Alternative approach to execute plan without Python script verification execution.
    # Note: You can append `--auto-append` to the end of the command to avoid the need to type 'yes' to approve the deployment.
    terraform apply
    ```

### Teardown

1. To destroy the infrastructure created via Terraform, execute the following command:
    ```bash
    terraform destroy
    ```


## Logging

The tool offers the ability to configure the specific docker logging driver used to capture Tower container logs. By default, the [`local file`](https://docs.docker.com/config/containers/logging/local/) logging driver is configured.


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
| <a name="vpc"></a> [vpc](001_vpc.tf) | [terraform-aws-modules/s3-bucket/aws](https://registry.terraform.io/modules/terraform-aws-modules/vpc/aws/5.1.2) | 5.1.2 |
| <a name="tower_eice_ingress_sg"></a> [tower_eice_ingress_sg](002_security_groups.tf) | [terraform-aws-modules/security-group/aws](https://registry.terraform.io/modules/terraform-aws-modules/security-group/aws/5.1.0) | 5.1.0 |
| <a name="tower_eice_egress_sg"></a> [tower_eice_egress_sg](002_security_groups.tf) | [terraform-aws-modules/security-group/aws](https://registry.terraform.io/modules/terraform-aws-modules/security-group/aws/5.1.0) | 5.1.0 |
| <a name="sg_ec2_core"></a> [sg_ec2_core](002_security_groups.tf) | [terraform-aws-modules/security-group/aws](https://registry.terraform.io/modules/terraform-aws-modules/security-group/aws/5.1.0) | 5.1.0 |
| <a name="sg_ec2_core"></a> [sg_ec2_core](002_security_groups.tf) | [terraform-aws-modules/security-group/aws](https://registry.terraform.io/modules/terraform-aws-modules/security-group/aws/5.1.0) | 5.1.0 |
| <a name="sg_ec2_noalb"></a> [sg_ec2_noalb](002_security_groups.tf) | [terraform-aws-modules/security-group/aws](https://registry.terraform.io/modules/terraform-aws-modules/security-group/aws/5.1.0) | 5.1.0 |
| <a name="sg_alb_core"></a> [sg_alb_core](002_security_groups.tf) | [terraform-aws-modules/security-group/aws](https://registry.terraform.io/modules/terraform-aws-modules/security-group/aws/5.1.0) | 5.1.0 |
| <a name="sg_db"></a> [sg_db](002_security_groups.tf) | [terraform-aws-modules/security-group/aws](https://registry.terraform.io/modules/terraform-aws-modules/security-group/aws/5.1.0) | 5.1.0 |
| <a name="sg_batch"></a> [sg_batch](002_security_groups.tf) | [terraform-aws-modules/security-group/aws](https://registry.terraform.io/modules/terraform-aws-modules/security-group/aws/5.1.0) | 5.1.0 |
| <a name="rds"></a> [rds](003_database.tf) | [terraform-aws-modules/rds/aws](https://registry.terraform.io/modules/terraform-aws-modules/rds/aws/6.1.1) | 6.1.1 |
| <a name="alb"></a> [alb](007_load_balancer.tf) | [terraform-aws-modules/alb/aws](https://registry.terraform.io/modules/terraform-aws-modules/alb/aws/8.7.0) | 8.7.0 |

### Outputs

| Name | Description |
|------|-------------|
| <a name="aws_account_id"></a> [aws_account_id](012_outputs.tf) | AWS Account ID |
| <a name="aws_caller_arn"></a> [aws_caller_arn](012_outputs.tf) | Assumed role used to deploy the project |
| <a name="aws_caller_user"></a> [aws_caller_user](012_outputs.tf) | User used to deploy the project |
| <a name="ec2_ssh_key"></a> [ec2_ssh_key](012_outputs.tf) | SSH key attached to the EC2 instance |
| <a name="tower_server_url"></a> [tower_server_url](012_outputs.tf) | URL to check your Tower intance |
| <a name="route53_record_status"></a> [route53_record_status](012_outputs.tf) | Identifies if a Route53 record was created or not |
| <a name="aws_ec2_private_ip"></a> [aws_ec2_private_ip](012_outputs.tf) | Private IP of the EC2 Instance |
| <a name="aws_ec2_public_ip"></a> [aws_ec2_public_ip](012_outputs.tf) | Public IP of the EC2 Instance (if applicable) |  
| <a name="tower_api_endpoint"></a> [tower_api_endpoint](012_outputs.tf) | Platform API endpoint |
| <a name="seqera_configuration"></a> [seqera_configuration](012_outputs.tf) | Path to the SeqeraKit setup file |
| <a name="redis_endpoint"></a> [redis_endpoint](012_outputs.tf) | URL for your Redis instance |
