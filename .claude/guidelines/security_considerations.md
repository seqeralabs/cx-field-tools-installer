# Security Considerations

- Sensitive values are stored in AWS SSM Parameter Store only — never in `terraform.tfvars` or repo-tracked files.
- Private-subnet access uses AWS Instance Connect Endpoint with `ProxyCommand`.
- Template files use the `.tpl` extension to avoid accidental secret exposure via filename pattern matching.
- Custom certificates are supported via [`assets/src/customcerts/`](../../assets/src/customcerts/).
- Run `make verify-full` to invoke `tfsec` security scanning before applying.
