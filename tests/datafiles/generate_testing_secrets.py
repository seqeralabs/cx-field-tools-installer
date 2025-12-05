#!/usr/bin/env python3

import json
import sys
from pathlib import Path

# Add the project root to Python path to avoid import conflicts
project_root = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(project_root))

from tests.utils.config import FP


def modify_all_ssm_json_for_testing():
    """
    Loads all SSM sensitive values JSON files, modifies ssm_key paths for testing,
    and provides a section to customize all values.
    """

    # Get the project root directory
    templates_dir = Path(FP.ROOT) / "templates"
    test_data_dir = Path(FP.ROOT) / "tests" / "datafiles" / "secrets"
    Path(test_data_dir).mkdir(parents=True, exist_ok=True)

    # Find all SSM JSON files
    json_files = list(templates_dir.glob("ssm_sensitive_values_*.json"))

    if not json_files:
        print("No SSM sensitive values JSON files found!")
        return

    print(f"{json_files=}")

    all_data = {}

    for json_file in json_files:
        print(f"\nProcessing: {json_file.name}")
        print("-" * 50)

        # Load the JSON file
        with open(json_file, "r") as f:
            data = json.load(f)

        # Step 1: Modify ssm_key values to replace "/tower-template" with "/tower-testing"
        for key, value in data.items():
            if "ssm_key" in value:
                original_ssm_key = value["ssm_key"]
                modified_ssm_key = original_ssm_key.replace("/tower-template", "/tower-testing")
                value["ssm_key"] = modified_ssm_key
                print(f"Modified {key}: {original_ssm_key} -> {modified_ssm_key}")

        # Store the modified data
        file_key = json_file.stem  # filename without extension
        all_data[file_key] = data

    # Step 2: Value assignment section - CUSTOMIZE THESE VALUES AS NEEDED
    # =======================================================================
    # NOTE: Modify the values below for your testing environment
    # =======================================================================

    # TOWER VALUES (ssm_sensitive_values_tower.json)
    if "ssm_sensitive_values_tower" in all_data:
        tower_data = all_data["ssm_sensitive_values_tower"]

        # License and Harbor credentials
        tower_data["TOWER_LICENSE"]["value"] = "YOUR_TEST_LICENSE_KEY"
        tower_data["HARBOR_USERNAME"]["value"] = "your_harbor_username"
        tower_data["HARBOR_PASSWORD"]["value"] = "your_harbor_password"

        # Crypto and JWT secrets (use strong random values in real usage)
        tower_data["TOWER_CRYPTO_SECRET"]["value"] = "test_crypto_secret_32_chars_long"
        tower_data["TOWER_JWT_SECRET1"]["value"] = "test_jwt_secret_must_match_secret2"
        tower_data["TOWER_JWT_SECRET2"]["value"] = "test_jwt_secret_must_match_secret2"

        # SMTP credentials (if using external SMTP)
        tower_data["TOWER_SMTP_USER"]["value"] = "test_smtp_user@example.com"
        tower_data["TOWER_SMTP_PASSWORD"]["value"] = "test_smtp_password"

        # Database credentials
        tower_data["TOWER_DB_USER"]["value"] = "tower_test_user"
        tower_data["TOWER_DB_PASSWORD"]["value"] = "tower_test_password"
        tower_data["TOWER_DB_MASTER_USER"]["value"] = "tower_test_master"
        tower_data["TOWER_DB_MASTER_PASSWORD"]["value"] = "tower_test_master_password"

        # OIDC configuration (if using OIDC)
        tower_data["TOWER_OIDC_CLIENT"]["value"] = "test_oidc_client_id"
        tower_data["TOWER_OIDC_SECRET"]["value"] = "test_oidc_client_secret"
        tower_data["TOWER_OIDC_ISSUER"]["value"] = "https://your-oidc-provider.com"

        # Google OAuth (if using Google auth)
        tower_data["TOWER_GOOGLE_CLIENT"]["value"] = "test_google_client_id"
        tower_data["TOWER_GOOGLE_SECRET"]["value"] = "test_google_client_secret"
        # Note: TOWER_GOOGLE_ISSUER is typically left as default

        # GitHub OAuth (if using GitHub auth)
        tower_data["TOWER_GITHUB_CLIENT"]["value"] = "test_github_client_id"
        tower_data["TOWER_GITHUB_SECRET"]["value"] = "test_github_client_secret"

    # GROUNDSWELL VALUES (ssm_sensitive_values_groundswell.json)
    if "ssm_sensitive_values_groundswell" in all_data:
        groundswell_data = all_data["ssm_sensitive_values_groundswell"]

        # Groundswell database credentials
        groundswell_data["SWELL_DB_USER"]["value"] = "swell_test_user"
        groundswell_data["SWELL_DB_PASSWORD"]["value"] = "swell_test_password"

    # SEQERAKIT VALUES (ssm_sensitive_values_seqerakit.json)
    if "ssm_sensitive_values_seqerakit" in all_data:
        seqerakit_data = all_data["ssm_sensitive_values_seqerakit"]

        # AWS credentials
        seqerakit_data["TOWER_AWS_USER"]["value"] = "test_aws_user"
        seqerakit_data["TOWER_AWS_PASSWORD"]["value"] = "test_aws_password"
        seqerakit_data["TOWER_AWS_ROLE"]["value"] = "arn:aws:iam::123456789012:role/test-role"

        # GitHub credentials
        seqerakit_data["TOWER_GITHUB_USER"]["value"] = "test_github_user"
        seqerakit_data["TOWER_GITHUB_TOKEN"]["value"] = "ghp_test_github_token_replace_me"

        # Docker credentials
        seqerakit_data["TOWER_DOCKER_USER"]["value"] = "test_docker_user"
        seqerakit_data["TOWER_DOCKER_TOKEN"]["value"] = "dckr_pat_test_docker_token"

        # CodeCommit credentials
        seqerakit_data["TOWER_CODECOMMIT_USER"]["value"] = "test_codecommit_user"
        seqerakit_data["TOWER_CODECOMMIT_PASSWORD"]["value"] = "test_codecommit_password"
        seqerakit_data["TOWER_CODECOMMIT_BASEURL"]["value"] = "https://git-codecommit.us-east-1.amazonaws.com"

    # WAVE LITE VALUES (ssm_sensitive_values_wave_lite.json)
    if "ssm_sensitive_values_wave_lite" in all_data:
        wave_lite_data = all_data["ssm_sensitive_values_wave_lite"]

        # Wave Lite database credentials
        wave_lite_data["WAVE_LITE_DB_MASTER_USER"]["value"] = "wave_lite_test_master"
        wave_lite_data["WAVE_LITE_DB_MASTER_PASSWORD"]["value"] = "wave_lite_test_master_password"
        wave_lite_data["WAVE_LITE_DB_LIMITED_USER"]["value"] = "wave_lite_test_limited"
        wave_lite_data["WAVE_LITE_DB_LIMITED_PASSWORD"]["value"] = "wave_lite_test_limited_password"

        # Wave Lite Redis auth
        wave_lite_data["WAVE_LITE_REDIS_AUTH"]["value"] = "wave_lite_test_redis_password"

    # # =======================================================================
    # # End of value assignment section
    # # =======================================================================

    # Save modified data to new files that mirror the original templates
    print("\n" + "=" * 60)
    print("CREATING MODIFIED TEMPLATE FILES")
    print("=" * 60)

    for file_key, data in all_data.items():
        # Create output filename by replacing original with "_testing"
        output_file = test_data_dir / f"{file_key}_testing.json"

        # Write the complete modified data structure to match original template
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        print(f"Created: {output_file}")
        print(f"  - Modified {len(data)} secrets")
        print("  - Changed all SSM keys from '/tower-template' to '/tower-testing'")
        print("  - Updated all values for testing environment")

    print(f"\nAll modified template files saved to: {templates_dir}")
    print(f"Total files created: {len(all_data)}")

    return all_data


if __name__ == "__main__":
    modify_all_ssm_json_for_testing()
