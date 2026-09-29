{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "LineageIntegrationSQS",
            "Effect": "Allow",
            "Action": [
                "sqs:CreateQueue",
                "sqs:GetQueueAttributes",
                "sqs:SetQueueAttributes",
                "sqs:GetQueueUrl",
                "sqs:ReceiveMessage",
                "sqs:DeleteMessage"
            ],
            "Resource": "arn:aws:sqs:${aws_region}:${aws_account}:seqera-lineage-*"
        },
        {
            "Sid": "LineageIntegrationS3",
            "Effect": "Allow",
            "Action": [
                "s3:CreateBucket",
                "s3:GetBucketNotification",
                "s3:PutBucketNotification",
                "s3:GetBucketLocation"
            ],
            "Resource": "arn:aws:s3:::seqera-lineage-*"
        }%{ if !tower_version_before_26_2 },
        {
            "Sid": "LineageEnhancedPermissionsforv2620SNS",
            "Effect": "Allow",
            "Action": [
                "sns:CreateTopic",
                "sns:SetTopicAttributes",
                "sns:Subscribe",
                "sns:ConfirmSubscription",
                "sns:Unsubscribe",
                "sns:DeleteTopic"
            ],
            "Resource": "arn:aws:sns:${aws_region}:${aws_account}:${lineage_store_prefix}-*"
        },
        {
            "Sid": "LineageEnhancedPermissionsforv2620S3",
            "Effect": "Allow",
            "Action": [
                "s3:CreateBucket",
                "s3:GetBucketNotification",
                "s3:PutBucketNotification",
                "s3:GetBucketLocation",
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::${lineage_store_prefix}-*",
                "arn:aws:s3:::${lineage_store_prefix}-*/*"
            ]
        },
        {
            "Sid": "LineageEnhancedPermissionsforv2620SQS",
            "Effect": "Allow",
            "Action": ["sqs:DeleteQueue"],
            "Resource": "arn:aws:sqs:${aws_region}:${aws_account}:seqera-lineage-*"
        }%{ endif }
    ]
}
