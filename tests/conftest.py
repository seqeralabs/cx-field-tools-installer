import pytest
import json


# TODO Add logger for agentic access

@pytest.fixture(scope="session", autouse=True)
def tfplan_json():
    with open("tfplan.json", "r") as f:
        yield json.load(f)
        print("Done")

        
        