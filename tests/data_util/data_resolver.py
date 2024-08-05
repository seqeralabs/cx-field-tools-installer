import json
from pathlib import Path

RESOURCES_PATH = Path(__file__).parent.parent.joinpath("resources")


def inject_test_data(file):
    """
    Read the content of the json file,
    can be used for injecting test data set to tests,
    helps in separating test data from the tests
    """
    file = str(RESOURCES_PATH.joinpath(file))
    with open(file, "r") as f:
        raw_data = json.load(f)
    yield raw_data
