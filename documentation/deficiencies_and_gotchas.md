# Deficiencies and Gotchas

This page lists to-be-built-in-future functionality and various oddities you may encounter while using the solution.


## Gotchas

- Application name

    Some AWS resources (e.g. ALB) don't like it when there is an underscore in the name. Use a hyphen instead (if necessary).

- SSM (Standard) character max

    Standard SSM entries have a maximum size of 4KB. The content of [`ssm_sensitive_values_tower.json`](templates/ssm_sensitive_values_tower.json) is slightly smaller than this maximum size. If you go over the limit, you will need to reduce payload length or split the secret.

- Customization of `terraform.tfvars` vs `.tf` files vs `tower.yml.tpl`

    The `terraform.tfvars` file offers an easy way to modify the most critical project options but it does not offer everything. This was done deliberately to balance convenience against information overload, but the result is that some values are hardcoded in the project `.tf` files and/or `tower.yml.tpl`.

    For example, in the [`001-vpc.tf`](../000-main.tf) file, any newly-created VPC will use a single NAT Gateway to serve all private subnets. This makes sense to minimize costs in a dev environment but may be inappropriate in a production setting.

    Similarly, for less used Tower application settings, it often made more sense to add a single YAML snippet to the [`tower.yml.tpl`](../assets/src/tower_config/tower.yml.tpl) template file rather than make the value available in the `terraform.tfvars` file (which requires modifications to at least 4 project files). I recognize that this detracts from the "_only make changes in the `terraform.tfvars` and Parameter Store secrets_" approach philosophy but ... decisions needed to be made.

    Nothing stops you from editing your `.tf` and `.tpl` files to ensure the tool best fits your team's needs. Just be mindful that these changes will need to be reapplied anytime you grab an updated version of the tool.

- Bash shell customizations

    This tool relies on the ability to redirect text on a local shell (e.g. `echo 'my_content' > my_file`). Shell settings like [`noclobber`](https://www.gnu.org/software/bash/manual/html_node/The-Set-Builtin.html) will prevent successful execution.

- SES [does not support interface endpoints](https://docs.aws.amazon.com/ses/latest/dg/send-email-set-up-vpc-endpoints.html) in some availability zones.

    Example error: `Error: creating EC2 VPC Endpoint (com.amazonaws.us-east-1.email-smtp): InvalidParameter: The VPC endpoint service com.amazonaws.us-east-1.email-smtp does not support the availability zone of the subnet: subnet-xxxxxxxxxxxxxxxxx.`

- VPC endpoint private DNS

    Interface endpoints are generated with [`private_dns_enabled = true](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_endpoint#route_table_ids). If you put your Tower instance in a different subnet than your AWS Batch compute AND want both subnets to use an interface endpoint to the same AWS service (e.g. Parameter Store), an error will occur during the creation of the second endpoint instance due to a DNS record already existing. 

    To avoid this problem, the Terraform logic is implemented as follows: "_If creating an endpoint tied to the Tower subnet, create a DNS entry. If creating an endpoint tied to the Batch subnet(s), do not try to create a DNS entry._" 
    
    To ensure smooth operations across your VPC, consider assigning a superset of interface endpoints to your Tower instance. This will ensure DNS entries are available across the VPC.

- Extraneous cloud artefacts due to failed Terraform deployments

    Terraform is pretty good at cleaning up after itself, but we have noticed that - if particular internal Terraform milestones can't be reached during a deployment before a deployment-ending error occurs - extra resources can appear in cloud account (e.g. a 2nd or 3rd VM).

    This problem is only likely to be seen during the initial phase of your deployment efforts as you tweak OOTB settings to fit your organization's reality. Once you can successfully complete an end-to-end deployment, it is suggested you run a full destroy-and-redeploy cycle to clean up any extraneous artefacts that may have spawned. 

- `tw cli` limitations

    Current as of May 4/24, the `tw cli` does not support all transactions available via the Tower APIs (_including the creation of some Git credential types like CodeCommit). This lack of support means that direct invocation of Seqerakit after infrastructure creation requires an alternative implementation (_i.e. breaking up the monolith setup.yml file and invoking direct API calls in the middle). This workaround can be retired once `tw` is fully harmonized with the API offerings.

- Limitations of Terraform templating

    The Terraform `templatefile` function is used extensively in this project to generate config files (_e.g. `file.json.tpl` --> `file.json`). This generally works well, but the `$` variable identification notation causes problems when: 
    
        1. Trying to create a template file that contains both variables being passed to the `templatefile` function within Terraform and Bash subshell commands / conditional logic which are expected to be interpolated when Ansible runs the resulting file on the EC2. 

        2. Using proper punctuation in comments (_e.g. the `'` in `won't`), which results in hugely frustrating-to-resolve file generation errors which make me want to purge Ansible from this solution every couple of weeks.

    As a result of these challenges, two behaviours are implemented:

        1. Avoidance wherever possible in comments of characters that could be interpreted as string identifiers or code to be executed: `'`, `"`, and `\``.

        2. Break-up of Ansible and Bash scripts into smaller files in a way such that some files can be pushed through the Terraform templating engine, while others are treated as static files.

    TBD whether Terraform templating should remain the longer-term solution (current as of May 2024). The introduction of the new Python-based variable configuration checker could likely be easily extended to handle template file generation as well, and brings all the power of a true programming language. 

- Launch Template behaviour

    The `data.aws_ami` resource filtering we use in [`006_ec2.tf`](https://github.com/seqeralabs/cx-field-tools-installer/blob/master/006_ec2.tf) was too loose upon initial release. While it does well at finding updated Amazon Linux 2023 AMIs, existing candidates can be pulled from at least 4 different family types (_standard, minimal, neuron, hvm, etc_). 

    The default behaviour has been remediated in version 1.3:

        - A flag (`ec2_update_ami_if_available`) is now available in the `terraform.tfvars` file to allow implementators to decide whether to allow AMIs to automatically update or pin to a specific version.

        - We mooted whether to make the `data.aws_ami` filtering object more specific but decided to leave as is for reverse compatibility. Implementators seeking greater control over the application can choose to modify the resource directly. [Reference Issue](https://github.com/seqeralabs/cx-field-tools-installer/issues/73)


## Deficiencies

In no particular order, the following items are acknowledged for eventual future remediation.

- Modify solution to allow use of existing ALB (must create new for now).
- Replace `mysql` client install (Ansible step) with docker container. Bypasses risk of expiring GPG key.
- Move hardcoded Elasticache values to `terraform.tfvars` file.