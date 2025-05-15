## ------------------------------------------------------------------------------------
## AMI
## ------------------------------------------------------------------------------------
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  # https://docs.aws.amazon.com/linux/al2023/ug/ec2.html#launch-from-ec2-console
  filter {
    name   = "name"
    values = ["al2023-ami-minimal-*"]
    # values = ["al2023-ami-ecs-hvm-2023.0.20230509-kernel-6.1-x86_64"]
    # values = ["al2023-ami-ecs-hvm-2023*"]
  }
  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}


## ------------------------------------------------------------------------------------
## EC2 SSH Key
## ------------------------------------------------------------------------------------
resource "tls_private_key" "ec2_ssh_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}


resource "aws_key_pair" "generated_key" {
  key_name   = local.global_prefix
  public_key = tls_private_key.ec2_ssh_key.public_key_openssh
}


## ------------------------------------------------------------------------------------
## EC2 Launch Template
## ------------------------------------------------------------------------------------
resource "aws_launch_template" "lt_with_no_ami_lifecycle" {

  count = var.ec2_update_ami_if_available == true ? 1 : 0

  image_id      = data.aws_ami.amazon_linux_2023.id
  instance_type = var.ec2_host_instance_type

  vpc_security_group_ids = local.ec2_sg_final
  key_name               = aws_key_pair.generated_key.key_name

  iam_instance_profile {
    name = data.aws_iam_instance_profile.tower_vm.name
  }

  metadata_options {
    # IMDS token config
    http_tokens = var.ec2_require_imds_token == true ? "required" : "optional"
  }

  user_data = base64encode(local.lt_content_raw)
}


resource "aws_launch_template" "lt_with_ami_lifecycle" {

  count = var.ec2_update_ami_if_available == false ? 1 : 0

  image_id      = data.aws_ami.amazon_linux_2023.id
  instance_type = var.ec2_host_instance_type

  vpc_security_group_ids = local.ec2_sg_final
  key_name               = aws_key_pair.generated_key.key_name

  iam_instance_profile {
    name = data.aws_iam_instance_profile.tower_vm.name
  }

  metadata_options {
    # IMDS token config
    http_tokens = var.ec2_require_imds_token == true ? "required" : "optional"
  }

  user_data = base64encode(local.lt_content_raw)

  lifecycle {
    ignore_changes = [ image_id ]
  }
}


## ------------------------------------------------------------------------------------
## EC2 Instance
## ------------------------------------------------------------------------------------
resource "aws_instance" "ec2" {

  depends_on = [module.rds[0]]

  subnet_id = local.subnet_ids_ec2[0]

  launch_template {
    # id      = aws_launch_template.lt.id
    id        = ( var.ec2_update_ami_if_available == true ? 
      aws_launch_template.lt_with_no_ami_lifecycle[0].id : aws_launch_template.lt_with_ami_lifecycle[0].id
    )
    version = "$Latest"
  }

  root_block_device {
    encrypted  = var.flag_encrypt_ebs
    kms_key_id = var.flag_use_kms_key == true ? var.ec2_ebs_kms_key : ""
    volume_size = var.ec2_root_volume_size
  }

  # This is here to stop the EC2 from being updated in place due to perception user data has changed
  # when it actually hasn't (triggered by `depends_on` or `data` read). See:
  #  - https://github.com/hashicorp/terraform-provider-aws/issues/5011
  #  - https://github.com/hashicorp/terraform/issues/11806
  lifecycle {
    ignore_changes = [user_data]
  }

  metadata_options {
    # IMDS token config
    http_tokens = var.ec2_require_imds_token == true ? "required" : "optional"
  }

  tags = {
    tag-key = local.global_prefix # This tag allows Console InstanceConnect to attach
    Name    = local.global_prefix
  }
}


## ------------------------------------------------------------------------------------
## Elatic IP & Association
## Use so machine termination will not require changes to external DNS.
## ------------------------------------------------------------------------------------
resource "aws_eip" "towerhost" {
  count = var.flag_make_instance_public == true ? 1 : 0

  domain = "vpc"
}


resource "aws_eip_association" "eip_assoc" {
  count = var.flag_make_instance_public == true ? 1 : 0

  instance_id   = aws_instance.ec2.id
  allocation_id = aws_eip.towerhost[0].id
}


## ------------------------------------------------------------------------------------
## Instance Connect Endpoint -- critical for SSH into private subnets
## ------------------------------------------------------------------------------------
# This turned out to be a moot issue since a VPC can only have a single EICE endpoint. Keeping anyways in case folks have more quota.
# https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/eice-quotas.html
# https://discuss.hashicorp.com/t/the-for-each-value-depends-on-resource-attributes-that-cannot-be-determined-until-apply/25016/2
resource "aws_ec2_instance_connect_endpoint" "example" {
  count = var.flag_make_instance_private == true || var.flag_make_instance_private_behind_public_alb == true ? 1 : 0

  subnet_id          = local.subnet_ids_ec2[0]
  security_group_ids = [module.sg_eice.security_group_id]

  tags = {
    Name = local.global_prefix
  }
}
