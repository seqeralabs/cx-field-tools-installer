# Optional Config - Update Githooks Settings

The project ships with a `.githooks` folder, which contains a Python script that wil scan your `terraform.tfvars` file for configuration mismatches which cause your deployment to fail.

To automatically invoke the script prior to a commit to your git repository, execute the following in the root of your project: `git config core.hooksPath .githooks`.
