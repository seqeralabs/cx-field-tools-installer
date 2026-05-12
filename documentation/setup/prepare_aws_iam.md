# Prepare AWS IAM Permissions
This page provides instructions on how to create the AWS IAM permissions the solution requires to deploy your Seqera Platform instance.


## NOTE
By default, the solution expects to assume an AWS IAM Role when interacting with your AWS Account. If you are using static user credentials, you will need to implement changes in the terraform files (specifically, `var.aws_profile`).


## STEP
### Configure IAM Permissions

1. Make a scratch copy of the JSON payload contained within [Permissions](./permissions.md).

2. Modify the payload as follows:

    1. Perform a find-and-replace on `APP_NAME_REPLACE_ME` (_suggested default is `tower-dev`_).

    2. Replace every `AWS_REGION_REPLACE_ME` with your desired AWS region.
    
    3. Replace every `AWS_ACCOUNT_REPLACE_ME` instance with the id of the AWS Account which the Terraform installer will interact with.


### Create Permissioned IAM User / Role

1. Create an AWS IAM Role / User and attach these permissions.

2. Configure this identity into the AWS CLI on the machine where the Terraform project is located. Ensure it is active when executing the installer.
