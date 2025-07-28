import boto3
import pytest


# # Default AWS-managed KMS key
# aws ssm put-parameter \
#   --name "/app/secret/db-password" \
#   --value "MySecureP@ssw0rd" \
#   --type "SecureString" \
#   --overwrite


# ssm = boto3.client("ssm")

# response = ssm.put_parameter(
#     Name="/my/app/secret-db-password",  # full parameter path
#     Value="s3cr3tP@ssw0rd!",  # secret value
#     Type="SecureString",  # tell SSM to store it encrypted
#     KeyId="alias/aws/ssm",  # KMS key (omit for default key or supply custom key ARN)
#     Overwrite=True,  # overwrite if the parameter already exists
# )

# print("SSM Secure String created:", response["Version"])
