# Private Certificates

This solution can support the use of private TLS certificates to secure your Seqera Platform (SP) instance endpoints, but requires some minor one-time setup by you prior to deployment.

Two flows are supported:

1. Bootstrapping a self-signed Certificate Authority (CA) and creating a new leaf certificate.
2. Use of a pre-existing leaf certificate signed by your own private CA.

**NOTE:** Seqera strongly recommends you use a traditional ALB with public certificate approach, if possible, as this will simplify your experience getting other parts of the Seqera ecosystem to connect to your SP instance.


## Prerequisites
- You will need an S3 bucket to store your certificates & keys.
- **_NOTE: You are responsible for implementing necessary security restrictions on the prefix where the certs and keys will be stored._**


## Constraints
The provided solution assumes the following:

1. Root CA files will be called `rootCA.crt` and `rootCA.key`.
2. Leaf files will be called `<YOUR_SP_DOMAIN>.crt` and `<YOUR_SP_DOMAIN>.key`.
3. All Root CA & Leaf files will be stored in the same S3 prefix.


## Configuration
### Generate Certificate
#### Bootstrapping a new CA
In this flow, we create a new self-signed Certificate Authority and issue a leaf cert to cover your Seqera Platform instance.

1. Collect DNS names.

    1. SP (_mandatory_)
        1. The value specified in _terraform.tfvars_ `tower_server_url`. 

    1. Studios (_optional_)
        1. If using subdomain routing, the value will be `*.<VALUE_OF_tower_server_url>`<br />(_Project hardcodes `connect.<VALUE_OF_tower_server_url>` and actual Studios use `<RANDOM_ALPHANUMERIC>.<VALUE_OF_tower_server_url>`_).<br /><br />
        2. If using path-based routing (available v25.2.0+), it is the value specified in _terraform.tfvars_ `data_studio_path_routing_url`.

    1. Wave-Lite (_optional_)
        1. The value specified in _terraform.tfvars_ `wave_lite_server_url` (_remove prefix_).

1. Create certificate assets.

    1. Within the project, navigate via commandline to `assets/src/customcert`.

    1. Execute the following (_omit the Studios and/or Wave-Lite entries if not applicable_): `./create_self_signed_cert.sh <SP_DNS> <STUDIOS_DNS> <WAVE_LITE_DNS>`. This will create your certificate assets.

        **Example:** `./create_self_signed_cert.sh autodc.dev-seqera.net autoconnect.dev-seqera.net autowave.dev-seqera.net` will create the following (_these will be used for illustration purposes in the rest of the steps_):
        
        - `rootCA.crt`
        - `rootCA.key`
        - `autodc.dev-seqera.net.crt`
        - `autodc.dev-seqera.net.key`

    1. Copy the following files to the chosen S3 prefix (_e.g. s3://example_bucket/sp_cert_files_):

        - `rootCA.crt`
        - `rootCA.key`
        - `autodc.dev-seqera.net.crt`
        - `autodc.dev-seqera.net.key`

    1. Delete all generated files:

        - `rootCA.crt`
        - `rootCA.key`
        - `autodc.dev-seqera.net.crt`
        - `autodc.dev-seqera.net.key`

1. Update _terraform.tfvars_ `private_cacert_bucket_prefix` with the S3 prefix (_e.g. s3://example_bucket/sp_cert_files_).


#### Using a certificate from an existing CA
In this flow, you use a leaf certificate issued by an existing private CA managed by your organization. **Assumption: You previously evaluated what DNS names were required and included them in the certificate request.**

1. Load certificate assets to S3.

    1. Copy the following files to the chosen S3 prefix (_e.g. s3://example_bucket/sp_cert_files_):

        - `rootCA.crt`
        - `autodc.dev-seqera.net.crt`
        - `autodc.dev-seqera.net.key`

1. Update _terraform.tfvars_ `private_cacert_bucket_prefix` with the S3 prefix (_e.g. s3://example_bucket/sp_cert_files_).


### Update permissions granted to EC2 instance created by Terraform
Manually update the IAM permissions granted to the EC2 instance so it can access your certificate-holding Bucket.

1. Update `assets/src/aws/iam_role_policy_ec2.json.tpl`:
    
    1. Modify Sid `AllObjectActions`, adding another ARN entry for your S3 prefix (_e.g. `arn:aws:s3::example_bucket/sp_cert_files/*`).


## Prepare Compute Assets
### Studios Custom Images with Private Certificates
When using private certificates with Studios, you must create custom container images that include your root CA certificate. This project provides a helper script to automate this process.

**Prerequisites:**
- Docker installed and running
- AWS CLI configured with appropriate permissions
- An AWS ECR repository created for your custom Studios images

**Process:**
1. Navigate to the certificate assets directory:
   ```bash
   cd assets/src/customcerts
   ```

2. Use the provided helper script to bake your root CA certificate into the Studios image:
   ```bash
   ./studios-private-cert-helper.sh <base-image> <cert-file> [new-tag] [alias] [ecr-uri]
   ```

   **Examples:**
   - **Local build only:**
     ```bash
     ./studios-private-cert-helper.sh public.cr.seqera.io/platform/data-studio-xpra:6.2.0-r2-1-0.8 ./rootCA.crt
     ```

   - **Build and push to ECR:**
     ```bash
     ./studios-private-cert-helper.sh \
       public.cr.seqera.io/platform/data-studio-xpra:6.2.0-r2-1-0.8 \
       ./rootCA.crt \
       seqera/xpra:with-ca \
       corp_ca \
       123456789012.dkr.ecr.eu-west-1.amazonaws.com/xpra:with-ca
     ```

**Important Notes:**
- **ECR Support Only:** The script currently supports AWS ECR repositories only. You must create an ECR repository before using the push functionality.
- **Custom Image Configuration:** After creating your custom image, you'll need to configure Studios to use it. See the [Seqera Platform Enterprise documentation on custom containers](https://docs.seqera.io/platform-enterprise/25.1/studios/custom-envs#custom-containers) for detailed instructions.
- **Multiple Image Types:** You may need to create custom images for different Studios environments (e.g., Jupyter, RStudio, VSCode) if you use multiple types.

### Other Compute Assets
- TODO: Bake cert into Nextflow worker nodes using Wave-Lite.


## Runtime
At runtime, if you make `flag_use_private_cacert = true`, the preloaded certificate files will be pulled during the deployment and made available to your SP instance.
