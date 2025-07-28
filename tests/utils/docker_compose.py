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

    # Purge volumes (DB)
    indices_to_purge = []
    for i, volume in enumerate(retained_content["services"]["wave-db"]["volumes"]):
        if ":/var/lib/postgresql/data" in volume:
            indices_to_purge.append(i)
    for i in reversed(indices_to_purge):
        retained_content["services"]["wave-db"]["volumes"].pop(i)
    if len(retained_content["services"]["wave-db"]["volumes"]) == 0:
        retained_content["services"]["wave-db"].pop("volumes")

    # Purge volumes (Redis)
    indices_to_purge = []
    for i, volume in enumerate(retained_content["services"]["wave-redis"]["volumes"]):
        if ":/data" in volume:
            indices_to_purge.append(i)
    for i in reversed(indices_to_purge):
        retained_content["services"]["wave-redis"]["volumes"].pop(i)
    if len(retained_content["services"]["wave-redis"]["volumes"]) == 0:
        retained_content["services"]["wave-redis"].pop("volumes")

    # The docker-commpose template file uses $HOME for its filemount roots.
    # 2. Change $HOME to `PROJECT_ROOT/assets/`

    text = yaml.dump(retained_content)
    text = text.replace("$HOME", f"{root}/assets")

    write_file(test_docker_compose_file, text)
