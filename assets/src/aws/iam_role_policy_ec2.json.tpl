{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ListObjectsInBucket",
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::${seqerakit_root_bucket}"
            ]
        },
        {
            "Sid": "AllObjectActions",
            "Effect": "Allow",
            "Action": "s3:*Object",
            "Resource": [
                "arn:aws:s3:::${seqerakit_root_bucket}/*"
            ]
        },
        { 
            "Sid": "EnableInstanceConnect",
            "Effect":"Allow",
            "Action":"ec2-instance-connect:SendSSHPublicKey",
            "Resource": "arn:aws:ec2:${aws_region}:${aws_account}:instance/*",
            "Condition":{ 
                "StringEquals":{ "aws:ResourceTag/tag-key":"${tag_key}" }
            }
        },
        {
            "Sid": "EnableInstanceConenctFromConsole",
            "Effect": "Allow",
            "Action": "ec2:DescribeInstances",
            "Resource": "*"
        },
        {
            "Sid": "AllowLogging",
            "Effect": "Allow",
            "Action": [
                "cloudwatch:PutMetricData",
                "ec2:DescribeVolumes",
                "ec2:DescribeTags",
                "logs:PutLogEvents",
                "logs:DescribeLogStreams",
                "logs:DescribeLogGroups",
                "logs:CreateLogStream",
                "logs:CreateLogGroup",
                "logs:PutRetentionPolicy"
            ],
            "Resource": "*"
        },
        {
            "Sid": "AllowSSMPullMoreLimited",
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter",
                "ssm:GetParameters",
                "ssm:GetParametersByPath"
            ],
            "Resource": [
                "arn:aws:ssm:${aws_region}:${aws_account}:parameter/config/${app_name}",
                "arn:aws:ssm:${aws_region}:${aws_account}:parameter/config/${app_name}*",
                "arn:aws:ssm:${aws_region}:${aws_account}:parameter/seqera/${app_name}/*",
                "arn:aws:ssm:${aws_region}:${aws_account}:parameter/config/application",
                "arn:aws:ssm:${aws_region}:${aws_account}:parameter/config/application_*"
            ]
        },
        {
            "Sid": "KeyPermissionForSSMSecureStrings",
            "Action": [
                "kms:Decrypt",
                "kms:Encrypt",
                "kms:GenerateDataKey"
            ],
            "Effect": "Allow",
			"Resource": [ "${ssm_key_arn}" ]
        }
    ]
}
