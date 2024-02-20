{
    "Version": "2012-10-17",
    "Statement": [
        { 
            "Sid": "AllowEc2Assumption",
            "Effect": "Allow",
            "Action": [ "sts:AssumeRole" ],
            "Principal": {
                "Service": [ "ec2.amazonaws.com" ]
            }
        }
    ]
}