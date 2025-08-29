# CHANGELOG
> Last updated: Aug 18, 2025

This file was created post 1.5.0 Release.

```bash
# Example:
$ git log origin/master..origin/gwright99/25_2_0_update --oneline
```


## 1.6.2
- **Notable Changes**:
    - **CX Installer**
        - General
            - Add [EC2 instance role option](https://docs.seqera.io/platform-enterprise/enterprise/advanced-topics/use-iam-role#configure-seqera)
        <br /><br />
        - Architecture
            - TBD
        <br /><br />
        - Documentation
            - TBD
        <br /><br />
        - Testing
            - Added refactored local testing framework

### Configuration File Changes
#### `terraform.tfvars`
| Status | Component | Parameter Name | Description |
| ------ | --------- | -------------- | ----------- |
| New | Platform & Seqerakit | `flag_allow_aws_instance_credentials` | Allows activation of EC2 Instance Role for Seqera Platform to use when authenticating to AWS. |




## 1.6.1
- **Notable Changes**:
    - **CX Installer**
        - General
            - Patched issues reported in [234 - Release 1.6.0 deployment issues](https://github.com/seqeralabs/cx-field-tools-installer/issues/234)
            - Added explicit call-out in 1.6.0 section that new variable `use_mocks` was added.
        <br /><br />
        - Architecture
            - All Security Group resources from 1.5.0 reintroduced in a deprecation section at bottom of `002_security_groups.tf`. This is to help existing sites transition to the new 1.6.0+ SG model.
                - Commented out ingress rules for deprecated SG `tower_ec2_direct_connect_sg` due to `local.tower_ec2_direct_connect_sg_final` no longer existing.
                - Commented out ingress rules for deprecated SG `tower_ec2_alb_connect_sg` due to `local.tower_ec2_alb_connect_sg_final` no longer existing.
            - Modified `connection_strings` module:
                - `data.external.generate_db_connection_string` to use absolute path from module root rather than relative path.
                - Added `wave_lite_enabled` qualifier to variables associated with Wave Lite external DB and external Redis.
        <br /><br />
        - Documentation
            - Renamed _Changelog_ entry from `2.0.0` to `1.6.0`.
            - Added discrete _Upgrade Steps_ page.
            - Added warning re: EBS volume during multi-version upgrade cycle.
            - Added escape hatch documentation is deployed resource doesn't reflect expected changes.


### Configuration File Changes
#### `terraform.tfvars`
| Status | Component | Parameter Name | Description |
| ------ | --------- | -------------- | ----------- |
| Modified | Platform | `ec2_root_volume_size` | Changed from `8` to `16` to provide more storage buffer. |


## 1.6.0

### Feature Updates & Improvements
- **Breaking Changes**:
    - Private certificates served from deployed EC2 must now be pre-loaded to S3 Bucket prior to deployment.

- **Notable Changes**:
    - **Seqera Ecosytem**
        - Platform
            - Bumped Platform version to `v25.2.0`.
            - Crypto secret rotation added.

        - Studios
            - Bumped Studio version to `0.8.3`.
            - Studios path-based routing supported for ALB & EC2-direct flow.
            - Added `0.8.5` Studios client images.

        - Wave
            - Wave-Lite support introduced.

        - Groundswell
            - Bumped image to `0.4.3`.


    - **CX Installer**
        - General
            - Began experimenting producing code with AI. Efforts are tightly scoped and 100% human supervised thus far.
        <br /><br />
        - Architecture
            - Subnet reconcilation logic centralized in module `subnet_collector`.
            - URL / connection string generation logic centralized in module `connection_strings`.
            - Changed private certificate flow: Certs must now be pre-loaded to S3 bucket & are pulled at run-time.
            - Refactored `assets/src/customcerts/`: Generation script supports multiple domains & removed placeholder files.
            - Merged / broke out EC2 security groups for easier management and better permissions scoping. **This could break ancillary components if you reused the security groups elsewhere!**
            - Refactored when most `assets/target/` files are produced. Rather than waiting for all infrastructure to be created, we now create files as soon as minimal dependencies are met (_to facilitate testing_).
            - Added new variable `use_mocks`to `variables.tf`. This value defaults to `false` since it should only be `true` during testing.
            - Added `... && !var.use_mock` to database and redis assets' `count` property to facilitate testing.
            - Moved conditional Ansible steps from Bash environment logic to `.tpl` inclusion / exclusion.
            - Modified `docker-compose.yml` so that all configuration files are mounted from their respective `target/**` folder.
            - Bumped `seqerakit --> v0.5.5` and `tw --> 0.14.0`.
            - Broke out monolithic step in `011_configure_vm.tf` into smaller chained resources for bettter visibility and reduced blast radius.
        <br /><br />
        - Security
            - Bumped `java-17-amazon-corretto-devel-1:17.0.14+7-1.amzn2023.1` to `java-17-amazon-corretto-devel-1:17.0.16+8-1.amzn2023.1`.
            - Bumped docker version from `28.1.1` --> `28.3.3`.
        <br /><br />
        - Documentation
            - Changed `TEMPLATE_terraform.tfvars` application name from `tower-dev` to `tower-template`.
            - Added Design Decision explaining why Studio subdomain routing is the default over path-based routing.
            - Added Setup guidance re: Platform crypto secret rotation.
            - Added Setup guidance re: how to prepare / pre-loaded Private Certificates.
        <br /><br />
        - Validation
            - Added Studios path-based routing checks & warnings.
        <br /><br />
        - Testing
            - Added preliminary testing framework. Validates outputs of `module.connection_strings` and some files in `assets/target/`.
            - Added preliminary MySQL & Postgres & Docker Compose Testcontainers for local validation.
            - Added test data generation (tfvars & secrets) mechanism.
            - Added test logging facility (via Pytest lifecycle hooks) to facilitate human observability and AI agent resolution.
            - Added Pytest marks to allow for targeted test runs.
            - Added `terraform plan` caching mechanism to speed up n+1 tests.


### Configuration File Changes
#### `terraform.tfvars`
| Status | Component | Parameter Name | Description |
| ------ | --------- | -------------- | ----------- |
| New | Studios | `flag_studio_enable_path_routing` | Enables/Disables Studios path-based routing. |
| New | Studios |  `flag_studio_enable_path_routing` | The URL to use rather than default subdomain approach. |
| New | Wave-Lite | `secrets_bootstrap_wave_lite` | Secrets associated with Wave-Lite configuration. |
| New | Wave-Lite | `flag_use_wave_lite` | Enables/Disables Wave-Lite. |
| New | Wave-Lite | `num_wave_lite_replicas` | Number of Wave-Lite relicas to run. |
| New | Private Certificate | `flag_use_private_cacert` | Single flag replacing `flag_generate_private_cacert` & `flag_use_existing_private_cacert` |
| | | | |
| Modified | Studios | `data_studio_options` | Removed deprecated entries. Added `0.8.4` options. |
| Modified | Private Certificate | `bucket_prefix_for_new_private_ca_cert` | Renamed to `private_cacert_bucket_prefix`. |
| | | | |
| Deleted | Private Certificate | `flag_generate_private_cacert` | Deleted in favour of unified `flag_use_private_cacert` |
| Deleted | Private Certificate | `flag_use_existing_private_cacert` | Deleted in favour of unified `flag_use_private_cacert` |
| Deleted | Private Certificate | `existing_ca_cert_file` | Deleted since not required after S3 Bucket pre-load flow change. |
| Deleted | Private Certificate | `existing_ca_key_file` | Deleted since not required after S3 Bucket pre-load flow change. |
| Deleted | Private Certificate | `flag_use_custom_docker_compose_file` | Deleted since not required after S3 Bucket pre-load flow change. |
| Deleted | Wave-Lite | `wave_lite_server_url` | The URL to use to check the Wave-Lite endpoint. |



#### SSM Secrets
- Added `templates/ssm_sensitivie_values_wave_lite.json`
