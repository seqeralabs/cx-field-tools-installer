# Prepare `terraform.tfvars` file
This page provides instructions on how to populate the `terraform.tfvars` file the solution requires to properly configure your Seqera Platform deployment.


## NOTE
Fulsome field-level documentation exists inside the `terraform.tfvars` file. Consult there for details beyond the high-level instructions here.


## STEPS

1. Create a working copy of the [`terraform.tfvars`](../../templates/TEMPLATE_terraform.tfvars) file in the project root.

    ```bash
    # In project root
    cp templates/TEMPLATE_terraform.tfvars terraform.tfvars
    ```

2. Modify the root-level `terraform.tfvars` file as follows:

    1. Update the `app_name` with your chosen application name.
    
    2. Update the following secrets values with your chosen SSM prefixes:
        
        - `secrets_bootstrap_tower`
        - `secrets_bootstrap_seqerakit`
        - `secrets_bootstrap_groundswell`
        - `secrets_bootstrap_wave_lite`

    3. Replace every instance of `REPLACE_ME` with values appropriate for your organization.

    4. Set `flag_*` variables to `true` / `false` to match your desired implementation architecture.

    5. Review each instance of `REPLACE_ME_IF_NECESSARY` and modify as required (_these decisions will be driven by the flag activations_).

    6. Review and modify placehoder values as necessary. Do not modify commented fields with `DO_NOT_UNCOMMENT_ME` values. These are in the file solely to provide a visual reminder that these keys are being set behind the scene via SSM secrets values.
