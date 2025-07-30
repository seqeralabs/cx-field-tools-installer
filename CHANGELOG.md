# CHANGELOG
> Last updated: July 27, 2025

This file was created post 1.5.0 Release.

```
$ git log origin/master..origin/gwright99/25_2_0_update --oneline
$ git log origin/gwright99/25_2_0_update..origin/gwright99/25-2-fix-private-certs --oneline

8a54dd1 Checkpoint: Make Studio distroless regex more flexible.

e9b4f9e Checkpoint: Purged extraneous private certificate variables and copying logic that does not conform with new one-time manual write flow.
```

## 2.0.0

### Feature Updates & Improvements
- **Breaking Changes**:
    - Private certificates served from deployed EC2 must now be pre-loaded to S3 Bucket prior to deployment.

- **Notable Changes**:
    - **Seqera Ecosytem**
        - (Platform) -- Crypto secret rotation added.

        - (Studios)  -- Studios path-based routing supported for ALB & EC2-direct flow.

        - (Wave) -- Wave-Lite support introduced.


    - **CX Installer**
        - (General) -- Began experimenting producing code with AI. Efforts are tightly scoped and 100% human supervised thus far.
        <br /><br />
        - (Architecture) -- Subnet reconcilation logic centralized in module `subnet_collector`.
        - (Architecture) -- URL / connection string generation logic centralized in module `connection_strings`.
        - (Architecture) -- Changed private certificate flow: Certs must now be pre-loaded to S3 bucket & are pulled at run-time.
        - (Architecture) -- Refactored `assets/src/customcerts/`: Generation script supports multiple domains & removed placeholder files.
        - (Architecture) -- Modified security groups `sg_ec2_noalb` & `sg_ec2_noalb_connect` for tighter scoping.
        - (Architecture) -- Refactored when most `assets/target/` files are produced. Rather than waiting for all infrastructure to be created, we now create files as soon as minimal dependencies are met (_to facilitate testing_).
        <br /><br />
        - (Security) -- Bumped `java-17-amazon-corretto-devel-1:17.0.14+7-1.amzn2023.1` to `1:17.0.15+6-1.amzn2023.1`.
        - (Security) -- Bumped docker version from `28.1.1` --> `28.3.1`.
        <br /><br />
        - (Documentation) -- Changed `TEMPLATE_terraform.tfvars` application name from `tower-dev` to `tower-template`.
        - (Documentation) -- Added Design Decision explaining why Studio subdomain routing is the default over path-based routing.
        - (Documentation) -- Added Setup guidance re: Platform crypto secret rotation.
        - (Documentation) -- Added Setup guidance re: how to prepare / pre-loaded Private Certificates.
        <br /><br />
        - (Validation) -- Added Studios path-based routing checks & warnings.
        <br /><br />
        - (Testing) -- Added preliminary testing framework. Validates outputs of `module.connection_strings` and some files in `assets/target/`.
        - (Testing) -- Added preliminary MySQL & Postgres & Docker Compose Testcontainers for local validation.
        - (Testing) -- Added test data generation (tfvars & secrets) mechanism.
        - (Testing) -- Added test logging facility (via Pytest lifecycle hooks) to facilitate human observability and AI agent resolution.
        - (Testing) -- Added Pytest marks to allow for targeted test runs.
        - (Testing) -- Added `terraform plan` caching mechanism to speed up n+1 tests.


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

### Security Updates

- TODO: Add the updates done (if any as part of Wave-Lite initial work)


