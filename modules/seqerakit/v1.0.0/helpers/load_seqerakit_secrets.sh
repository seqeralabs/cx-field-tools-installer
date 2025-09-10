#!/bin/bash

# ------------------------------------------------------------------------------------
# Load Seqerakit Secrets from SSM into Environment Variables
# ------------------------------------------------------------------------------------
# Usage: source load_seqerakit_secrets.sh [bootstrap_ssm_path] [aws_profile] [aws_region]
# Example: source load_seqerakit_secrets.sh /scidev/seqerakit/config playground us-east-1
# ------------------------------------------------------------------------------------

# set -e

# Get parameters
BOOTSTRAP_SSM_PATH=${1:-"/scidev/seqerakit/config"}
AWS_PROFILE_PARAM=${2:-"$AWS_PROFILE"}
AWS_REGION_PARAM=${3:-"$AWS_DEFAULT_REGION"}

echo "Loading secrets from: $BOOTSTRAP_SSM_PATH"
if [ -n "$AWS_PROFILE_PARAM" ]; then
    echo "Using AWS profile: $AWS_PROFILE_PARAM"
    export AWS_PROFILE="$AWS_PROFILE_PARAM"
fi
if [ -n "$AWS_REGION_PARAM" ]; then
    echo "Using AWS region: $AWS_REGION_PARAM"
    export AWS_DEFAULT_REGION="$AWS_REGION_PARAM"
    export AWS_REGION="$AWS_REGION_PARAM"
fi

# Check dependencies
if ! command -v jq &> /dev/null; then
    echo "❌ Error: jq is required. Install with: brew install jq"
    return 1
fi

if ! command -v aws &> /dev/null; then
    echo "❌ Error: AWS CLI is required"
    return 1
fi

# Test AWS CLI
if ! aws sts get-caller-identity &>/dev/null; then
    echo "❌ Error: AWS CLI not configured. Run 'aws configure' or 'aws sso login'"
    return 1
fi

# Get the bootstrap parameter
BOOTSTRAP_JSON=$(aws ssm get-parameters \
    --name "$BOOTSTRAP_SSM_PATH" \
    --with-decryption \
    --query "Parameters[*].{Value:Value}" \
    --output text)

if [ -z "$BOOTSTRAP_JSON" ] || [ "$BOOTSTRAP_JSON" = "None" ]; then
    echo "❌ Error: Parameter not found: $BOOTSTRAP_SSM_PATH"
    return 1
fi

# Validate JSON
if ! echo "$BOOTSTRAP_JSON" | jq empty 2>/dev/null; then
    echo "❌ Error: Invalid JSON in parameter"
    return 1
fi

# Extract and set environment variables
export TOWER_AWS_USER=$(echo "$BOOTSTRAP_JSON" | jq -r '.["TOWER_AWS_USER"]["value"] // empty')
export TOWER_AWS_PASSWORD=$(echo "$BOOTSTRAP_JSON" | jq -r '.["TOWER_AWS_PASSWORD"]["value"] // empty')
export TOWER_AWS_ROLE=$(echo "$BOOTSTRAP_JSON" | jq -r '.["TOWER_AWS_ROLE"]["value"] // empty')
export TOWER_GITHUB_USER=$(echo "$BOOTSTRAP_JSON" | jq -r '.["TOWER_GITHUB_USER"]["value"] // empty')
export TOWER_GITHUB_TOKEN=$(echo "$BOOTSTRAP_JSON" | jq -r '.["TOWER_GITHUB_TOKEN"]["value"] // empty')
export TOWER_DOCKER_USER=$(echo "$BOOTSTRAP_JSON" | jq -r '.["TOWER_DOCKER_USER"]["value"] // empty')
export TOWER_DOCKER_TOKEN=$(echo "$BOOTSTRAP_JSON" | jq -r '.["TOWER_DOCKER_TOKEN"]["value"] // empty')
export TOWER_CODECOMMIT_USER=$(echo "$BOOTSTRAP_JSON" | jq -r '.["TOWER_CODECOMMIT_USER"]["value"] // empty')
export TOWER_CODECOMMIT_PASSWORD=$(echo "$BOOTSTRAP_JSON" | jq -r '.["TOWER_CODECOMMIT_PASSWORD"]["value"] // empty')
export TOWER_CODECOMMIT_REGION=$(echo "$BOOTSTRAP_JSON" | jq -r '.["TOWER_CODECOMMIT_REGION"]["value"] // empty')

echo "✓ Secrets loaded successfully"
