# CHANGELOG
> Last updated: Dec 11, 2025

This file was updated as part of the 1.7.0 Release.

```bash
# Example:
$ git log origin/master..origin/gwright99/25_2_0_update --oneline
```


## 1.7.0
- **Forward Roadmap Guidance**

    To help implementers plan effectively, please be aware of upcoming changes targeted for the next release. Implementation details are not yet finalized, so interested parties are invited to comment on the related GitHub Issues.

    Note these items in particular:

    1. Upgrade AWS RDS MySQL 8.0 to 8.4. [`#271`](https://github.com/seqeralabs/cx-field-tools-installer/issues/271)
    2. Upgrade Terraform AWS provider to version 6. [`#158`](https://github.com/seqeralabs/cx-field-tools-installer/issues/158)

    All in-scope ticket will be tagged with label `v1.8 Release`.

- **Notable Changes**
    - **CX Installer**
        - General
            - Updated Seqera Platform container version from v25.2.2 to v25.3.0. [`264`](https://github.com/seqeralabs/cx-field-tools-installer/issues/264)
            - Updated redis to `7.2.6` for Platform and Wave. [`#251`](https://github.com/seqeralabs/cx-field-tools-installer/issues/251)
            - Updated Seqera Platform frontend container to use non-privileged version. [`#270`](https://github.com/seqeralabs/cx-field-tools-installer/issues/270)
            - Updated Groundswell container version from 0.4.3 to 0.4.6. [`#238`](https://github.com/seqeralabs/cx-field-tools-installer/issues/238)
            - Updated Platform Connect containers version to 0.9.0. [`#273`](https://github.com/seqeralabs/cx-field-tools-installer/issues/273)
            - Updated Studios recommended base images. [`#273`](https://github.com/seqeralabs/cx-field-tools-installer/issues/273)
            - Changed `wave-db` container pin from `postgres:latest` to `postgres:17.6`. This is necessary to due to a change in how the [data directory is managed in postgres containers >= 18](https://hub.docker.com/_/postgres#pgdata). [`#250`](https://github.com/seqeralabs/cx-field-tools-installer/issues/250)
            - Modified `wave-db` and `wave-redis` port configuration to resolve string conversion error. [`298`](https://github.com/seqeralabs/cx-field-tools-installer/issues/298)
            - Added Seqera Platform pipeline versioning feature. [`#284`](https://github.com/seqeralabs/cx-field-tools-installer/issues/284)
            - Removed `FLYWAY_LOCATIONS` as configurable option. [`268`](https://github.com/seqeralabs/cx-field-tools-installer/issues/268)
            - Added [EC2 instance role option](https://docs.seqera.io/platform-enterprise/enterprise/advanced-topics/use-iam-role#configure-seqera). [`#242`](https://github.com/seqeralabs/cx-field-tools-installer/issues/242)
            - Added warning and check for personal workspace disablement. [`#246`](https://github.com/seqeralabs/cx-field-tools-installer/issues/246)
            - Added setting to auto-assign IPv4 addresses to instances in public subnets.
            - Modified docker compose file to use official Seqera Wave image & made image tag configurable. [`#252`](https://github.com/seqeralabs/cx-field-tools-installer/issues/252)
            - Made OpenAPI support configurable.
            - Entra ID (aka Azure AD) changes:
                - Added OAUTH2 configuration snippet in `tower.yml.tpl` for Platform versions < 25.3. [`#267`](https://github.com/seqeralabs/cx-field-tools-installer/issues/267)
                - Added verification check and warning. [`#276`](https://github.com/seqeralabs/cx-field-tools-installer/issues/276)
            - Changed backtick in Seqerakit yml to avoid TF warning message. [`#218`](https://github.com/seqeralabs/cx-field-tools-installer/issues/218)
            - Added `$.tower.runner.phantom-job.interval` value to _tower.yml.tpl_ to make UNKNOWN timeout configurable. [`#160`](https://github.com/seqeralabs/cx-field-tools-installer/issues/160)
        <br /><br />

        - Security
            - Bumped `runc` from 1.3.0 to 1.3.4. [`#272`](https://github.com/seqeralabs/cx-field-tools-installer/issues/272)
            - Bumped `docker` from 28.3.3 to 28.5.2. [`#272`](https://github.com/seqeralabs/cx-field-tools-installer/issues/272)
        <br/><br/>
        - Documentation
            - Updated instance role docs to reflect terraform deployment option. [`#242`](https://github.com/seqeralabs/cx-field-tools-installer/issues/242)
            - Updated templated `terraform.tfvars` with instance role flag and related considerations. [`#242`](https://github.com/seqeralabs/cx-field-tools-installer/issues/242)
            - Fixed hanging hypen in `permissions.md` document.
        <br /><br />

        - Testing
            - Added refactored local testing framework. Validates `tower.env` to ensure correct representation of the EC2 instance role option, `TOWER_ALLOW_INSTANCE_CREDENTIALS`, based on selection set in terraform.tfvars file. [`#242`](https://github.com/seqeralabs/cx-field-tools-installer/issues/242)
            - Added `labels.seqera` entry to each Wave-Lite container to facilatate positive testing (in support of [`#249`](https://github.com/seqeralabs/cx-field-tools-installer/issues/249)).
            - Added `labels.seqera` entry to generic `reverseproxy` container to align with Wave-Lite changes.
            - Updated baseline tests for new studios 0.9.0 version and Platform v25.3.0 feature flags.


### Configuration File Changes
#### `terraform.tfvars`
| Status | Component | Parameter Name | Description |
| ------ | --------- | -------------- | ----------- |
| New | Platform & Seqerakit | `flag_allow_aws_instance_credentials` | Allows activation of EC2 Instance Role for Seqera Platform to use when authenticating to AWS. |
| New | Platform | `flag_map_public_ip_on_launch` | Configure VPC module to enable auto-assignment of IPv4 addresses to instances spun up in public subnets. |
| New | Platform | `tower_enable_openapi` | Control whether your Platform instance enables the OpenAPI console or not. |
| New | Platform | `tower_enable_pipeline_versioning` | Control pipeline version feature. |
| New | Platform | `pipeline_versioning_eligible_workspaces` | Specific Platform Workspaces where pipeline versioning is active. |
| New | Wave | `wave_lite_container_version` | Specify the exact Wave image to be deployed for the Wave-Lite service. |
||||
| Modified | Platform | `tower_container_version` | Updated from v25.2.2 to v25.3.0 |
| Modified | Groundswell | `swell_container_version` | Updated  from 0.4.3 to 0.4.6 |
| Modified | Studios | `data_studio_container_version` | Updated  from 0.8.3 to 0.9.0 |
| Modified | Studios | `data_studio_options` | Removed 0_8_0 images and added 0_9_0 images |
||||
| Deleted | Platform | `flyway_locations` | Classpath configuration. Not necessary in modern deployments. |




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
| Deleted | Wave-Lite | `wave_lite_server_url` | The URL to use to check the Wave-Lite endpoint. |
| Deleted | Private Certificate | `flag_generate_private_cacert` | Deleted in favour of unified `flag_use_private_cacert` |
| Deleted | Private Certificate | `flag_use_existing_private_cacert` | Deleted in favour of unified `flag_use_private_cacert` |
| Deleted | Private Certificate | `existing_ca_cert_file` | Deleted since not required after S3 Bucket pre-load flow change. |
| Deleted | Private Certificate | `existing_ca_key_file` | Deleted since not required after S3 Bucket pre-load flow change. |
| Deleted | Private Certificate | `flag_use_custom_docker_compose_file` | Deleted since not required after S3 Bucket pre-load flow change. |




#### SSM Secrets
- Added `templates/ssm_sensitivie_values_wave_lite.json`
