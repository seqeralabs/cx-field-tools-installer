# Prepare SSM Secrets
This page provides instructions on how to populate AWS Parameter Store secrets with your sensitive value payloads. 


## STEPS

1. Decide on the [AWS Parameter Store prefixes](https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-su-create.html) to store the payloads of your now-populated `ssm_sensitive_values_*` files.

    Default values in `terraform.tfvars` are:
    - `/seqera/sensitive_values/tower_dev/tower`
    - `/seqera/sensitive_values/tower_dev/seqerakit`
    - `/seqera/sensitive_values/tower_dev/groundswell`
    - `/seqera/sensitive_values/tower_dev/wave-lite`


2. Create the entries and paste the appropriate JSON payload for each. Ensure that:

    1. **Type** is set to `SecureString`.
    2. **Data type** is `text`.
