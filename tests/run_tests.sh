#!/bin/bash

# Exit on any error
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🚀 Starting test suite..."

# 1. Run plan comparison test
echo -e "\n${GREEN}Running plan comparison test...${NC}"
./plan_test.sh
if [ $? -eq 0 ]; then
    echo "✅ Plan comparison test passed"
else
    echo "❌ Plan comparison test failed"
    exit 1
fi

# 2. Run local values test
echo -e "\n${GREEN}Running local values test...${NC}"
./local_values_test.sh
if [ $? -eq 0 ]; then
    echo "✅ Local values test passed"
else
    echo "❌ Local values test failed"
    exit 1
fi

# 3. Run integration tests
echo -e "\n${GREEN}Running integration tests...${NC}"
cd test_env
terraform init
terraform plan -out=tfplan
terraform apply -auto-approve tfplan

# Run validation tests
terraform output -json > outputs.json
if [ $? -eq 0 ]; then
    echo "✅ Integration test passed"
else
    echo "❌ Integration test failed"
    exit 1
fi

# Cleanup
terraform destroy -auto-approve
cd ..

echo -e "\n${GREEN}All tests passed! 🎉${NC}" 