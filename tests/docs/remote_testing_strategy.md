# Remote Testing Strategy

Can think of two options:

1. Use Github Actions matrix strategy.
2. Try to use CX-Playground K8s cluster, spinning up a pod for each testcase.

While I think the K8s mechanism could be interesting from a technical challenge, GHA seems to make more sense from:

1. Implementation maturity
2. Better alignment to Seqera technology standards.


## GitHub Implementation
ChatGPT suggests the following:

Key Points:
- Each stack = a Terraform tfvars file, e.g. stack-a.tfvars, stack-b.tfvars, etc.
- Each permutation is defined in a matrix.
- Each matrix job runs concurrently by default.
- Each job:
    - Deploys a unique Terraform stack using its own tfvars.
    - Waits for deployment to finish.
    - Runs its unique pytest test suite (e.g., tests/stack-a/, tests/stack-b/).
    - Optionally tears down the stack after testing.

```yaml
name: Terraform Multi-Stack Testing

on:
  push:
    branches: [ main ]

jobs:
  test-permutations:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        stack:
          - name: stack-a
            tfvars: stack-a.tfvars
            test_dir: tests/stack-a
          - name: stack-b
            tfvars: stack-b.tfvars
            test_dir: tests/stack-b
          - name: stack-c
            tfvars: stack-c.tfvars
            test_dir: tests/stack-c

    name: Deploy and Test ${{ matrix.stack.name }}
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.6.6

      - name: Terraform Init
        run: terraform init

      - name: Terraform Apply for ${{ matrix.stack.name }}
        run: |
          terraform apply -auto-approve -var-file=${{ matrix.stack.tfvars }}

      - name: Wait for Resources (Optional Polling)
        run: |
          # Example: wait for RDS or endpoint to be available
          # sleep or curl + retries here if needed
          echo "Waiting for infrastructure readiness..."

      - name: Install Python Dependencies
        run: pip install -r ${{ matrix.stack.test_dir }}/requirements.txt

      - name: Run Tests
        run: pytest ${{ matrix.stack.test_dir }}

      - name: Terraform Destroy (optional teardown)
        if: always()
        run: terraform destroy -auto-approve -var-file=${{ matrix.stack.tfvars }}
```

Considerations:
- Overrides and plans currently generated during `pytest` test run-time. This seems to require definition upfront.
- TBD if stacks should deploy everything in each test (_probably_) or try to leverage pre-existing infra to avoid AWS limits (e.g. VPC quota).
- How can I get into a runner if a test fails, to easily recreate?
    - Do I need to get into the runner, or is it enough to just know what's failing since I should be able to deploy the same test locally?