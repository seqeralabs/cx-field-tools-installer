# Security


## Hardening the Installer Project

We use [tfsec](https://github.com/aquasecurity/tfsec) to scan this project for vulnerabilities. 

The latest scan was conducted **mid April 2024**, with highlighted vulnerabilities and fixes being tracked and actioned in [Issue #36 - Fix tfsec-identified Critical/High vulnerabilities](https://github.com/seqeralabs/cx-field-tools-installer/issues/36).


### Patching vs Suppression vs Ignoring Reported Vulnerabilites

While it would be ideal to completely fix all reported issues, there are a few-complicating factors to be considered:

- **Testing vs Production**

    Setting RDS config values like `skip_final_snapshot = false` and `deletion_protection = true` make absolute sense in a Production setting where it is highly unlikely one wants to destroy their database instance after it is created. 

    These settings, however, interfere with the orderly spin-up/spin-down of resources created during a testing loop (_i.e. terraform goes into an infinite loop waiting for a resource to be destroyed that cant be destroyed due actions taken by AWS as a result of these settings_).


- **Uncertain cost implications due to cost of feature activation**

    Some best practice features will generate real-world costs in your cloud account. While these costs are generally expected to be small, the fact that this cannot be 100% guaranteed from the outset means that these features should be treated as "opt-in" / "opt-out" rather than strictly hardcoded. 

    Other features that do not have any additional cost by default can be hardcoded as true due to the zero-cost gains that are achieved.

    Example: 
    - Unquantified cost: [VPC Flow logs](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html#flow-logs-pricing)
    - No cost with default options: [RDS Performance Insights](https://aws.amazon.com/rds/performance-insights/pricing/)


- **Necessity of feature**

    Some features, like configuring redis snapshot retention, arent necessary given how the Seqera Platform application works.


### Mitigation approach

The following approach is being followed to mitigate vulnerabilities:

1. Hardcode best practices where appropriate.
    Example: RDS Performance Insights (_7-day retention_).

2. Use _tfvars_ flags for toggle-able settings.
    Example: Make RDS `deletion_protection` configurable, with default set to `true`.

3. Add checks to configuration checker to emit reminders/warnings.

4. Suppress `tfsec` warnings for configurations handled by 2 & 3.


### Tfsec suppressions in place

!!! warn "Trivy reporting errors on inner module config"

    Some errors are being suppressed due to Trivy going too deep into module paths and reporting false positives (_i.e. multiple from the VPC examples folder_). Suppressing to minimize noise in scans to ensure real problems are not drowned out.

    NOTE: I don't like using top-level overrides via `.trivyignore` but inline exceptions dont appear to be working.


Managed via [`.trivyignore`](../.trivyignore):

- [VPC](../001_vpc.tf)
    - Log group is not encrypted: [`avd-aws-0017`](https://avd.aquasec.com/misconfig/avd-aws-0017)
    - LogGroup wildcard: [`avd-aws-0057`](https://avd.aquasec.com/misconfig/avd-aws-0057)
    - Default VPC used: [`avd-aws-0101`](https://avd.aquasec.com/misconfig/avd-aws-0101)
    - Network ACL rule allows access on ALL ports: [`avd-aws-0102`](https://avd.aquasec.com/misconfig/aws/ec2/avd-aws-0102/)
    - Network ACL rule allows ingress from public internet: [`avd-aws-0105`](https://avd.aquasec.com/misconfig/aws/ec2/avd-aws-0105/)
    - Flow Log Enablement: [`avd-aws-0178`](https://avd.aquasec.com/misconfig/aws/ec2/avd-aws-0178/)


- [Security Groups](../002_security_groups.tf)
    - Allowed egress to multiple public internet addresses (_multiple_): [`avd-aws-0104`](https://avd.aquasec.com/misconfig/avd-aws-0104)
    - Security group rule allows ingress from public internet: [`avd-aws-0107](https://avd.aquasec.com/misconfig/avd-aws-0107)


- [RDS](../003_database.tf)
    - Instance does not have Deletion Protect: [`avd-aws-0177`]https://avd.aquasec.com/misconfig/avd-aws-0177)
    - Instance does not have performance insights enabled: ['avd-aws-0133`](https://avd.aquasec.com/misconfig/avd-aws-0133)
    - Instance has very low backup retention period: [`avd-aws-0077`](https://avd.aquasec.com/misconfig/avd-aws-0077)
    - Instance does not have storage encryption enabled: [`avd-aws-0080`](https://avd.aquasec.com/misconfig/avd-aws-0080)


- [Elasticache (Redis)]((../003_database.tf))
    - `ignore:aws-elasticache-enable-backup-retention`


- [EC2](../006_ec2.tf)
    - Instance does not required IMDS token: [`avd-aws-0028`](https://avd.aquasec.com/misconfig/avd-aws-0028)
    - Launch Template does not require IMDS token: [`avd-aws-0130`](https://avd.aquasec.com/misconfig/avd-aws-0130)
    - Root block device is not encrypted: [`avd-aws-0131`](https://avd.aquasec.com/misconfig/avd-aws-0131)


- [Load Balancer](../007_load_balancer.tf)
    - Listener uses an outdated TLS policy: [`avd-aws-0047`](https://avd.aquasec.com/misconfig/avd-aws-0047)
    - Application load balancer not dropping invalid headers: [`avd-aws-0052`](https://avd.aquasec.com/misconfig/avd-aws-0052)
    - Load balancer is exposed publicly: [`avd-aws-0053`](https://avd.aquasec.com/misconfig/avd-aws-0053)
    - Listener does not use HTTPS: [`avd-aws-0054`](https://avd.aquasec.com/misconfig/avd-aws-0054)


## Hardening Cloud Objects Created By The Project

We must balance security with convenience: 

- If the project is too strict on security, deployment efforts can be significantly slowed as a myriad of connectivity problems emerge and must be resolved. 
- Conversely, deployments with no security expose our clients to unnecessary risks which could have been easily mitigated with a few easy-to-make decisions.

We try to expose suggested best practices, but it **ultimately the implementer's decision re: what is best for their organization**. As you make this decision, please be mindful of the following items.


### AMI Updating 

By default, the installer will try to grab the [very latest Amazon Linux 2023 AMI available](https://github.com/seqeralabs/cx-field-tools-installer/blob/master/006_ec2.tf#L1-L25) in your region. 

This is generally seen as a good idea because it ensures security/application patches are introduced into your environment regularly. Unfortunately, it can occasionally cause VMs to be destroyed and replaced (_potentially resulting in the loss of data if the implementation is using the container db_) and can also knock highly regulated installations out of compliance (_i.e. if an AMI is auto-replaced without the necessary paperwork). 

As of Release 1.3, more control has been introduced to allow implementers to pick a pattern which best fits their needs. [Reference Issue](https://github.com/seqeralabs/cx-field-tools-installer/issues/73)


## Egress Rules

Depending on the pipelines your run, many calls may need to egress from your Seqera Platform / Compute Environment to a variety of endpoints exposed on the public internet. 

For ease of deployment, the installer starts from a very loose posture re: security egress controls (`0.0.0.0/0`). While this helps minimize stand-up efforts, it may be inappropriate for your eventual Production deployment stance. Please me mindful of this behaviour and lockdown as necessary once 'happy path' pipeline runs prove successful.