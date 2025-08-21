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

from testcontainers.compose import DockerCompose

from tests.utils.config import root
from tests.utils.config import test_docker_compose_file
from tests.utils.docker_compose import prepare_wave_only_docker_compose
from tests.utils.filehandling import read_yaml, read_file


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
