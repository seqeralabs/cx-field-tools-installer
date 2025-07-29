<!-- BEGIN_TF_DOCS -->
## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | 5.12.0 |
| <a name="provider_external"></a> [external](#provider\_external) | 2.3.3 |
| <a name="provider_null"></a> [null](#provider\_null) | 3.2.2 |
| <a name="provider_random"></a> [random](#provider\_random) | 3.6.2 |
| <a name="provider_tls"></a> [tls](#provider\_tls) | 4.0.5 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_alb"></a> [alb](#module\_alb) | terraform-aws-modules/alb/aws | 8.7.0 |
| <a name="module_elasticache_wave_lite"></a> [elasticache\_wave\_lite](#module\_elasticache\_wave\_lite) | ./modules/elasticache | n/a |
| <a name="module_rds"></a> [rds](#module\_rds) | terraform-aws-modules/rds/aws | 6.1.1 |
| <a name="module_rds-wave-lite"></a> [rds-wave-lite](#module\_rds-wave-lite) | terraform-aws-modules/rds/aws | 6.1.1 |
| <a name="module_tower_alb_sg"></a> [tower\_alb\_sg](#module\_tower\_alb\_sg) | terraform-aws-modules/security-group/aws | 5.1.0 |
| <a name="module_tower_batch_sg"></a> [tower\_batch\_sg](#module\_tower\_batch\_sg) | terraform-aws-modules/security-group/aws | 5.1.0 |
| <a name="module_tower_db_sg"></a> [tower\_db\_sg](#module\_tower\_db\_sg) | terraform-aws-modules/security-group/aws | 5.1.0 |
| <a name="module_tower_ec2_alb_connect_sg"></a> [tower\_ec2\_alb\_connect\_sg](#module\_tower\_ec2\_alb\_connect\_sg) | terraform-aws-modules/security-group/aws | 5.1.0 |
| <a name="module_tower_ec2_alb_sg"></a> [tower\_ec2\_alb\_sg](#module\_tower\_ec2\_alb\_sg) | terraform-aws-modules/security-group/aws | 5.1.0 |
| <a name="module_tower_ec2_alb_wave_sg"></a> [tower\_ec2\_alb\_wave\_sg](#module\_tower\_ec2\_alb\_wave\_sg) | terraform-aws-modules/security-group/aws | 5.1.0 |
| <a name="module_tower_ec2_direct_connect_sg"></a> [tower\_ec2\_direct\_connect\_sg](#module\_tower\_ec2\_direct\_connect\_sg) | terraform-aws-modules/security-group/aws | 5.1.0 |
| <a name="module_tower_ec2_direct_sg"></a> [tower\_ec2\_direct\_sg](#module\_tower\_ec2\_direct\_sg) | terraform-aws-modules/security-group/aws | 5.1.0 |
| <a name="module_tower_ec2_egress_sg"></a> [tower\_ec2\_egress\_sg](#module\_tower\_ec2\_egress\_sg) | terraform-aws-modules/security-group/aws | 5.1.0 |
| <a name="module_tower_ec2_ssh_sg"></a> [tower\_ec2\_ssh\_sg](#module\_tower\_ec2\_ssh\_sg) | terraform-aws-modules/security-group/aws | 5.1.0 |
| <a name="module_tower_eice_egress_sg"></a> [tower\_eice\_egress\_sg](#module\_tower\_eice\_egress\_sg) | terraform-aws-modules/security-group/aws | 5.1.0 |
| <a name="module_tower_eice_ingress_sg"></a> [tower\_eice\_ingress\_sg](#module\_tower\_eice\_ingress\_sg) | terraform-aws-modules/security-group/aws | 5.1.0 |
| <a name="module_tower_interface_endpoint_sg"></a> [tower\_interface\_endpoint\_sg](#module\_tower\_interface\_endpoint\_sg) | terraform-aws-modules/security-group/aws | 5.1.0 |
| <a name="module_tower_redis_sg"></a> [tower\_redis\_sg](#module\_tower\_redis\_sg) | terraform-aws-modules/security-group/aws | 5.1.0 |
| <a name="module_vpc"></a> [vpc](#module\_vpc) | terraform-aws-modules/vpc/aws | 5.1.2 |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_alb_certificate_arn"></a> [alb\_certificate\_arn](#input\_alb\_certificate\_arn) | n/a | `string` | n/a | yes |
| <a name="input_app_name"></a> [app\_name](#input\_app\_name) | n/a | `string` | n/a | yes |
| <a name="input_aws_account"></a> [aws\_account](#input\_aws\_account) | n/a | `string` | n/a | yes |
| <a name="input_aws_profile"></a> [aws\_profile](#input\_aws\_profile) | n/a | `string` | n/a | yes |
| <a name="input_aws_region"></a> [aws\_region](#input\_aws\_region) | n/a | `string` | n/a | yes |
| <a name="input_private_cacert_bucket_prefix"></a> [bucket\_prefix\_for\_new\_private\_ca\_cert](#input\_bucket\_prefix\_for\_new\_private\_ca\_cert) | n/a | `string` | n/a | yes |
| <a name="input_custom_resource_naming_prefix"></a> [custom\_resource\_naming\_prefix](#input\_custom\_resource\_naming\_prefix) | n/a | `string` | n/a | yes |
| <a name="input_data_explorer_disabled_workspaces"></a> [data\_explorer\_disabled\_workspaces](#input\_data\_explorer\_disabled\_workspaces) | n/a | `string` | n/a | yes |
| <a name="input_data_studio_container_version"></a> [data\_studio\_container\_version](#input\_data\_studio\_container\_version) | n/a | `string` | n/a | yes |
| <a name="input_data_studio_eligible_workspaces"></a> [data\_studio\_eligible\_workspaces](#input\_data\_studio\_eligible\_workspaces) | n/a | `string` | n/a | yes |
| <a name="input_data_studio_options"></a> [data\_studio\_options](#input\_data\_studio\_options) | n/a | <pre>map(object({<br/>    qualifier = string<br/>    icon = string<br/>    tool = optional(string)<br/>    status = optional(string)<br/>    container = string<br/>  }))</pre> | n/a | yes |
| <a name="input_db_allocated_storage"></a> [db\_allocated\_storage](#input\_db\_allocated\_storage) | n/a | `number` | n/a | yes |
| <a name="input_db_backup_retention_period"></a> [db\_backup\_retention\_period](#input\_db\_backup\_retention\_period) | n/a | `number` | n/a | yes |
| <a name="input_db_container_engine"></a> [db\_container\_engine](#input\_db\_container\_engine) | n/a | `string` | n/a | yes |
| <a name="input_db_container_engine_version"></a> [db\_container\_engine\_version](#input\_db\_container\_engine\_version) | n/a | `string` | n/a | yes |
| <a name="input_db_database_name"></a> [db\_database\_name](#input\_db\_database\_name) | n/a | `string` | n/a | yes |
| <a name="input_db_deletion_protection"></a> [db\_deletion\_protection](#input\_db\_deletion\_protection) | n/a | `bool` | n/a | yes |
| <a name="input_db_enable_storage_encrypted"></a> [db\_enable\_storage\_encrypted](#input\_db\_enable\_storage\_encrypted) | n/a | `bool` | n/a | yes |
| <a name="input_db_engine"></a> [db\_engine](#input\_db\_engine) | n/a | `string` | n/a | yes |
| <a name="input_db_engine_version"></a> [db\_engine\_version](#input\_db\_engine\_version) | n/a | `string` | n/a | yes |
| <a name="input_db_instance_class"></a> [db\_instance\_class](#input\_db\_instance\_class) | n/a | `string` | n/a | yes |
| <a name="input_db_param_group"></a> [db\_param\_group](#input\_db\_param\_group) | n/a | `string` | n/a | yes |
| <a name="input_default_tags"></a> [default\_tags](#input\_default\_tags) | n/a | `map(string)` | n/a | yes |
| <a name="input_docker_cidr_range"></a> [docker\_cidr\_range](#input\_docker\_cidr\_range) | n/a | `string` | n/a | yes |
| <a name="input_ec2_ebs_kms_key"></a> [ec2\_ebs\_kms\_key](#input\_ec2\_ebs\_kms\_key) | n/a | `string` | n/a | yes |
| <a name="input_ec2_host_instance_type"></a> [ec2\_host\_instance\_type](#input\_ec2\_host\_instance\_type) | n/a | `string` | n/a | yes |
| <a name="input_ec2_require_imds_token"></a> [ec2\_require\_imds\_token](#input\_ec2\_require\_imds\_token) | n/a | `bool` | n/a | yes |
| <a name="input_ec2_root_volume_size"></a> [ec2\_root\_volume\_size](#input\_ec2\_root\_volume\_size) | n/a | `number` | n/a | yes |
| <a name="input_ec2_update_ami_if_available"></a> [ec2\_update\_ami\_if\_available](#input\_ec2\_update\_ami\_if\_available) | n/a | `bool` | n/a | yes |
| <a name="input_wave_lite_elasticache "></a> [elasticache\_wave\_instance](#input\_elasticache\_wave\_instance) | Configuration for the Wave Elasticache instance including networking, clustering, and encryption settings | <pre>object({<br/>    apply_immediately = bool<br/>    engine            = string<br/>    engine_version    = string<br/>    node_type         = string<br/>    port              = number<br/><br/>    security_group_ids = list(string)<br/>    subnet_ids         = list(string)<br/><br/>    unclustered = object({<br/>      num_cache_nodes = number<br/>    })<br/><br/>    clustered = object({<br/>      multi_az_enabled           = bool<br/>      automatic_failover_enabled = bool<br/>      num_node_groups            = optional(number)<br/>      replicas_per_node_group    = optional(number)<br/>      parameter_group_name       = string<br/>    })<br/><br/>    encryption = object({<br/>      auth_token                 = optional(string)<br/>      at_rest_encryption_enabled = bool<br/>      transit_encryption_enabled = bool<br/>      kms_key_id                 = optional(string)<br/>    })<br/>  })</pre> | n/a | yes |
| <a name="input_enable_vpc_flow_logs"></a> [enable\_vpc\_flow\_logs](#input\_enable\_vpc\_flow\_logs) | n/a | `bool` | n/a | yes |
| <a name="input_existing_ca_cert_file"></a> [existing\_ca\_cert\_file](#input\_existing\_ca\_cert\_file) | n/a | `string` | n/a | yes |
| <a name="input_existing_ca_key_file"></a> [existing\_ca\_key\_file](#input\_existing\_ca\_key\_file) | n/a | `string` | n/a | yes |
| <a name="input_existing_route53_private_zone_name"></a> [existing\_route53\_private\_zone\_name](#input\_existing\_route53\_private\_zone\_name) | n/a | `string` | n/a | yes |
| <a name="input_existing_route53_public_zone_name"></a> [existing\_route53\_public\_zone\_name](#input\_existing\_route53\_public\_zone\_name) | n/a | `string` | n/a | yes |
| <a name="input_flag_create_external_db"></a> [flag\_create\_external\_db](#input\_flag\_create\_external\_db) | n/a | `bool` | n/a | yes |
| <a name="input_flag_create_external_redis"></a> [flag\_create\_external\_redis](#input\_flag\_create\_external\_redis) | n/a | `bool` | n/a | yes |
| <a name="input_flag_create_hosts_file_entry"></a> [flag\_create\_hosts\_file\_entry](#input\_flag\_create\_hosts\_file\_entry) | n/a | `bool` | n/a | yes |
| <a name="input_flag_create_load_balancer"></a> [flag\_create\_load\_balancer](#input\_flag\_create\_load\_balancer) | n/a | `bool` | n/a | yes |
| <a name="input_flag_create_new_vpc"></a> [flag\_create\_new\_vpc](#input\_flag\_create\_new\_vpc) | n/a | `bool` | n/a | yes |
| <a name="input_flag_create_route53_private_zone"></a> [flag\_create\_route53\_private\_zone](#input\_flag\_create\_route53\_private\_zone) | n/a | `bool` | n/a | yes |
| <a name="input_flag_data_explorer_enabled"></a> [flag\_data\_explorer\_enabled](#input\_flag\_data\_explorer\_enabled) | n/a | `bool` | n/a | yes |
| <a name="input_flag_disable_email_login"></a> [flag\_disable\_email\_login](#input\_flag\_disable\_email\_login) | n/a | `bool` | n/a | yes |
| <a name="input_flag_do_not_use_https"></a> [flag\_do\_not\_use\_https](#input\_flag\_do\_not\_use\_https) | n/a | `bool` | n/a | yes |
| <a name="input_flag_docker_logging_journald"></a> [flag\_docker\_logging\_journald](#input\_flag\_docker\_logging\_journald) | n/a | `bool` | n/a | yes |
| <a name="input_flag_docker_logging_jsonfile"></a> [flag\_docker\_logging\_jsonfile](#input\_flag\_docker\_logging\_jsonfile) | n/a | `bool` | n/a | yes |
| <a name="input_flag_docker_logging_local"></a> [flag\_docker\_logging\_local](#input\_flag\_docker\_logging\_local) | n/a | `bool` | n/a | yes |
| <a name="input_flag_enable_data_studio"></a> [flag\_enable\_data\_studio](#input\_flag\_enable\_data\_studio) | n/a | `bool` | n/a | yes |
| <a name="input_flag_enable_groundswell"></a> [flag\_enable\_groundswell](#input\_flag\_enable\_groundswell) | n/a | `bool` | n/a | yes |
| <a name="input_flag_encrypt_ebs"></a> [flag\_encrypt\_ebs](#input\_flag\_encrypt\_ebs) | n/a | `bool` | n/a | yes |
| <a name="input_flag_generate_private_cacert"></a> [flag\_generate\_private\_cacert](#input\_flag\_generate\_private\_cacert) | n/a | `bool` | n/a | yes |
| <a name="input_flag_iam_use_prexisting_role_arn"></a> [flag\_iam\_use\_prexisting\_role\_arn](#input\_flag\_iam\_use\_prexisting\_role\_arn) | n/a | `bool` | n/a | yes |
| <a name="input_flag_limit_data_studio_to_some_workspaces"></a> [flag\_limit\_data\_studio\_to\_some\_workspaces](#input\_flag\_limit\_data\_studio\_to\_some\_workspaces) | n/a | `bool` | n/a | yes |
| <a name="input_flag_make_instance_private"></a> [flag\_make\_instance\_private](#input\_flag\_make\_instance\_private) | n/a | `bool` | n/a | yes |
| <a name="input_flag_make_instance_private_behind_public_alb"></a> [flag\_make\_instance\_private\_behind\_public\_alb](#input\_flag\_make\_instance\_private\_behind\_public\_alb) | n/a | `bool` | n/a | yes |
| <a name="input_flag_make_instance_public"></a> [flag\_make\_instance\_public](#input\_flag\_make\_instance\_public) | n/a | `bool` | n/a | yes |
| <a name="input_flag_oidc_use_generic"></a> [flag\_oidc\_use\_generic](#input\_flag\_oidc\_use\_generic) | n/a | `bool` | n/a | yes |
| <a name="input_flag_oidc_use_github"></a> [flag\_oidc\_use\_github](#input\_flag\_oidc\_use\_github) | n/a | `bool` | n/a | yes |
| <a name="input_flag_oidc_use_google"></a> [flag\_oidc\_use\_google](#input\_flag\_oidc\_use\_google) | n/a | `bool` | n/a | yes |
| <a name="input_flag_overwrite_ssm_keys"></a> [flag\_overwrite\_ssm\_keys](#input\_flag\_overwrite\_ssm\_keys) | Not to be used in PROD but helpful when sharing same instance in DEV. | `bool` | `false` | no |
| <a name="input_flag_private_tower_without_eice"></a> [flag\_private\_tower\_without\_eice](#input\_flag\_private\_tower\_without\_eice) | n/a | `bool` | n/a | yes |
| <a name="input_flag_run_seqerakit"></a> [flag\_run\_seqerakit](#input\_flag\_run\_seqerakit) | n/a | `bool` | n/a | yes |
| <a name="input_flag_use_aws_ses_iam_integration"></a> [flag\_use\_aws\_ses\_iam\_integration](#input\_flag\_use\_aws\_ses\_iam\_integration) | n/a | `bool` | n/a | yes |
| <a name="input_flag_use_container_db"></a> [flag\_use\_container\_db](#input\_flag\_use\_container\_db) | n/a | `bool` | n/a | yes |
| <a name="input_flag_use_container_redis"></a> [flag\_use\_container\_redis](#input\_flag\_use\_container\_redis) | n/a | `bool` | n/a | yes |
| <a name="input_flag_use_custom_docker_compose_file"></a> [flag\_use\_custom\_docker\_compose\_file](#input\_flag\_use\_custom\_docker\_compose\_file) | n/a | `bool` | n/a | yes |
| <a name="input_flag_use_custom_resource_naming_prefix"></a> [flag\_use\_custom\_resource\_naming\_prefix](#input\_flag\_use\_custom\_resource\_naming\_prefix) | n/a | `bool` | n/a | yes |
| <a name="input_flag_use_existing_external_db"></a> [flag\_use\_existing\_external\_db](#input\_flag\_use\_existing\_external\_db) | n/a | `bool` | n/a | yes |
| <a name="input_flag_use_existing_private_cacert"></a> [flag\_use\_existing\_private\_cacert](#input\_flag\_use\_existing\_private\_cacert) | n/a | `bool` | n/a | yes |
| <a name="input_flag_use_existing_route53_private_zone"></a> [flag\_use\_existing\_route53\_private\_zone](#input\_flag\_use\_existing\_route53\_private\_zone) | n/a | `bool` | n/a | yes |
| <a name="input_flag_use_existing_route53_public_zone"></a> [flag\_use\_existing\_route53\_public\_zone](#input\_flag\_use\_existing\_route53\_public\_zone) | n/a | `bool` | n/a | yes |
| <a name="input_flag_use_existing_smtp"></a> [flag\_use\_existing\_smtp](#input\_flag\_use\_existing\_smtp) | n/a | `bool` | n/a | yes |
| <a name="input_flag_use_existing_vpc"></a> [flag\_use\_existing\_vpc](#input\_flag\_use\_existing\_vpc) | n/a | `bool` | n/a | yes |
| <a name="input_flag_use_kms_key"></a> [flag\_use\_kms\_key](#input\_flag\_use\_kms\_key) | n/a | `bool` | n/a | yes |
| <a name="input_flag_use_wave"></a> [flag\_use\_wave](#input\_flag\_use\_wave) | n/a | `bool` | n/a | yes |
| <a name="input_flag_use_wave_lite"></a> [flag\_use\_wave\_lite](#input\_flag\_use\_wave\_lite) | n/a | `bool` | n/a | yes |
| <a name="input_flag_vm_copy_files_to_instance"></a> [flag\_vm\_copy\_files\_to\_instance](#input\_flag\_vm\_copy\_files\_to\_instance) | n/a | `bool` | n/a | yes |
| <a name="input_flyway_locations"></a> [flyway\_locations](#input\_flyway\_locations) | n/a | `string` | n/a | yes |
| <a name="input_iam_prexisting_instance_role_arn"></a> [iam\_prexisting\_instance\_role\_arn](#input\_iam\_prexisting\_instance\_role\_arn) | n/a | `string` | n/a | yes |
| <a name="input_new_route53_private_zone_name"></a> [new\_route53\_private\_zone\_name](#input\_new\_route53\_private\_zone\_name) | n/a | `string` | n/a | yes |
| <a name="input_secrets_bootstrap_groundswell"></a> [secrets\_bootstrap\_groundswell](#input\_secrets\_bootstrap\_groundswell) | SSM SecureString for Groundswell secrets. | `string` | n/a | yes |
| <a name="input_secrets_bootstrap_seqerakit"></a> [secrets\_bootstrap\_seqerakit](#input\_secrets\_bootstrap\_seqerakit) | SSM SecureString for Seqerakit secrets. | `string` | n/a | yes |
| <a name="input_secrets_bootstrap_tower"></a> [secrets\_bootstrap\_tower](#input\_secrets\_bootstrap\_tower) | SSM SecureString for Tower secrets. | `string` | n/a | yes |
| <a name="input_secrets_bootstrap_wave_lite"></a> [secrets\_bootstrap\_wave\_lite](#input\_secrets\_bootstrap\_wave\_lite) | SSM SecureString for Wave Lite secrets. | `string` | n/a | yes |
| <a name="input_seqerakit_aws_fusion_instances"></a> [seqerakit\_aws\_fusion\_instances](#input\_seqerakit\_aws\_fusion\_instances) | n/a | `string` | n/a | yes |
| <a name="input_seqerakit_aws_manual_compute_queue"></a> [seqerakit\_aws\_manual\_compute\_queue](#input\_seqerakit\_aws\_manual\_compute\_queue) | n/a | `string` | n/a | yes |
| <a name="input_seqerakit_aws_manual_head_queue"></a> [seqerakit\_aws\_manual\_head\_queue](#input\_seqerakit\_aws\_manual\_head\_queue) | n/a | `string` | n/a | yes |
| <a name="input_seqerakit_aws_normal_instances"></a> [seqerakit\_aws\_normal\_instances](#input\_seqerakit\_aws\_normal\_instances) | n/a | `string` | n/a | yes |
| <a name="input_seqerakit_aws_use_batch"></a> [seqerakit\_aws\_use\_batch](#input\_seqerakit\_aws\_use\_batch) | n/a | `bool` | n/a | yes |
| <a name="input_seqerakit_aws_use_forge"></a> [seqerakit\_aws\_use\_forge](#input\_seqerakit\_aws\_use\_forge) | n/a | `bool` | n/a | yes |
| <a name="input_seqerakit_aws_use_fusion_v2"></a> [seqerakit\_aws\_use\_fusion\_v2](#input\_seqerakit\_aws\_use\_fusion\_v2) | n/a | `bool` | n/a | yes |
| <a name="input_seqerakit_compute_env_name"></a> [seqerakit\_compute\_env\_name](#input\_seqerakit\_compute\_env\_name) | n/a | `string` | n/a | yes |
| <a name="input_seqerakit_compute_env_region"></a> [seqerakit\_compute\_env\_region](#input\_seqerakit\_compute\_env\_region) | n/a | `string` | n/a | yes |
| <a name="input_seqerakit_flag_credential_create_aws"></a> [seqerakit\_flag\_credential\_create\_aws](#input\_seqerakit\_flag\_credential\_create\_aws) | n/a | `bool` | n/a | yes |
| <a name="input_seqerakit_flag_credential_create_codecommit"></a> [seqerakit\_flag\_credential\_create\_codecommit](#input\_seqerakit\_flag\_credential\_create\_codecommit) | n/a | `bool` | n/a | yes |
| <a name="input_seqerakit_flag_credential_create_docker"></a> [seqerakit\_flag\_credential\_create\_docker](#input\_seqerakit\_flag\_credential\_create\_docker) | n/a | `bool` | n/a | yes |
| <a name="input_seqerakit_flag_credential_create_github"></a> [seqerakit\_flag\_credential\_create\_github](#input\_seqerakit\_flag\_credential\_create\_github) | n/a | `bool` | n/a | yes |
| <a name="input_seqerakit_flag_credential_use_aws_role"></a> [seqerakit\_flag\_credential\_use\_aws\_role](#input\_seqerakit\_flag\_credential\_use\_aws\_role) | n/a | `bool` | n/a | yes |
| <a name="input_seqerakit_flag_credential_use_codecommit_baseurl"></a> [seqerakit\_flag\_credential\_use\_codecommit\_baseurl](#input\_seqerakit\_flag\_credential\_use\_codecommit\_baseurl) | n/a | `bool` | n/a | yes |
| <a name="input_seqerakit_org_fullname"></a> [seqerakit\_org\_fullname](#input\_seqerakit\_org\_fullname) | n/a | `string` | n/a | yes |
| <a name="input_seqerakit_org_name"></a> [seqerakit\_org\_name](#input\_seqerakit\_org\_name) | n/a | `string` | n/a | yes |
| <a name="input_seqerakit_org_url"></a> [seqerakit\_org\_url](#input\_seqerakit\_org\_url) | n/a | `string` | n/a | yes |
| <a name="input_seqerakit_outdir"></a> [seqerakit\_outdir](#input\_seqerakit\_outdir) | n/a | `string` | n/a | yes |
| <a name="input_seqerakit_root_bucket"></a> [seqerakit\_root\_bucket](#input\_seqerakit\_root\_bucket) | n/a | `string` | n/a | yes |
| <a name="input_seqerakit_team_members"></a> [seqerakit\_team\_members](#input\_seqerakit\_team\_members) | n/a | `string` | n/a | yes |
| <a name="input_seqerakit_team_name"></a> [seqerakit\_team\_name](#input\_seqerakit\_team\_name) | n/a | `string` | n/a | yes |
| <a name="input_seqerakit_workdir"></a> [seqerakit\_workdir](#input\_seqerakit\_workdir) | n/a | `string` | n/a | yes |
| <a name="input_seqerakit_workspace_fullname"></a> [seqerakit\_workspace\_fullname](#input\_seqerakit\_workspace\_fullname) | n/a | `string` | n/a | yes |
| <a name="input_seqerakit_workspace_name"></a> [seqerakit\_workspace\_name](#input\_seqerakit\_workspace\_name) | n/a | `string` | n/a | yes |
| <a name="input_sg_egress_batch_ec2"></a> [sg\_egress\_batch\_ec2](#input\_sg\_egress\_batch\_ec2) | n/a | `list(string)` | n/a | yes |
| <a name="input_sg_egress_eice"></a> [sg\_egress\_eice](#input\_sg\_egress\_eice) | n/a | `list(string)` | n/a | yes |
| <a name="input_sg_egress_interface_endpoint"></a> [sg\_egress\_interface\_endpoint](#input\_sg\_egress\_interface\_endpoint) | n/a | `list(string)` | n/a | yes |
| <a name="input_sg_egress_tower_alb"></a> [sg\_egress\_tower\_alb](#input\_sg\_egress\_tower\_alb) | n/a | `list(string)` | n/a | yes |
| <a name="input_sg_egress_tower_ec2"></a> [sg\_egress\_tower\_ec2](#input\_sg\_egress\_tower\_ec2) | n/a | `list(string)` | n/a | yes |
| <a name="input_sg_ingress_cidrs"></a> [sg\_ingress\_cidrs](#input\_sg\_ingress\_cidrs) | n/a | `list(string)` | n/a | yes |
| <a name="input_sg_ssh_cidrs"></a> [sg\_ssh\_cidrs](#input\_sg\_ssh\_cidrs) | n/a | `list(string)` | n/a | yes |
| <a name="input_skip_final_snapshot"></a> [skip\_final\_snapshot](#input\_skip\_final\_snapshot) | n/a | `bool` | n/a | yes |
| <a name="input_swell_container_version"></a> [swell\_container\_version](#input\_swell\_container\_version) | n/a | `string` | n/a | yes |
| <a name="input_swell_database_name"></a> [swell\_database\_name](#input\_swell\_database\_name) | n/a | `string` | n/a | yes |
| <a name="input_tower_audit_retention_days"></a> [tower\_audit\_retention\_days](#input\_tower\_audit\_retention\_days) | n/a | `number` | n/a | yes |
| <a name="input_tower_contact_email"></a> [tower\_contact\_email](#input\_tower\_contact\_email) | n/a | `string` | n/a | yes |
| <a name="input_tower_container_version"></a> [tower\_container\_version](#input\_tower\_container\_version) | Harbor container version (i.e. tag: `v23.2.0`) | `string` | n/a | yes |
| <a name="input_tower_db_dialect"></a> [tower\_db\_dialect](#input\_tower\_db\_dialect) | n/a | `string` | n/a | yes |
| <a name="input_tower_db_driver"></a> [tower\_db\_driver](#input\_tower\_db\_driver) | n/a | `string` | n/a | yes |
| <a name="input_tower_db_max_lifetime"></a> [tower\_db\_max\_lifetime](#input\_tower\_db\_max\_lifetime) | n/a | `number` | n/a | yes |
| <a name="input_tower_db_max_pool_size"></a> [tower\_db\_max\_pool\_size](#input\_tower\_db\_max\_pool\_size) | n/a | `number` | n/a | yes |
| <a name="input_tower_db_min_pool_size"></a> [tower\_db\_min\_pool\_size](#input\_tower\_db\_min\_pool\_size) | n/a | `number` | n/a | yes |
| <a name="input_tower_db_url"></a> [tower\_db\_url](#input\_tower\_db\_url) | n/a | `string` | n/a | yes |
| <a name="input_tower_email_trusted_orgs"></a> [tower\_email\_trusted\_orgs](#input\_tower\_email\_trusted\_orgs) | n/a | `string` | n/a | yes |
| <a name="input_tower_email_trusted_users"></a> [tower\_email\_trusted\_users](#input\_tower\_email\_trusted\_users) | n/a | `string` | n/a | yes |
| <a name="input_tower_enable_platforms"></a> [tower\_enable\_platforms](#input\_tower\_enable\_platforms) | n/a | `string` | n/a | yes |
| <a name="input_tower_root_users"></a> [tower\_root\_users](#input\_tower\_root\_users) | n/a | `string` | n/a | yes |
| <a name="input_tower_server_port"></a> [tower\_server\_port](#input\_tower\_server\_port) | n/a | `string` | n/a | yes |
| <a name="input_tower_server_url"></a> [tower\_server\_url](#input\_tower\_server\_url) | n/a | `string` | n/a | yes |
| <a name="input_tower_smtp_auth"></a> [tower\_smtp\_auth](#input\_tower\_smtp\_auth) | n/a | `bool` | n/a | yes |
| <a name="input_tower_smtp_host"></a> [tower\_smtp\_host](#input\_tower\_smtp\_host) | n/a | `string` | n/a | yes |
| <a name="input_tower_smtp_port"></a> [tower\_smtp\_port](#input\_tower\_smtp\_port) | n/a | `string` | n/a | yes |
| <a name="input_tower_smtp_ssl_protocols"></a> [tower\_smtp\_ssl\_protocols](#input\_tower\_smtp\_ssl\_protocols) | n/a | `string` | n/a | yes |
| <a name="input_tower_smtp_starttls_enable"></a> [tower\_smtp\_starttls\_enable](#input\_tower\_smtp\_starttls\_enable) | n/a | `bool` | n/a | yes |
| <a name="input_tower_smtp_starttls_required"></a> [tower\_smtp\_starttls\_required](#input\_tower\_smtp\_starttls\_required) | n/a | `bool` | n/a | yes |
| <a name="input_vpc_existing_alb_subnets"></a> [vpc\_existing\_alb\_subnets](#input\_vpc\_existing\_alb\_subnets) | n/a | `list(string)` | n/a | yes |
| <a name="input_vpc_existing_batch_subnets"></a> [vpc\_existing\_batch\_subnets](#input\_vpc\_existing\_batch\_subnets) | n/a | `list(string)` | n/a | yes |
| <a name="input_vpc_existing_db_subnets"></a> [vpc\_existing\_db\_subnets](#input\_vpc\_existing\_db\_subnets) | n/a | `list(string)` | n/a | yes |
| <a name="input_vpc_existing_ec2_subnets"></a> [vpc\_existing\_ec2\_subnets](#input\_vpc\_existing\_ec2\_subnets) | n/a | `list(string)` | n/a | yes |
| <a name="input_vpc_existing_id"></a> [vpc\_existing\_id](#input\_vpc\_existing\_id) | n/a | `string` | n/a | yes |
| <a name="input_vpc_existing_redis_subnets"></a> [vpc\_existing\_redis\_subnets](#input\_vpc\_existing\_redis\_subnets) | n/a | `list(string)` | n/a | yes |
| <a name="input_vpc_gateway_endpoints_all"></a> [vpc\_gateway\_endpoints\_all](#input\_vpc\_gateway\_endpoints\_all) | n/a | `list(any)` | n/a | yes |
| <a name="input_vpc_interface_endpoints_batch"></a> [vpc\_interface\_endpoints\_batch](#input\_vpc\_interface\_endpoints\_batch) | n/a | `list(any)` | n/a | yes |
| <a name="input_vpc_interface_endpoints_tower"></a> [vpc\_interface\_endpoints\_tower](#input\_vpc\_interface\_endpoints\_tower) | n/a | `list(any)` | n/a | yes |
| <a name="input_vpc_new_alb_subnets"></a> [vpc\_new\_alb\_subnets](#input\_vpc\_new\_alb\_subnets) | n/a | `list(string)` | n/a | yes |
| <a name="input_vpc_new_azs"></a> [vpc\_new\_azs](#input\_vpc\_new\_azs) | n/a | `list(string)` | n/a | yes |
| <a name="input_vpc_new_batch_subnets"></a> [vpc\_new\_batch\_subnets](#input\_vpc\_new\_batch\_subnets) | n/a | `list(string)` | n/a | yes |
| <a name="input_vpc_new_cidr_range"></a> [vpc\_new\_cidr\_range](#input\_vpc\_new\_cidr\_range) | n/a | `string` | n/a | yes |
| <a name="input_vpc_new_db_subnets"></a> [vpc\_new\_db\_subnets](#input\_vpc\_new\_db\_subnets) | n/a | `list(string)` | n/a | yes |
| <a name="input_vpc_new_ec2_subnets"></a> [vpc\_new\_ec2\_subnets](#input\_vpc\_new\_ec2\_subnets) | n/a | `list(string)` | n/a | yes |
| <a name="input_vpc_new_private_subnets"></a> [vpc\_new\_private\_subnets](#input\_vpc\_new\_private\_subnets) | n/a | `list(string)` | n/a | yes |
| <a name="input_vpc_new_public_subnets"></a> [vpc\_new\_public\_subnets](#input\_vpc\_new\_public\_subnets) | n/a | `list(string)` | n/a | yes |
| <a name="input_vpc_new_redis_subnets"></a> [vpc\_new\_redis\_subnets](#input\_vpc\_new\_redis\_subnets) | n/a | `list(string)` | n/a | yes |
| <a name="input_wave_lite_db_allocated_storage"></a> [wave\_lite\_db\_allocated\_storage](#input\_wave\_lite\_db\_allocated\_storage) | n/a | `number` | n/a | yes |
| <a name="input_wave_lite_db_backup_retention_period"></a> [wave\_lite\_db\_backup\_retention\_period](#input\_wave\_lite\_db\_backup\_retention\_period) | n/a | `number` | n/a | yes |
| <a name="input_wave_lite_db_deletion_protection"></a> [wave\_lite\_db\_deletion\_protection](#input\_wave\_lite\_db\_deletion\_protection) | n/a | `bool` | n/a | yes |
| <a name="input_wave_lite_db_enable_storage_encrypted"></a> [wave\_lite\_db\_enable\_storage\_encrypted](#input\_wave\_lite\_db\_enable\_storage\_encrypted) | n/a | `bool` | n/a | yes |
| <a name="input_wave_lite_db_engine"></a> [wave\_lite\_db\_engine](#input\_wave\_lite\_db\_engine) | n/a | `string` | n/a | yes |
| <a name="input_wave_lite_db_engine_version"></a> [wave\_lite\_db\_engine\_version](#input\_wave\_lite\_db\_engine\_version) | n/a | `string` | n/a | yes |
| <a name="input_wave_lite_db_instance_class"></a> [wave\_lite\_db\_instance\_class](#input\_wave\_lite\_db\_instance\_class) | n/a | `string` | n/a | yes |
| <a name="input_wave_lite_db_param_group"></a> [wave\_lite\_db\_param\_group](#input\_wave\_lite\_db\_param\_group) | n/a | `string` | n/a | yes |
| <a name="input_wave_lite_skip_final_snapshot"></a> [wave\_lite\_skip\_final\_snapshot](#input\_wave\_lite\_skip\_final\_snapshot) | n/a | `bool` | n/a | yes |
| <a name="input_wave_server_url"></a> [wave\_server\_url](#input\_wave\_server\_url) | n/a | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_aws_account_id"></a> [aws\_account\_id](#output\_aws\_account\_id) | n/a |
| <a name="output_aws_caller_arn"></a> [aws\_caller\_arn](#output\_aws\_caller\_arn) | n/a |
| <a name="output_aws_caller_user"></a> [aws\_caller\_user](#output\_aws\_caller\_user) | n/a |
| <a name="output_aws_ec2_private_ip"></a> [aws\_ec2\_private\_ip](#output\_aws\_ec2\_private\_ip) | n/a |
| <a name="output_aws_ec2_public_ip"></a> [aws\_ec2\_public\_ip](#output\_aws\_ec2\_public\_ip) | n/a |
| <a name="output_database_connection_string"></a> [database\_connection\_string](#output\_database\_connection\_string) | Dynamically generated db connectino string based on tfvars selections. |
| <a name="output_ec2_ssh_key"></a> [ec2\_ssh\_key](#output\_ec2\_ssh\_key) | n/a |
| <a name="output_redis_endpoint"></a> [redis\_endpoint](#output\_redis\_endpoint) | n/a |
| <a name="output_route53_record_status"></a> [route53\_record\_status](#output\_route53\_record\_status) | n/a |
| <a name="output_seqera_configuration"></a> [seqera\_configuration](#output\_seqera\_configuration) | n/a |
| <a name="output_tower_api_endpoint"></a> [tower\_api\_endpoint](#output\_tower\_api\_endpoint) | Outputs for SEQERAKIT |
| <a name="output_tower_server_url"></a> [tower\_server\_url](#output\_tower\_server\_url) | n/a |
<!-- END_TF_DOCS -->    
