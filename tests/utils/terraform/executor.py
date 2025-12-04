import subprocess
from pathlib import Path

from tests.utils.config import FP


## ------------------------------------------------------------------------------------
## Subprocess Utility Functions
## ------------------------------------------------------------------------------------
# NOTE: PIPE needed to capture plan output (for apply), but causes noisy console.
#       Replaced with shell-type subprocess.run commands Bash redirect output to files.
def execute_subprocess(command: str) -> bytes:
    """
    Execute a subprocess command.
    """
    result = subprocess.run(
        command,
        check=True,
        # stdout=subprocess.PIPE,
        stdout=subprocess.DEVNULL,  # > /dev/null
        stderr=subprocess.STDOUT,  # 2>&1
        shell=True,
    ).stdout

    return result


class TF:
    """
    Terraform command execution helpers.
      - Plan based on core tfvars, core override, and testcase override.
      - Targeted apply/destroy available if necessary. eg.
        - `terraform apply   --auto-approve tfpan`
        - `terraform apply   --auto-approve -target=null_resource.my_resource`
        - `terraform destroy --auto-approve`
        - `terraform destroy --auto-approve -target=null_resource.my_resource`
    """

    @staticmethod
    def plan(qualifier: str = "") -> None:
        """Run terraform plan with caching support."""
        files_to_purge = [FP.TFPLAN_FILE_LOCATION, FP.TFPLAN_JSON_LOCATION]

        for file in files_to_purge:
            Path(file).unlink(missing_ok=True)

        command = f"terraform plan {qualifier} -out=tfplan -refresh=false && terraform show -json tfplan > tfplan.json"
        execute_subprocess(command)

    @staticmethod
    def apply(qualifier: str = "") -> None:
        """Run terraform apply (defaults to using tfplan)."""
        qualifier = qualifier if len(qualifier) > 0 else "tfplan"
        command = f"terraform apply --auto-approve {qualifier}"
        execute_subprocess(command)

    @staticmethod
    def destroy(qualifier: str = "") -> None:
        """Run terraform destroy."""
        qualifier = qualifier if len(qualifier) > 0 else ""
        command = f"terraform destroy --auto-approve {qualifier}"
        execute_subprocess(command)
