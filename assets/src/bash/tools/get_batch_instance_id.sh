#!/bin/bash

# https://repost.aws/knowledge-center/batch-instance-id-ip-address
# https://serverfault.com/questions/971990/how-to-find-out-an-ec2-instances-private-and-public-ip-via-aws-cli

# How to invoke: /bin/bash get_batch_instance_id.sh <ID_OF_HEAD_JOB> <AWS_REGION>

JOB_ID=$1
REGION=$2

CONTAINER_INSTANCE_ARN=$(aws batch describe-jobs --jobs "$JOB_ID" --query 'jobs[0].container.containerInstanceArn' --region "$REGION" --output text);
echo ${CONTAINER_INSTANCE_ARN}

TMP=${CONTAINER_INSTANCE_ARN#*/}
CLUSTER_NAME=${TMP%/*}

EC2_ID=$(aws ecs describe-container-instances  --container-instances "$CONTAINER_INSTANCE_ARN" --cluster "$CLUSTER_NAME" --query "containerInstances[0].ec2InstanceId" --region "$REGION" --output text)
EC2_IP=$(aws --region "$REGION"  ec2 describe-instances --filters "Name=instance-state-name,Values=running" "Name=instance-id,Values=$EC2_ID" --query "Reservations[*].Instances[*].[PrivateIpAddress]" --output text)

echo ${EC2_ID}
echo ${EC2_IP}