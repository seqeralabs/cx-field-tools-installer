# Prepare Secrets
This page provides instructions on how to populate the secrets payload your Seqera Platform instance will load and use at run-time.


## NOTE
In our experience, modifying large JSON objects directly within the AWS Parameter Store console is an unpleasant process which can easily introduce typos in the resulting object. 

To streamline your deployment effort, these templated files have been provided as scratch work files: **They are NOT expected to be checked into source control!!**. Instead, we assume you will make the modifications within your IDE (_taking advantage of its native liniting capabilities_) before executing a one-shot copy directly into the corresponding AWS Parameter Store key. 


## WARNING 
Some deployments may choose not to activate particular platform features (_e.g. Wave-Lite_). Regardless of which features you enable, **ALL** secrets objects must be created in AWS Parameter Store for the application to deploy successfully (_this is a result of how the deployment solution was written)_. 

If you do not intend to use a specific feature, we suggest simply retaining the templated text. Although the keys will exist in your Parameter Store, the feature will not be activated until you explicitly choose to do so via your deployment's [terraform.tfvars](../../templates/TEMPLATE_terraform.tfvars) file.


## STEPS
### Prepare Core Application Secrets

1. Modify the [`ssm_sensitive_values_tower.json`](../../templates/ssm_sensitive_values_tower.json) in the `templates` folder:

    1. Perform a find-and-replace on `tower-template` if you select a different application name.

    2. Replace every instance of `CHANGE_ME` in the file with the values supplied to you during your Seqera onboarding.

    3. Replace every instance of `CHANGE_ME_SEE_SEQERA_DOCS` with your own values. 
    
        Configuration value guidance can be found at [Seqera Platform Enterprise configuration](https://docs.seqera.io/platform/latest/enterprise/configuration/overview).

    4. Review each instance of `CHANGE_ME_IF_NECESSARY` and [replace as needed](https://docs.seqera.io/platform/latest/enterprise/configuration/authentication).


    **WARNING:** 
    1. Do not change `ssm_key` entries apart from the application name. Path changes will prevent the application from booting.

    2. SSM entries have a limit of 4096 characters. Very long client-supplied values may result in errors when you try to create the entry.


### Prepare Seqerakit Secrets

1. Modify the [`ssm_sensitive_values_seqerakit.json`](templates/ssm_sensitive_values_seqerakit.json) in the `templates` folder:

    1. Execute a find-and-replace on `tower-template` if you select a different application name.

    2. Replace every instance of `CHANGE_ME` in the file with the [values appropriate for your organization](https://github.com/seqeralabs/nf-tower-aws).

    3. Review each instance of `CHANGE_ME_IF_NECESSARY` and [replace as needed]((https://docs.seqera.io/platform/23.3.0/credentials/overview)).

          An AWS credential set is a mandatory minimum. The `terraform.tfvars` file has flags that can enable/disable expectations regarding the AWS IAM role, Github credential, and Docker credential. 


        **WARNING:** 
        1. Do not change `ssm_key` entries apart from the application name. Path changes will prevent the application from booting.


### Prepare Groundswell Secrets

1. Modify the [`ssm_sensitive_values_groundswell.json`](templates/ssm_sensitive_values_groundswell.json) in the `templates` folder:

    1. Execute a find-and-replace on `tower-template` if you select a different application name.

    2. Replace default values if necessary.


### Prepare Wave-Lite Application Secrets

1. Modify the [`ssm_sensitive_values_wave_lite.json`](../../templates/ssm_sensitive_values_wave_lite.json) in the `templates` folder:

    1. Perform a find-and-replace on `tower-template` if you select a different application name.

    2. Replace every instance of `CHANGE_ME_SEE_SEQERA_DOCS` with your own values. 
    
        Configuration value guidance can be found at [Seqera Platform Enterprise configuration](https://docs.seqera.io/platform/latest/enterprise/configuration/overview).


    **WARNING:** 
    1. Do not change `ssm_key` entries apart from the application name. Path changes will prevent the application from booting.
