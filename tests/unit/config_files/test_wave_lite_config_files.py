import pytest
import subprocess
import json
import tempfile
import os
import time
import yaml
import urllib.request
import urllib.error
from pathlib import Path
import shutil

from tests.utils.config import root, sql_test_scratch_dir, expected_sql, ssm_wave_lite
from tests.utils.config import test_docker_compose_file

from testcontainers.compose import DockerCompose
from testcontainers.postgres import PostgresContainer

from tests.utils.docker_compose import prepare_wave_only_docker_compose

from tests.utils.filehandling import read_json, read_yaml, read_file
from tests.utils.filehandling import write_file, move_file, copy_file
from tests.utils.filehandling import parse_key_value_file


## ------------------------------------------------------------------------------------
## Wave Lite SQL File checks
## ------------------------------------------------------------------------------------
"""
NOTE: This test case lives in its own file because it uses a different mechanic than the other config
  file tests. Whereas the rest use `terraform console`, this one builds files from the src/ repo and
  then compares the result against generated-ahead-of-time references in the tests/datafiles/expected_results/
  folder.
"""


@pytest.mark.local
@pytest.mark.wave
def test_sql_files_wave(session_setup):
    """
    Scenario:
        - Confirm that Wave SQL files are properly processed by python file.
        - NOTE: Does not work same way as most other config files (baseline terraform variables + `terraform template`)

    How this works:
        1. Copy original .sql files from source to test location.
        2. Process copied files via sedalternative.py, this will populate with end-state values.
        3. Compare files vs test references in `tests/datafiles/expected_results/expected_sql/`
    """
    ## SETUP
    ## ========================================================================================
    # Always grab to-be-converted files from src/.
    # This ensures any forgotten-about modifications will be caught during the test.
    source_root           = f"{root}/assets/src/wave_lite_config/"
    script_path           = f"{root}/scripts/installer/utils/sedalternative.py"

    # Copy files to test location
    Path(sql_test_scratch_dir).mkdir(parents=True, exist_ok=True)
    shutil.copy(f"{source_root}/wave-lite-container-1.sql", f"{sql_test_scratch_dir}/wave-lite-container-1.sql")
    shutil.copy(f"{source_root}/wave-lite-container-2.sql", f"{sql_test_scratch_dir}/wave-lite-container-2.sql")
    shutil.copy(f"{source_root}/wave-lite-rds.sql", f"{sql_test_scratch_dir}/wave-lite-rds.sql")

    # Run conversion using hardcoded Wave Lite credentials.
    command = f"python3 {script_path} wave_lite_test_limited wave_lite_test_limited_password {sql_test_scratch_dir}"
    subprocess.run(
        command,
        shell=True,
        text=True,
        capture_output=False,
    )

    ## COMPARISON
    ## ========================================================================================
    wave_lite_container_1 = read_file(f"{sql_test_scratch_dir}/wave-lite-container-1.sql")
    wave_lite_container_2 = read_file(f"{sql_test_scratch_dir}/wave-lite-container-2.sql")
    wave_lite_rds         = read_file(f"{sql_test_scratch_dir}/wave-lite-rds.sql")

    ref_wave_lite_container_1 = read_file(f"{expected_sql}/wave-lite-container-1.sql")
    ref_wave_lite_container_2 = read_file(f"{expected_sql}/wave-lite-container-2.sql")
    ref_wave_lite_rds         = read_file(f"{expected_sql}/wave-lite-rds.sql")

    assert ref_wave_lite_container_1 == wave_lite_container_1
    assert ref_wave_lite_container_2 == wave_lite_container_2
    assert ref_wave_lite_rds == wave_lite_rds


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
@pytest.mark.testcontainer
def test_wave_lite_compose_deployment(session_setup, config_baseline_settings_default):
    """
    Test Wave containers (x4) in local docker-compose deployment.
    Creates a cut-down version of the full docker-compose.yml file generated for the EC2.
    Compose file is run and we ensure the service-info endpoint (via reverse proxy) is available.
    """

    # Prepare docker-compose file
    prepare_wave_only_docker_compose(root)
    folder_path = os.path.dirname(test_docker_compose_file)
    filename = os.path.basename(test_docker_compose_file)

    # Start docker-compose deployment
    with DockerCompose(context=folder_path, compose_file_name=filename, pull=True) as compose:
        # Test wave-lite service-info endpoint
        service_url = "http://localhost:9099/service-info"
        max_retries = 10
        delay = 3

        for attempt in range(max_retries):
            try:
                with urllib.request.urlopen(service_url, timeout=10) as response:
                    assert response.status == 200, f"Expected HTTP 200, got {response.status}"
                    response_data = json.loads(response.read().decode("utf-8"))

                assert "serviceInfo" in response_data
                service_info = response_data["serviceInfo"]
                assert "version" in service_info
                assert "commitId" in service_info

            except (urllib.error.URLError, json.JSONDecodeError, AssertionError) as e:
                if attempt == max_retries:
                    pytest.fail(
                        f"Failed to connect to wave-lite service at {service_url} after {max_retries} retries: {e}"
                    )
                time.sleep(delay)
