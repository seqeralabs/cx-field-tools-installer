# Permission

Permissions were identified via:
1) [iamlive](https://github.com/iann0036/iamlive) transaction observation.
2) **Update** - Active testing in AWS on April 13, 2024.



```json
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Sid": "InteractWithSSMParameters",
			"Effect": "Allow",
			"Action": [
				"ssm:PutParameter",
				"ssm:GetParameter",
				"ssm:GetParameters",
				"ssm:DeleteParameter",
				"ssm:AddTagsToResource"
			],
			"Resource": [
				"arn:aws:ssm:AWS_REGION_REPLACE_ME:AWS_ACCOUNT_REPLACE_ME:parameter/config/APP_NAME_REPLACE_ME*",
				"arn:aws:ssm:AWS_REGION_REPLACE_ME:AWS_ACCOUNT_REPLACE_ME:parameter/seqera/APP_NAME_REPLACE_ME*",
				"arn:aws:ssm:AWS_REGION_REPLACE_ME:AWS_ACCOUNT_REPLACE_ME:parameter/seqera/sensitive-values/APP_NAME_REPLACE_ME*"
			]
		},
		{
			"Sid": "InteractWithTFPrefixedIAMResources",
			"Effect": "Allow",
			"Action": [
				"iam:AddRoleToInstanceProfile",
				"iam:AttachRolePolicy",
				"iam:CreateInstanceProfile",
				"iam:CreatePolicy",
				"iam:CreateRole",
				"iam:DeleteInstanceProfile",
				"iam:DeletePolicy",
				"iam:DetachRolePolicy",
				"iam:DeleteRole",
				"iam:GetInstanceProfile",
				"iam:GetPolicy",
				"iam:GetPolicyVersion",
				"iam:GetRole",
				"iam:ListAttachedRolePolicies",
				"iam:ListInstanceProfilesForRole",
				"iam:ListPolicyVersions",
				"iam:ListRolePolicies",
				"iam:PassRole",
				"iam:RemoveRoleFromInstanceProfile",
				"iam:TagInstanceProfile",
				"iam:TagPolicy",
				"iam:TagRole"
			],
			"Resource": [
				"arn:aws:iam::AWS_ACCOUNT_REPLACE_ME:role/tf-APP_NAME_REPLACE_ME-*",
				"arn:aws:iam::AWS_ACCOUNT_REPLACE_ME:policy/tf-APP_NAME_REPLACE_ME-*",
				"arn:aws:iam::AWS_ACCOUNT_REPLACE_ME:instance-profile/tf-APP_NAME_REPLACE_ME-*"
			]
		},
		{
			"Sid": "InteractWithTFPrefixedOtherResources",
			"Effect": "Allow",
			"Action": [
				"ec2:DeleteKeyPair",
				"ec2:ImportKeyPair",
				"elasticache:AddTagsToResource",
				"elasticache:CreateCacheCluster",
				"elasticache:CreateCacheSubnetGroup",
				"elasticache:DeleteCacheCluster",
				"elasticache:DeleteCacheSubnetGroup",
				"elasticache:DescribeCacheSubnetGroups",
				"elasticache:DescribeCacheClusters",
				"elasticache:ListTagsForResource",
				"elasticloadbalancing:CreateListener",
				"elasticloadbalancing:DeleteListener",
				"elasticloadbalancing:CreateLoadBalancer",
				"elasticloadbalancing:DeleteLoadBalancer",
				"elasticloadbalancing:ModifyLoadBalancerAttributes",
				"elasticloadbalancing:SetIpAddressType",
				"elasticloadbalancing:SetSecurityGroups",
				"rds:CreateDBInstance",
				"rds:CreateDBParameterGroup",
				"rds:CreateDBSubnetGroup",
				"rds:CreateOptionGroup",
				"rds:DeleteDBInstance",
				"rds:DeleteDBSubnetGroup",
				"rds:DeleteOptionGroup",
				"rds:DescribeDBInstances",
				"rds:DescribeDBParameters",
				"rds:DeleteDBParameterGroup",
				"rds:DescribeDBParameterGroups",
				"rds:DescribeDBSubnetGroups",
				"rds:DescribeOptionGroups",
				"rds:ListTagsForResource"
			],
			"Resource": "*",
			"Condition": {
				"StringEquals": {
					"aws:ResourceAccount": "AWS_ACCOUNT_REPLACE_ME",
					"aws:RequestedRegion": "AWS_REGION_REPLACE_ME"
				}
			}
		},
		{
			"Sid": "WildcardPrivileges",
			"Effect": "Allow",
			"Action": [
				"ec2:AllocateAddress",
				"ec2:AssociateAddress",
				"ec2:AssociateRouteTable",
				"ec2:AttachInternetGateway",
				"ec2:AuthorizeSecurityGroupEgress",
				"ec2:AuthorizeSecurityGroupIngress",
				"ec2:CreateInstanceConnectEndpoint",
				"ec2:CreateInternetGateway",
				"ec2:CreateNatGateway",
				"ec2:CreateLaunchTemplate",
				"ec2:CreateNetworkAclEntry",
				"ec2:CreateRoute",
				"ec2:CreateRouteTable",
				"ec2:CreateSecurityGroup",
				"ec2:CreateSubnet",
				"ec2:CreateTags",
				"ec2:CreateVpc",
				"ec2:CreateVpcEndPoint",
				"ec2:DeleteInstanceConnectEndpoint",
				"ec2:DeleteInternetGateway",
				"ec2:DeleteLaunchTemplate",
				"ec2:DeleteNatGateway",
				"ec2:DeleteNetworkAclEntry",
				"ec2:DeleteNetworkInterface",
				"ec2:DeleteRoute",
				"ec2:DeleteRouteTable",
				"ec2:DeleteSecurityGroup",
				"ec2:DeleteSubnet",
				"ec2:DeleteVpc",
				"ec2:DeleteVpcEndpoints",
				"ec2:DescribeAddresses",
				"ec2:DescribeImages",
				"ec2:DescribeInstanceAttribute",
				"ec2:DescribeInstances",
				"ec2:DescribeInstanceTypes",
				"ec2:DescribeInstanceConnectEndpoints",
				"ec2:DescribeInternetGateways",
				"ec2:DescribeKeyPairs",
				"ec2:DescribeLaunchTemplates",
				"ec2:DescribeLaunchTemplateVersions",
				"ec2:DescribeNatGateways",
				"ec2:DescribeNetworkAcls",
				"ec2:DescribeNetworkInterfaces",
				"ec2:DescribePrefixLists",
				"ec2:DescribeRouteTables",
				"ec2:DescribeSecurityGroups",
				"ec2:DescribeSecurityGroupRules",
				"ec2:DescribeSubnets",
				"ec2:DescribeTags",
				"ec2:DescribeVolumes",
				"ec2:DescribeVpcs",
				"ec2:DescribeVpcEndpoints",
				"ec2:DescribeVpcAttribute",
				"ec2:DetachInternetGateway",
				"ec2:DetachNetworkInterface",
				"ec2:DisassociateAddress",
				"ec2:DisassociateRouteTable",
				"ec2:ModifyInstanceAttribute",
				"ec2:ModifySubnetAttribute",
				"ec2:ModifyVpcAttribute",
				"ec2:ReleaseAddress",
				"ec2:RevokeSecurityGroupEgress",
				"ec2:RevokeSecurityGroupIngress",
				"ec2:RunInstances",
				"ec2:TerminateInstances",
				"elasticloadbalancing:AddTags",
				"elasticloadbalancing:CreateTargetGroup",
				"elasticloadbalancing:DeleteTargetGroup",
				"elasticloadbalancing:DescribeListeners",
				"elasticloadbalancing:DescribeLoadBalancers",
				"elasticloadbalancing:DescribeLoadBalancerAttributes",
				"elasticloadbalancing:DescribeTags",
				"elasticloadbalancing:DescribeTargetGroups",
				"elasticloadbalancing:DescribeTargetGroupAttributes",
				"elasticloadbalancing:DescribeTargetHealth",
				"elasticloadbalancing:DeregisterTargets",
				"elasticloadbalancing:ModifyTargetGroupAttributes",
				"elasticloadbalancing:RegisterTargets",
				"rds:AddTagsToResource",
				"route53:ChangeResourceRecordSets",
				"route53:CreateHostedZone",
				"route53:DeleteHostedZone",
				"route53:GetChange",
				"route53:GetHostedZone",
				"route53:ListHostedZones",
				"route53:ListResourceRecordSets",
				"route53:ListTagsForResource",
				"ssm:DescribeParameters",
				"ssm:ListTagsForResource",
				"sts:GetCallerIdentity"
			],
			"Resource": "*",
			"Condition": {
				"StringEquals": {
					"aws:ResourceAccount": "AWS_ACCOUNT_REPLACE_ME",
					"aws:RequestedRegion": "AWS_REGION_REPLACE_ME"
				}
			}
		},
		{
			"Sid": "WildcardPrivilegesEdgecase",
			"Effect": "Allow",
			"Action": [
				"ec2:RunInstances"
			],
			"Resource": "*",
			"Condition": {
				"StringEquals": {
					"aws:RequestedRegion": "AWS_REGION_REPLACE_ME"
				}
			}
		}
	]
}
```