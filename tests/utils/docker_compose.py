import yaml
from typing import Any

from tests.utils.local import read_yaml, write_file
from tests.utils.local import root, test_docker_compose_file


def prepare_wave_only_docker_compose(root: str) -> dict[str, Any]:
    """
    Prepare the wave-only docker-compose file.
    """
    # Read the docker-compose.yml file
    docker_compose_path = f"{root}/assets/target/docker_compose/docker-compose.yml"
    docker_compose_data = read_yaml(docker_compose_path)

    retained_content = {
        "services": {},
        "networks": {},
        "volumes": {},
        "configs": {},
        "secrets": {},
    }

    # Keep networks. Purge any service keys we dont want.
    desired_services = ["wave-lite", "wave-lite-reverse-proxy", "wave-db", "wave-redis"]
    for service in docker_compose_data["services"]:
        if service in desired_services:
            retained_content["services"][service] = docker_compose_data["services"][service]

    retained_content["networks"] = docker_compose_data["networks"]

    # The docker-commpose template file uses $HOME for its filemount roots. Change $HOME to `PROJECT_ROOT/assets/`
    #  /var/lib/postgresql/data    (postgres)
    #  /data                       (redis)
    text = yaml.dump(retained_content)
    text = text.replace("$HOME", f"{root}/assets/")
    # Dont want stateful containers - purge volume mount for:
    text = text.replace("  - $HOME/.wave/db/postgresql:/var/lib/postgresql/data", "")
    text = text.replace("  - $HOME/.wave/db/wave-lite-redis:/data", "")

    # Let the testcases write these out to temporary file.
    # Write the docker-compose.yml file
    # write_file(f"{root}/assets/target/docker_compose/docker-compose-wave-only.yml", yaml.dump(docker_compose_data))

    print(f"retained_content: {retained_content}")
    write_file(test_docker_compose_file, text)
    # return retained_content
