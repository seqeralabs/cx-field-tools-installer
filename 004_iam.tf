## ------------------------------------------------------------------------------------
## IAM template files
## ------------------------------------------------------------------------------------

locals {
  instance_assume_role_policy = templatefile("assets/src/aws/iam_trust_policy_ec2.json.tpl", {})

  instance_role_policy_main = templatefile("assets/src/aws/iam_role_policy_ec2.json.tpl",
    {
      seqerakit_root_bucket       = trimprefix(var.seqerakit_root_bucket, "s3://"),
      app_name                    = var.app_name,
      secrets_bootstrap_tower     = var.secrets_bootstrap_tower,
      secrets_bootstrap_seqerakit = var.secrets_bootstrap_seqerakit,
      tag_key                     = local.global_prefix,
      aws_region                  = var.aws_region,
      aws_account                 = var.aws_account
    }
  )

  instance_role_policy_ses = templatefile("assets/src/aws/iam_role_policy_ses.json.tpl", {})
  lt_content_raw           = templatefile("assets/src/aws/launch_template_ec2.tpl", {})
}


## ------------------------------------------------------------------------------------
## IAM resources
## ------------------------------------------------------------------------------------
resource "aws_iam_role" "ec2" {
  count = var.flag_iam_use_prexisting_role_arn == true ? 0 : 1

  name               = "${local.global_prefix}_role"
  assume_role_policy = local.instance_assume_role_policy
}


resource "aws_iam_instance_profile" "tower_vm" {
  count = var.flag_iam_use_prexisting_role_arn == true ? 0 : 1

  name = "${local.global_prefix}_instance_profile"
  role = aws_iam_role.ec2[0].name
}


resource "aws_iam_policy" "main_policy" {
  count = var.flag_iam_use_prexisting_role_arn == true ? 0 : 1

  name        = "${local.global_prefix}_policy_main"
  description = "Main Tower policy"
  policy      = local.instance_role_policy_main
}


resource "aws_iam_policy" "ses_policy" {
  count = var.flag_iam_use_prexisting_role_arn == true ? 0 : 1

  name        = "${local.global_prefix}_policy_ses"
  description = "SES Tower policy"
  policy      = local.instance_role_policy_ses
}


resource "aws_iam_role_policy_attachment" "attach_main" {
  count = var.flag_iam_use_prexisting_role_arn == true ? 0 : 1

  role       = aws_iam_role.ec2[0].name
  policy_arn = aws_iam_policy.main_policy[0].arn
}


# Create extra policy if SES Integration is true. Else, ignore.
resource "aws_iam_role_policy_attachment" "attach_ses" {
  count = var.flag_iam_use_prexisting_role_arn == false && var.flag_use_aws_ses_iam_integration == true ? 1 : 0

  role       = aws_iam_role.ec2[0].name
  policy_arn = aws_iam_policy.ses_policy[0].arn
}


## ------------------------------------------------------------------------------------
## Get name of Instance profile
##   Regardless of whether newly created or provided, get the instance role name for assignment to EC2 Launch Template
## ------------------------------------------------------------------------------------
data "aws_iam_instance_profile" "tower_vm" {
  name = (
    var.flag_iam_use_prexisting_role_arn == true ? var.iam_prexisting_instance_role_arn : aws_iam_instance_profile.tower_vm[0].name
  )
}
