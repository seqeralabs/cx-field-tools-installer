# Optional Config - Using AWS EC2 Instance Role
When integrating Seqera Platform with AWS, enabling an optional configuration allows for Seqera Platform credentials to solely rely on EC2 Instance Roles with the ability to assume IAM Roles for further granular permissions. Using instance roles removes the need to provide Seqera Platform with AWS long-lived credentials such as AWS secret key and secret access keys.

**AWS EC2 Instance Role**

- **Description**: EC2 instances can be assigned IAM Roles that grant them permissions to interact with AWS services. This avoids the need for long-lived credentials by allowing the instance to retrieve temporary credentials via the EC2 metadata service.
- **Seamless Integration**: Applications running on EC2 instances can automatically use these roles to authenticate to AWS services without managing separate credentials.
- **Tower Configuration**: The `TOWER_ALLOW_INSTANCE_CREDENTIALS` setting allows Tower to use the EC2 instance's IAM role instead of AWS long-lived credentials if no other credentials are provided.

## Security Considerations 

While using an EC2 Instance Role improves security by eliminating stored keys, it still requires trust in workspace-level administrators who are allowed to create Credentials in Seqera Workspaces.

Any user with adequate permissions (Admin) to create Credentials in workspaces will have the ability to use the IAM Role associated with a credential to gain access to any/all resources available to the IAM Role. 

Risk Scenario:

1. Workspace A is set up with Credentials defined to use IAM Role A with isolated access to specific AWS resources for privileged members of the workspace.

2. An Admin in Workspace B with knowledge of IAM Role A's ARN can technically create a new Credential in Workspace B defined to use IAM Role A ARN.
    - This allows members of Workspace B to access any/all AWS resources intended for Workspace A as defined by the policies of IAM Role A.


## Implementation Steps

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