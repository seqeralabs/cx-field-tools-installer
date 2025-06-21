#!/bin/bash

# Exit on any error
set -e

# Function to test subnet ID lookups
test_subnet_lookup() {
    local test_name=$1
    local cidrs=$2
    local expected_ids=$3
    local actual_ids=$(terraform output -json | jq -r ".subnet_ids_${test_name}.value")
    
    if [ "$actual_ids" = "$expected_ids" ]; then
        echo "✅ Subnet lookup test passed for ${test_name}"
    else
        echo "❌ Subnet lookup test failed for ${test_name}"
        echo "Expected: ${expected_ids}"
        echo "Got: ${actual_ids}"
        exit 1
    fi
}

# Run tests
echo "Running local value tests..."

# Test EC2 subnet lookups
test_subnet_lookup "ec2" "10.0.1.0/24,10.0.2.0/24" "subnet-123,subnet-456"

# Test Batch subnet lookups
test_subnet_lookup "batch" "10.0.3.0/24,10.0.4.0/24" "subnet-789,subnet-012"

# Add more tests as needed 