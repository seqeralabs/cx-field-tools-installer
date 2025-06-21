#!/bin/bash

# Exit on any error
set -e

# Store the original plan
echo "Generating original plan..."
terraform plan -out=original.tfplan

# Store the plan in a readable format
terraform show -json original.tfplan > original_plan.json

# Make your changes here
# ... (your refactoring changes) ...

# Generate new plan
echo "Generating new plan..."
terraform plan -out=new.tfplan

# Store the new plan in a readable format
terraform show -json new.tfplan > new_plan.json

# Compare the plans
echo "Comparing plans..."
if diff original_plan.json new_plan.json > /dev/null; then
    echo "✅ Plans are identical - no infrastructure changes detected"
    exit 0
else
    echo "❌ Plans differ - infrastructure changes detected"
    echo "Differences:"
    diff original_plan.json new_plan.json
    exit 1
fi 