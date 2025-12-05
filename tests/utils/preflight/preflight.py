import json
import subprocess
import sys


def check_aws_sso_token():
    """
    Terraform plan will fail if valid AWS SSO token not present.
    Invoke AWS CLI via subprocess call (STS get-caller-identity).
    Raises RuntimeError if token is expired or invalid
    """
    try:
        result = subprocess.run(
            ["aws", "sts", "get-caller-identity"],
            capture_output=True,
            text=True,
            check=True,
        )

        print("AWS SSO Token is valid!")

        # Parse the JSON output
        identity = json.loads(result.stdout)
        print(f"AWS Account: {identity['Account']}")
        print(f"IAM User/Role: {identity['Arn']}")

        return True

    except subprocess.CalledProcessError as e:
        # AWS CLI returned a non-zero exit code
        print(str(e), file=sys.stderr)

        # Trigger SSO login
        print("Initiating AWS SSO login.")
        subprocess.run(["aws", "sso", "login"])
        sys.exit(1)

    except Exception as e:
        raise RuntimeError(f"Unexpected error checking AWS SSO token: {str(e)}")
