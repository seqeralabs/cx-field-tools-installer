# Optional Config - Review your Terraform state storage strategy

By default, the installer writes the Terraform state to a local folder (`<PROJECT_ROOT>/DONTDELETE`). This is convenient for initial testing but likely not a good long-term solution for most clients. 

You can change the state management strategy at the top of the [`000-main.tf`](../../000_main.tf) file. We have provided a commented-out example that demonstrates how to write state to an S3 bucket.

**Note:** Bulletproof state management can become complex and is beyond the scope of this initiative. Consult Terraform's official docs on [Remote State](https://developer.hashicorp.com/terraform/language/state/remote) and modify your project as necessary to meet your organization's needs.
