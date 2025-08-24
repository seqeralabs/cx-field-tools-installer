# GitHub Actions Testing Strategy Brainstorming Session
Date: 2025-08-24
Topic: Multi-Configuration Terraform Testing with GitHub Actions

## Initial Requirements
- Create a testing strategy for multiple real-world deployments
- Each permutation based on different .tfvars files
- Deployments can take up to 30 minutes
- Need concurrent testing capabilities
- Must align with best practices

## Solution 1: Matrix-Based Parallel Testing

### Overview
Uses GitHub Actions' matrix strategy to run multiple tfvars configurations in parallel.

### Benefits:
- Maximum concurrency - all permutations run simultaneously
- Fast feedback - failures are isolated to specific configurations
- Easy to scale - just add more tfvars files to the matrix
- Native GitHub Actions feature - no additional tooling needed
- Clear visibility in GitHub UI - each matrix job appears separately

### Risks:
- AWS resource limits - parallel deployments may hit quota limits
- Cost implications - running many environments simultaneously
- State file conflicts if not properly isolated
- Potential for resource naming collisions

### Implementation:
```yaml
name: Multi-Config Testing

on:
  pull_request:
  workflow_dispatch:

jobs:
  prepare-configs:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set-matrix.outputs.matrix }}
    steps:
      - uses: actions/checkout@v4
      - id: set-matrix
        run: |
          # Dynamically generate matrix from tfvars files
          configs=$(find test-configs/ -name "*.tfvars" -exec basename {} .tfvars \;)
          echo "matrix={\"config\":[$configs]}" >> $GITHUB_OUTPUT

  test-deployment:
    needs: prepare-configs
    strategy:
      matrix: ${{ fromJson(needs.prepare-configs.outputs.matrix) }}
      max-parallel: 5  # Limit concurrent deployments
      fail-fast: false  # Continue other tests if one fails
    runs-on: ubuntu-latest
    env:
      TF_WORKSPACE: test-${{ matrix.config }}-${{ github.run_id }}
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE }}
          aws-region: ${{ vars.AWS_REGION }}
      
      - name: Initialize Terraform
        run: |
          terraform init \
            -backend-config="key=test/${{ matrix.config }}-${{ github.run_id }}.tfstate"
      
      - name: Copy test configuration
        run: |
          cp test-configs/${{ matrix.config }}.tfvars terraform.tfvars
          echo "app_name = \"test-${{ matrix.config }}-${{ github.run_id }}\"" >> override.auto.tfvars
      
      - name: Validate configuration
        run: make verify
      
      - name: Deploy infrastructure
        id: deploy
        run: |
          terraform apply -auto-approve
          terraform output -json > outputs.json
      
      - name: Run integration tests
        run: |
          pytest tests/integration/ \
            --config ${{ matrix.config }} \
            --outputs outputs.json \
            -v --junit-xml=results-${{ matrix.config }}.xml
      
      - name: Cleanup
        if: always()
        run: terraform destroy -auto-approve || true
```

## Solution 2: Orchestrated Wave Testing

### Overview
Uses a controller job with custom orchestration to manage deployments in waves.

### Benefits:
- Resource optimization - reuses base infrastructure across tests
- Cost-effective - sequential reuse of expensive resources (RDS, ALB)
- Better error handling - can implement retry logic
- Supports complex dependencies between configurations
- Can implement canary testing patterns

### Risks:
- Longer total execution time due to sequential aspects
- More complex orchestration logic
- Potential state drift between configurations
- Requires more sophisticated cleanup between tests

### Implementation:
```yaml
name: Wave-Based Testing

jobs:
  orchestrator:
    runs-on: ubuntu-latest
    outputs:
      test-plan: ${{ steps.plan.outputs.plan }}
    steps:
      - name: Generate test plan
        id: plan
        run: |
          python3 scripts/generate_test_plan.py \
            --configs test-configs/ \
            --waves 3 \
            --output plan.json

  base-infrastructure:
    needs: orchestrator
    runs-on: ubuntu-latest
    outputs:
      vpc-id: ${{ steps.base.outputs.vpc-id }}
      subnet-ids: ${{ steps.base.outputs.subnet-ids }}
    steps:
      - name: Deploy shared resources
        id: base
        run: |
          terraform apply -target=module.vpc -auto-approve
          echo "vpc-id=$(terraform output -raw vpc_id)" >> $GITHUB_OUTPUT

  test-wave:
    needs: [orchestrator, base-infrastructure]
    strategy:
      matrix:
        wave: [1, 2, 3]
    runs-on: ubuntu-latest
    steps:
      - name: Run wave tests
        run: |
          configs=$(echo '${{ needs.orchestrator.outputs.test-plan }}' | \
            jq -r ".waves[${{ matrix.wave }}].configs[]")
          
          for config in $configs; do
            cp test-configs/${config}.tfvars terraform.tfvars
            terraform apply -auto-approve
            pytest tests/integration/ --config ${config}
            terraform destroy -auto-approve
          done
```

## Enhanced Solution: S3 Backend with State Preservation

After discussion about needing persistent state files for debugging, the solution was enhanced to use S3 backend with unique prefixes.

### Key Features:
1. **Persistent state files** in S3 for post-mortem analysis
2. **State locking** via DynamoDB to prevent conflicts
3. **Organized state hierarchy** for easy navigation
4. **Optional cleanup** based on test results

### Enhanced Implementation:
```yaml
name: Multi-Config Testing with S3 Backend

env:
  STATE_BUCKET: 'company-terraform-test-states'
  STATE_REGION: 'us-east-1'
  LOCK_TABLE: 'terraform-test-locks'

jobs:
  prepare-configs:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set-matrix.outputs.matrix }}
      test-id: ${{ steps.set-id.outputs.test-id }}
    steps:
      - name: Generate unique test ID
        id: set-id
        run: |
          TEST_ID="$(date +%Y%m%d-%H%M%S)-${{ github.run_id }}"
          echo "test-id=${TEST_ID}" >> $GITHUB_OUTPUT
      
      - name: Set matrix from tfvars files
        id: set-matrix
        run: |
          configs=$(ls test-configs/*.tfvars | xargs -n1 basename | sed 's/.tfvars//' | jq -R . | jq -sc .)
          echo "matrix={\"config\":${configs}}" >> $GITHUB_OUTPUT

  test-deployment:
    needs: prepare-configs
    strategy:
      matrix: ${{ fromJson(needs.prepare-configs.outputs.matrix) }}
      max-parallel: 5
      fail-fast: false
    runs-on: ubuntu-latest
    env:
      TF_STATE_KEY: "tests/${{ needs.prepare-configs.outputs.test-id }}/${{ matrix.config }}/terraform.tfstate"
    steps:
      - name: Prepare backend configuration
        run: |
          cat > backend-${{ matrix.config }}.hcl <<EOF
          bucket         = "${STATE_BUCKET}"
          key            = "${TF_STATE_KEY}"
          region         = "${STATE_REGION}"
          dynamodb_table = "${LOCK_TABLE}"
          encrypt        = true
          EOF
      
      - name: Initialize Terraform
        run: |
          terraform init -backend-config=backend-${{ matrix.config }}.hcl
      
      - name: Deploy infrastructure
        id: deploy
        timeout-minutes: 45
        run: |
          terraform apply tfplan-${{ matrix.config }}
          terraform output -json > outputs-${{ matrix.config }}.json
      
      - name: Conditional cleanup
        if: success() && github.event.inputs.skip_cleanup != 'true'
        run: terraform destroy -auto-approve
      
      - name: Mark failed deployment
        if: failure()
        run: |
          aws s3api put-object-tagging \
            --bucket ${STATE_BUCKET} \
            --key "${TF_STATE_KEY}" \
            --tagging 'TagSet=[{Key=Status,Value=Failed}]'
```

## Test Configuration Organization

### Structure:
```
repository/
├── terraform.tfvars                 # Main/production config
├── test-configs/                    # Test-specific configurations
│   ├── minimal.tfvars              # Container DB, minimal setup
│   ├── standard-rds.tfvars         # External RDS database
│   ├── existing-vpc.tfvars         # Use existing VPC
│   ├── high-availability.tfvars    # HA setup with ALB
│   └── complex-integration.tfvars  # All external resources
└── test-secrets/                    # Test-specific secrets
    └── ssm-mappings.json           # Mapping of configs to SSM paths
```

### Example Test Configuration (minimal.tfvars):
```hcl
# Test A: Minimal deployment with container database
app_name = "WILL_BE_OVERRIDDEN"
secrets_bootstrap_tower       = "/test/secrets/minimal/tower"
secrets_bootstrap_seqerakit   = "/test/secrets/minimal/seqerakit"
secrets_bootstrap_groundswell = "/test/secrets/minimal/groundswell"
secrets_bootstrap_wave_lite   = "/test/secrets/minimal/wave-lite"

aws_account = "123456789012"
aws_region  = "us-east-1"
aws_profile = "test-profile"
tower_container_version = "v25.2.0"

# Infrastructure flags - Use container DB
flag_create_external_db       = false
flag_use_existing_external_db = false
flag_use_container_db         = true
flag_create_new_vpc          = true
flag_use_existing_vpc        = false
flag_create_load_balancer    = false
flag_make_instance_public    = true
```

### Example Test Configuration (standard-rds.tfvars):
```hcl
# Test B: Standard deployment with RDS
app_name = "WILL_BE_OVERRIDDEN"
secrets_bootstrap_tower       = "/test/secrets/standard/tower"

# Infrastructure flags - Create external RDS
flag_create_external_db       = true   # Key difference
flag_use_existing_external_db = false
flag_use_container_db         = false
flag_create_new_vpc          = true
flag_use_existing_vpc        = false
flag_create_load_balancer    = true
flag_make_instance_public    = false
```

## GitHub Runner Limits and Considerations

### Concurrent Jobs Limits:
- **Public Repos:** 20 concurrent jobs (free, unlimited minutes)
- **Private Repos Free:** 20 concurrent jobs, 2,000 minutes/month
- **Private Repos Pro:** 40 concurrent jobs, 3,000 minutes/month
- **Private Repos Enterprise:** 500 concurrent jobs, 50,000 minutes/month

### Time Limits:
- **Maximum job execution:** 6 hours (hard limit)
- **Idle timeout:** 45 minutes of no output
- **Maximum workflow:** 35 days

### Cost Optimization Strategies:
1. Tiered testing (smoke/standard/full)
2. Schedule-based testing for expensive suites
3. Self-hosted runners for heavy usage
4. Conditional testing based on changed files

## Graceful Shutdown and Cleanup Strategies

### Method 1: Kill Switch Pattern
Create a centralized kill switch that all matrix jobs check:

```yaml
jobs:
  create-kill-switch:
    steps:
      - name: Create kill switch in S3
        run: |
          KILL_SWITCH="test-runs/${{ github.run_id }}/kill-switch.json"
          echo '{"active": false}' | aws s3 cp - "s3://${STATE_BUCKET}/${KILL_SWITCH}"

  test-deployment:
    steps:
      - name: Deploy with kill switch monitoring
        run: |
          check_kill_switch() {
            STATUS=$(aws s3 cp "s3://${STATE_BUCKET}/${KILL_SWITCH}" - | jq -r '.active')
            if [ "$STATUS" = "true" ]; then
              echo "Kill switch activated - initiating cleanup"
              terraform destroy -auto-approve -refresh=false
              exit 1
            fi
          }
          
          terraform apply -auto-approve &
          TF_PID=$!
          
          while kill -0 $TF_PID 2>/dev/null; do
            check_kill_switch
            sleep 30
          done
```

### Method 2: Emergency Cleanup Workflow
Separate workflow for coordinated cleanup of failed deployments:

```yaml
name: Emergency Cleanup
on:
  workflow_dispatch:
    inputs:
      run_id:
        description: 'GitHub Run ID to cleanup'
      test_id:
        description: 'Test ID from prepare-configs'

jobs:
  cleanup-matrix:
    strategy:
      matrix:
        config: ${{ fromJson(needs.identify-resources.outputs.configs) }}
    steps:
      - name: Force destroy all resources
        run: |
          terraform init -backend-config="bucket=${STATE_BUCKET}" \
            -backend-config="key=tests/${TEST_ID}/${CONFIG}/terraform.tfstate"
          terraform destroy -auto-approve -parallelism=5 -refresh=false
```

## Targeted Test Execution

### Dynamic Matrix with Workflow Inputs:
```yaml
on:
  workflow_dispatch:
    inputs:
      test_configs:
        description: 'Comma-separated configs or "all"'
        default: 'all'
      test_pattern:
        description: 'Glob pattern (e.g., "*-rds")'

jobs:
  prepare-configs:
    steps:
      - name: Build dynamic matrix
        run: |
          if [ "${{ github.event.inputs.test_configs }}" = "all" ]; then
            SELECTED_CONFIGS=$(ls test-configs/*.tfvars | xargs -n1 basename | sed 's/.tfvars//')
          elif [ -n "${{ github.event.inputs.test_configs }}" ]; then
            IFS=',' read -ra CONFIGS <<< "${{ github.event.inputs.test_configs }}"
            SELECTED_CONFIGS="${CONFIGS[@]}"
          elif [ -n "${{ github.event.inputs.test_pattern }}" ]; then
            SELECTED_CONFIGS=$(ls test-configs/${{ github.event.inputs.test_pattern }}.tfvars)
          fi
```

### Usage Examples:
```bash
# Run specific configs
gh workflow run test.yml -f test_configs="minimal,standard-rds"

# Test pattern matching
gh workflow run test.yml -f test_pattern="*-rds"

# Run all tests
gh workflow run test.yml -f test_configs="all"
```

## Handling Transient Failures and Resume Capabilities

### Strategy 1: Automatic Retry with State Preservation
```yaml
- name: Deploy with intelligent retry
  run: |
    MAX_ATTEMPTS=3
    ATTEMPT=1
    
    while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
      if terraform apply -auto-approve 2>&1 | tee apply.log; then
        break
      else
        if grep -E "RequestLimitExceeded|Throttling" apply.log; then
          WAIT_TIME=$((60 * $ATTEMPT))  # Exponential backoff
          sleep $WAIT_TIME
        elif grep -E "VcpuLimitExceeded" apply.log; then
          echo 'ec2_instance_type = "t3.small"' >> override.auto.tfvars
        fi
        ATTEMPT=$((ATTEMPT + 1))
      fi
    done
```

### Strategy 2: Checkpoint-Based Resume
```yaml
- name: Deploy with checkpoints
  run: |
    CHECKPOINT_FILE="checkpoint-${{ matrix.config }}.json"
    
    # Check for existing checkpoint
    if aws s3 cp s3://${STATE_BUCKET}/checkpoints/checkpoint.json $CHECKPOINT_FILE; then
      RESUME_FROM=$(jq -r '.last_successful_step' $CHECKPOINT_FILE)
    else
      RESUME_FROM="start"
    fi
    
    # Phased deployment
    if [[ "$RESUME_FROM" < "vpc" ]]; then
      terraform apply -target=module.vpc -auto-approve
      update_checkpoint "vpc"
    fi
    
    if [[ "$RESUME_FROM" < "database" ]]; then
      terraform apply -target=aws_db_instance.main -auto-approve
      update_checkpoint "database"
    fi
```

### Strategy 3: Manual Resume Workflow
```yaml
name: Resume Failed Deployment
on:
  workflow_dispatch:
    inputs:
      test_id:
        description: 'Test ID from original run'
      configs_to_resume:
        description: 'Configs to resume or "all-failed"'

jobs:
  resume-deployment:
    steps:
      - name: Initialize with existing state
        run: |
          terraform init \
            -backend-config="bucket=${STATE_BUCKET}" \
            -backend-config="key=tests/${TEST_ID}/${CONFIG}/terraform.tfstate"
      
      - name: Resume deployment
        run: |
          terraform apply -auto-approve
```

## Final Recommendations

For the specific use case:
1. **Use Matrix-Based Solution** with S3 backend for state persistence
2. **Implement Kill Switch Pattern** for emergency stops
3. **Add Checkpoint-Based Resume** for complex deployments
4. **Include Dynamic Matrix Selection** for targeted testing
5. **Implement Automatic Retry** with intelligent error handling

Key considerations:
- Limit parallelism to 3-5 concurrent deployments
- Use unique state files per test configuration
- Implement automatic cleanup with manual override option
- Add cost monitoring via AWS tags
- Create comprehensive test result reporting

This approach balances:
- Speed (parallel execution)
- Reliability (state preservation, retry logic)
- Debuggability (persistent states, detailed logs)
- Flexibility (targeted execution, manual intervention)
- Cost-effectiveness (resource limits, cleanup automation)