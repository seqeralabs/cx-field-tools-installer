# Terraform Installer For Seqera Platform Enterprise (Docker-Compose)

A successful Seqera Platform deployment requires making decisions about networking, security posture, container orchestration, permissions, etc. which can sometimes be overwhelming to a client administrator who just wants to get their users onboarded and using the features offered by the Platform. 

The Seqera CX team has developed a field tool to simplify deployment in two ways:

1. Reduce the infrastructure and configuration burden, so that a first-time deployment of Seqera Platform Enterprise requires less than 1 hour of work and only a few minutes for subsequent redeployments.

2. Provide an Infrastructure-As-Code (IaC) solution so activities are repeatable and artifacts can be checked into source-control.


## Disclaimer - Use at your own discretion!!

**This is an unofficial field tool.** 

The solution is delivered on a best-effort basis, but provides no guarantees of appropriateness for your specific scenario. Please conduct your due diligence prior to execution within your environment.

For further information on how the project is managed, please see:

- [Design Decisions](documentation/design_decisions.md)<br />
    Information about project structure, design decisions, and assumptions made.

- [Security Scanning](documentation/security.md)<br />
    How we scan for / mitigate security vulnerabilities found within the solution.

- [Deficiencies & Gotchas](documentation/deficiencies_and_gotchas.md)<br />
    Information on existing deficiencies and gotchas.


## Appropriateness Criteria
You must meet the following criteria to use this solution successfully.

1. You are a client of Seqera Labs.
2. You will run Seqera Platform in AWS.
3. Your corporate policies allow you to store secrets in [AWS Systems Manager Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html) (SSM).
4. You have access to a local **Linux**-based terminal (_Mac supported, with caveats_).
5. You can use [Terraform](https://www.terraform.io/) to provision infrastructure.
6. You use OpenSSH and can maintain a `~/.ssh/config` file. 
7. **(New as of May 21, 2025)** You have access to a local container runtime (_e.g. [Docker](https://www.docker.com/_).


## <br />Prerequisites
#### Tool Dependencies
See [Tool Dependencies](./documentation/setup/install_tools.md) for tooling requirements. 


#### AWS IAM Permissions
See [Permissions](./documentation/setup/permissions.md) for the required AWS IAM permissions.


## <br />Configuration Steps (Mandatory)
See [Configuration Files](./documentation/setup/configuration_files.md) for file details.


#### 01: Clone the repository
1. Download a copy of the repository to your local workstation:

    ```bash
    git clone <path_to_offical_repo> && cd <name_of_local_directory>
    ```


#### 02: Prepare Configuration Files
1. Select a name for your Seqera Platform application (_default: `tower-dev`_).
    
    _This is a namespace isolator which prevents concurrent instances (e.g., `dev` and `prod`) from accidentally sharing configurations._


#### 02A: Prepare secrets 
1. Follow the instructions in [Prepare Secrets](./documentation/setup/prepare_secrets.md) and then return here.

2. Follow the instructions in [Prepare SSM Secrets](./documentation/setup/prepare_ssm.md) and then return here.

    _Remember your application name and SSM prefixes, as these are required for later configuration steps._


#### 02B: Prepare the `terraform.tfvars` file
1. Follow the instructions in [Prepare TFvars](./documentation/setup/prepare_tfvars.md).


#### 03: Create an AWS IAM Role with the necessary permissions
1. Follow the instructions in [Prepare AWS IAM Permissions](/documentation/setup/prepare_aws_iam.md).


#### 04: Modify OpenSSH config

1. Follow the instructions in [Prepare OpenSSH](/documentation/setup/prepare_openssh.md).


## <br />Configuration Steps (Optional)
The following configuration actions are encouraged but not mandatory.

#### 01: Review your Terraform state storage strategy
1. Follow the instructions in [Review Terraform State Strategy](./documentation/setup/optional_tfstate.md).

#### 02: Update your Git repo settings
1. Follow the instructions in [Update Githooks Settings](./documentation/setup/optional_githook.md).



## <br />Execution Steps

#### Deployment

1. Via terminal, navigate to the project root and initialize the project:
    ```bash
    $ terraform init
    ```

2. Create and review an execution plan:
    ```bash
    # Recommended approach. 
    # Execute the Seqera-supplied Python script to check your `terraform.tfvars` file for known configuration conflicts prior to terraform binary invocation.
    $ make plan

    # Alternative approach.
    # Execute plan without Python script verification execution.
    $ terraform plan
    ```

2. Execute the actions reviewed in the Terraform plan:
    ```bash
    # Recommended approach. 
    # Execute the Seqera-supplied Python script to check your  `terraform.tfvars` file for known configuration conflicts prior to terraform binary invocation.
    $ make apply

    # Alternative approach.
    # Execute plan without Python script verification execution.
    # Note: You can append `--auto-approve` to the end of the command to avoid the need to type 'yes' to approve the deployment.
    $ terraform apply
    ```


### Teardown

1. To destroy the deployed infrastructure:
    ```bash
    $ terraform destroy
    ```


## WARNINGS

1. If a database (_regardless if container or RDS_) was created as part of the deployment, teardown **will destroy it and all data within**.<br />Prior to deletion, consider backing up your database if the data may be needed in future.

2. Terraform is not aware of actions executed within the Seqera Platform (_i.e., invocation of Tower Forge to create compute environments by users / automation tools like Seqerakit_). Executing `terraform destroy` without first conducting a purge of objects within Seqera Platform will result in orphaned assets in your AWS Account.


## Multiple Deployment Consideration

Given client environment variability, Seqera offers no official guidance re: how best to run multiple concurrent implementations (_e.g. entirely separate repositories, different branches in a monorepo, Terraform workspaces, git submodules, etc_). Each site must decide what is best for them and implement accordingly.

With that said, for design purposes, this tool assumes that multiple project instances will live in the same filesystem (_each within its own exclusive namespace_). Each project's `ssh_config` file uses an alias matching the unique `app_name` from your `tfvars` file, making it possible to add multiple non-conflicting `Include` statements in your `~/.ssh/config`.


## Terraform Asset details

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
