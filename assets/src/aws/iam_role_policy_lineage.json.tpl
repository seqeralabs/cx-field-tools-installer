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
        }
    ]
}
