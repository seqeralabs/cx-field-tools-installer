# Optional Config - Using AWS EC2 Instance Role
If you run Seqera Platform on AWS infrastructure, an optional configuration is available that allows your AWS-type credentials to leverge the EC2 Instance Role identity rather than a discrete AWS User (_thereby avoiding the need to input the User's long-lived AWS secret key and secret access keys_).

**AWS EC2 Instance Role**

- **Description**: [EC2 instances can be assigned IAM Roles](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html) that grant them permissions to interact with AWS services. This avoids the need for long-lived credentials by allowing the instance to retrieve temporary credentials via the EC2 metadata service.
- **Seamless Integration**: Applications running on EC2 instances can automatically use these roles to authenticate to AWS services without managing separate credentials.
- **Tower Configuration**: The `TOWER_ALLOW_INSTANCE_CREDENTIALS` setting allows Tower to use the EC2 instance's IAM role instead of AWS long-lived credentials if no other credentials are provided.


## Security Considerations 

While using an EC2 Instance Role improves security by eliminating stored keys, it still requires trust in workspace-level administrators who are allowed to create Credentials in Seqera Workspaces.

[Any user with adequate permissions (Admin)](https://docs.seqera.io/platform-cloud/orgs-and-teams/roles) to create Credentials in workspaces will have the ability to leverage the EC2 Instance Role to access any other IAM Role which the EC2 Instance Role has access to. 

Risk Scenario:

1. Workspace A is set up with Credentials defined to use IAM Role A with isolated access to specific AWS resources for privileged members of the workspace.

2. An Admin in Workspace B with knowledge of IAM Role A's ARN can technically create a new Credential in Workspace B defined to use IAM Role A ARN.

    This allows members of Workspace B to access any/all AWS resources intended for Workspace A as defined by the policies of IAM Role A.


## Implementation Steps

### Installer-Based Configuration
As of v1.6.2, activation of this feature is available via Terraform configuration (_disabled by default_). Opt in by:

1. Setting `flag_allow_aws_instance_credentials=true` in `terraform.tfvars`.
2. Ensuring you populate `TOWER_AWS_ROLE` in Seqerakit SSM entry with an IAM Role that can be configured by the EC2 Instance Profile created by this solution.

    The example below contains a snippet for how to make the target IAM Role assumable by multiple iterations of a single deployment and/or multiple deployment instances. Modify as required and please ensure to have any changed vetted by your security stakeholders for alignment to your organization's security protocols.

```json
// Trust Policy addition (example) on IAM-Role-to-be-assumed
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "SID": "SomeSID",
            ...
        },
        {
            "Sid": "AllowCXInstallerInstanceRole",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::<YOUR_ACCOUNT>:root"
            },
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringLike": {
                    "aws:PrincipalArn": [
                        "arn:aws:iam::<YOUR_ACCOUNT>:role/tf-<YOUR_APP_NAME>-*",
                        "arn:aws:iam::<ANOTHER_ACCOUNT>:role/<CUSTOM_PREFIX>-*"
                    ]
                }
            }
        }
    ]
}
```

### Manual Configuration
If you are on an Release >= 1.6.2, want this feature but dont want to enable it via terraform automation, or need to implement a more complicatd region than what is available via the automation solution, you can manually configure your assets (_either within the repository prior to deployment, which will affect all future deployments; or direct modification of the asset on the EC2, which will persist only until the next deployment_).

#### Update Platform Configuration


1. Update the `tower.env` file to contain the following configuration and re-start deployment for changes to propagate:

```
TOWER_ALLOW_INSTANCE_CREDENTIALS=true
```
2. Restart your application in order for the changes to your `tower.env` to be picked up by the Seqera Platform containers.

#### Update AWS IAM Artifacts

1. Update AWS EC2 Instance Role IAM permissions which will allow for the AWS EC2 Instance Role to assume the target IAM Role:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowAssumeRole",
            "Effect": "Allow",
            "Action": "sts:AssumeRole",
            "Resource": "arn:aws:iam::111111111111:role/SeqeraPlatformRole"
        }
    ]
}
```

2. Update Target IAM Role Trust Policy which will allow target IAM Role to **be assumed** by the AWS EC2 Instance Role:

```json
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::::############::role/AWS_EC2_Instance_Role"
            },
            "Action": "sts:AssumeRole"
        }
```

## Multi AWS Account Role Assumtion

When Seqera Platform needs to access resources across multiple AWS accounts, you can configure cross-account role assumption using EC2 Instance Roles. This setup allows a single Seqera Platform deployment to securely access resources in different AWS accounts without managing multiple sets of long-lived credentials.

Here is an example overview of a potential multi-account set-up:

    Seqera Platform EC2 Instance (Account: Management - 999999999999)
    └── EC2 Instance Role: SeqeraPlatform-EC2-InstanceRole
        ├── Assumes Role A (Account A: Production - 111111111111)
        └── Assumes Role B (Account B: Development - 222222222222)

## Implementation Steps

1. Update AWS EC2 Instance Role IAM permissions (Management Account) which will allow for the AWS EC2 Instance Role to assume the target IAM Roles roles in the target AWS accounts:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowAssumeRoleInAccountA",
            "Effect": "Allow",
            "Action": "sts:AssumeRole",
            "Resource": "arn:aws:iam::111111111111:role/SeqeraPlatformRole-AccountA"
        },
        {
            "Sid": "AllowAssumeRoleInAccountB", 
            "Effect": "Allow",
            "Action": "sts:AssumeRole",
            "Resource": "arn:aws:iam::222222222222:role/SeqeraPlatformRole-AccountB"
        }
    ]
}
```

2. Update Target IAM Roles' Trust Policy in each AWS Account which will allow the target IAM Roles to **be assumed** by the AWS EC2 Instance Role (Management Account):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::999999999999:role/SeqeraPlatform-EC2-InstanceRole"
            },
            "Action": "sts:AssumeRole",
        }
    ]
}
```
