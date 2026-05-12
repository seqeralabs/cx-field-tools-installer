# CHANGELOG
> Last updated: Dec 11, 2025

This file was updated as part of the 1.7.0 Release.

```bash
# Example:
$ git log origin/master..origin/gwright99/25_2_0_update --oneline
```


## 1.8.0 (Upcoming Release -- Q1 2026)
- **Forward Roadmap Guidance**

    TBD

- **Notable Changes**
    - **CX Installer**
        - General
            - Added Studios SSH support. Requires Platform >= v25.3.3 and connect-proxy >= 0.10.0. [`#313`](https://github.com/seqeralabs/cx-field-tools-installer/issues/313)
            - Updated Platform Connect containers version to 0.11.0.
            - Updated Studios recommended base images.
            - Raised wave-lite nginx `client_max_body_size` from 1m to 10m to prevent HTTP 413 errors when Fusion uploads large bin/ bundles. [`#315`](https://github.com/seqeralabs/cx-field-tools-installer/issues/315)
            - Refactored `connection_strings` module to v2.0.0: streamlined module invocation (caller now resolves user-facing flags into mode strings — `platform_security_mode`, `platform_db_deployment`, `platform_redis_deployment`, `studio_mode`, `wave_mode` — before passing to the module, reducing input surface), and rationalized value generation (replaced interleaved flag ternaries with three logical sections: dispatch tables, single-step mode resolution, then composed final URLs). v1.0.0 deleted due to loss of supporting functions like `data "external"` (_see below_).
            - Removed the `data "external"` Python script for the DB connection-string suffix; logic now lives as a pure-HCL local conditional on engine version.
            - Migrated 12 single-variable validation checks from `scripts/installer/validation/check_configuration.py` to native Terraform `validation` blocks in `variables.tf` — `tower_server_url`, `tower_root_users`, `tower_db_url`, `tower_db_driver`, `tower_db_dialect`, `db_engine_version`, `db_container_engine_version`, `tower_container_version`, `data_studio_eligible_workspaces`, `data_studio_ssh_eligible_workspaces`, `pipeline_versioning_eligible_workspaces`, `private_cacert_bucket_prefix`. Errors now fire at plan time (earlier than the pre-plan Python script) and are co-located with each variable's declaration. Cross-variable and warning-only checks remain in the Python script.
            - TBD
        <br /><br />

        - Security
            - TBD
        <br/><br/>

        - Documentation
            - Added Studios SSH design decision to `design_decisions.md`. [`#313`](https://github.com/seqeralabs/cx-field-tools-installer/issues/313)
            - Updated `TEMPLATE_terraform.tfvars` with Studios SSH variables and configuration guidance. [`#313`](https://github.com/seqeralabs/cx-field-tools-installer/issues/313)
            - Added explicit Tower user auto-creation flags (`flag_tower_enable_participant_auto_create_user`, `flag_tower_enable_member_auto_create_user`) to `TEMPLATE_terraform.tfvars`. [`#312`](https://github.com/seqeralabs/cx-field-tools-installer/issues/312)
            - TBD
        <br /><br />

        - Testing
            - Updated baseline tests for new Studios 0.11.0 connect-proxy version.
            - Added parametrized round-based regression test for the 12 migrated single-variable validations (`tests/unit/variable_validation/`); new Makefile recipes (`run_tests_all`, `run_tests_core_only`, `run_tests_containers_only`, `run_tests_variables_only`, `run_tests_core_and_containers`, `run_tests_core_and_variables`) for marker-based test slicing.
            - Split the AWS SSO preflight out of the universal `session_setup` fixture into a dedicated opt-in `aws_preflight` fixture. Tests that interact with real AWS list `aws_preflight` as a fixture parameter; `tests/unit/` no longer requires the `aws` CLI. Closes [`#351`](https://github.com/seqeralabs/cx-field-tools-installer/issues/351).
            - Phase 1 of the `hcl2json` Docker-overhead removal (linux/amd64): added `extract_hcl2json` Makefile recipe that pulls the Go binary out of the vendored container once at setup time and places it at `/tmp/cx-installer/hcl2json` (project-namespaced so bwrap-style sandboxes can mount the directory into the jail); wired the recipe as a prerequisite on `verify` and every `run_tests_*` target. `scripts/installer/utils/extractors.py` now dispatches to the extracted binary (~10-50 ms/call instead of ~1-2 s) on supported hosts, fails fast with an instructional message when the binary is missing on a supported host, and keeps the per-call `docker run` fallback for unsupported hosts (Darwin until Phase 3). `tests/conftest.py` uses the shared helper instead of an inline `docker run`. Net effect: `tests/unit/` is runnable in sandboxed environments where Docker is blocked at runtime, provided extraction happened outside the sandbox (or `/tmp/cx-installer/` is mounted into it). [`#352`](https://github.com/seqeralabs/cx-field-tools-installer/issues/352)
            - TBD


### Configuration File Changes
#### `terraform.tfvars`
| Status | Component | Parameter Name | Description |
| ------ | --------- | -------------- | ----------- |
| New | Studios SSH | `flag_enable_data_studio_ssh` | Master toggle to enable SSH access into running Studio sessions. Requires `flag_enable_data_studio = true` and Platform >= v25.3.3. When enabled, a dedicated NLB is provisioned (if `flag_create_load_balancer = true`) and a `connect-ssh.<tower_server_url>` DNS record is created. |
| New | Studios SSH | `flag_limit_data_studio_ssh_to_some_workspaces` | When `true`, restricts SSH access to the workspace IDs listed in `data_studio_ssh_eligible_workspaces`. When `false`, SSH is available to all workspaces. |
| New | Studios SSH | `data_studio_ssh_eligible_workspaces` | Comma-separated list of numeric workspace IDs that are permitted to use Studios SSH. Only evaluated when `flag_limit_data_studio_ssh_to_some_workspaces = true`. |
||||
| New | Tower Auth | `flag_tower_enable_participant_auto_create_user` | Controls Tower's `tower.participant.auto-create-user`. When `true`, allows a workspace participant to be auto-created when added by email. Defaults to `false`. [`#312`](https://github.com/seqeralabs/cx-field-tools-installer/issues/312) |
| New | Tower Auth | `flag_tower_enable_member_auto_create_user` | Controls Tower's `tower.member.auto-create-user`. When `true`, allows the underlying User entity to be auto-created when an email is added as an Org Member. Defaults to `false`. [`#312`](https://github.com/seqeralabs/cx-field-tools-installer/issues/312) |
||||
| Modified | Studios | `data_studio_container_version` | Updated from 0.9.0 to 0.11.0. Note: Studios SSH requires connect-proxy >= 0.10.0. |
| Modified | Studios | `data_studio_options` | Removed 0.9.0 images and added 0.11.0 images. |
||||
| New | Redis | `platform_redis_elasticache` | Configuration block (`node_type`, `num_cache_nodes`, `engine_version`, `port`) for the standalone Seqera Platform ElastiCache (Redis) cluster. Required when `flag_create_external_redis = true`. |
||||




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
