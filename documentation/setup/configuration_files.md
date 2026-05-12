# Configuration Files

This solution is designed so that the average deployer can interact solely with a core set of [configuration files](../../templates/), and not need to interact with the underlying Terraform and Python assets.


## Configuration File Details
Configuration activities are split between two different categories:

1. Desired infrastructure and application deployment state (_via `terraform.tfvars`_).
2. Seeding of sensitive application secrets in AWS Parameter Store (_via `ssm_sensitive_values_*` files_).

1. [`terraform.tfvars`](../../templates//TEMPLATE_terraform.tfvars)<br />Used to set flags and values that control how your infrastructure and the Seqera Platform Enterprise instance is built and configured.

    This file must be configured and stored in the **project folder root**.

2. [`ssm_sensitive_values_tower.json`](../../templates//ssm_sensitive_values_tower.json)<br />Used to define secrets like credentials and passwords which the Seqera Platform needs to fulfill its duties.

    This file exists to make SSM data population more convenient and **should not** be stored in source-control. 

3. [`ssm_sensitive_values_seqerakit.json`](../../templates//ssm_sensitive_values_seqerakit.json)  (Optional) <br />Used to define secrets like tokens and credentials which the [Seqerakit](https://github.com/seqeralabs/seqera-kit) tool needs to fulfill its duties.

    This file exists to make SSM data population more convenient and **should not** be stored in source-control. 

4. [`ssm_sensitive_values_groundswell.json`](../../templates//ssm_sensitive_values_groundswell.json)  (Optional) <br />Used to define credentials for the Groundswell optimization service.

    This file exists to make SSM data population more convenient and **should not** be stored in source-control. 

5. [`ssm_sensitive_values_wave_lite.json`](../../templates//ssm_sensitive_values_wave_lite.json)  (Optional) <br />Used to define credentials for the Groundswell optimization service.

    This file exists to make SSM data population more convenient and **should not** be stored in source-control. 
