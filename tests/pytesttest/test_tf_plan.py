import configparser

import pytest

# from tests.data_util.data_resolver import inject_test_data
from data_util.data_resolver import inject_test_data

# https://betterprogramming.pub/terraform-resource-testing-101-c9da424faaf3

# # read values in .ini file
# config = configparser.ConfigParser()
# config.read("tests/resources/datatable.ini")

# for sect in config.sections():
#     resource_names = list(config["RESOURCES"].values())
#     print(resource_names)


# class TestPlan:
#     # read Terraform JSON plan file
#     test_plan = inject_test_data(file="tf_plan/plan.json")

#     @pytest.mark.parametrize("plan", test_plan)
#     def test_resource_names(self, plan):
#         # drill down into the needed json section
#         resources = plan["planned_values"]["root_module"]["resources"]
#         # retrieve all values of 'name' key in section of json
#         names_from_json = [resource["name"] for resource in resources]

#         # bi directional delta of lists
#         diff1 = [name for name in resource_names if name not in names_from_json]
#         diff2 = [name for name in names_from_json if name not in resource_names]
#         # print if there are any differences between json and .ini values
#         print(diff1 + diff2)

#         # assert that there are no differences
#         assert not diff1 and not diff2


test_plan = inject_test_data(file="tf_plan/plan.json")
kvs = [("app_name", "tower-dev"), ("aws_region", "us-east-1")]


# pytest -rs


@pytest.fixture(scope="function")
def plan():
    """
    `test_plan = inject_test_data(file="tf_plan/plan.json")` seems to create a generator,
    which SEEMS to have next() called on it when it is passed in as a parametrized value.
    First invocation works, n+1 fails to generator being empty.
    i.e. "got empty parameter set ['plan'], function test_example_check_kvs at /home/deeplearning/cx-field-tools-installer/tests/terraform/test_tf_plan.py:61"

    Once I moved the logic to function-level fixture, I could consistently generate a
    new instance but would get "generator object not subscriptable" error. Solved by
    manually invocating next() before returning object from fixture.
    """
    return next(inject_test_data(file="tf_plan/plan.json"))


# Old way where file data is generated first and passed in as parameter
@pytest.mark.parametrize("plan", test_plan)
def test_db_connection_string(plan):
    resources = plan["prior_state"]["values"]["root_module"]["resources"]
    db_connection_string_resource = [
        resource
        for resource in resources
        if resource["name"] == "generate_db_connection_string"
    ]
    db_connection_string_resource = db_connection_string_resource[0]

    db_connection_string = db_connection_string_resource["values"]["result"]["value"]
    assert db_connection_string.count("?") == 1


@pytest.mark.parametrize("key,value", kvs)
def test_example_check_kvs1(plan, key, value):
    variables = plan["variables"]
    assert variables[key]["value"] == value


# This leaks if you test the secret directly.
def test_secret_stack_trace(plan):
    resources = plan["planned_values"]["root_module"]["resources"]

    secret = [
        resource
        for resource in resources
        if resource.get("index") == "SWELL_DB_PASSWORD"
    ]

    secret = secret[0]
    # assert secret["values"]["value"] != ""
    assert secret["values"]["value"] == ""


def test_secrets_stack_trace(plan):
    resources = plan["planned_values"]["root_module"]["resources"]

    assert resources == []


# Unnecessary complexity. Handled by cleaner function above.
# # @pytest.mark.parametrize("plan", test_plan2)
# @pytest.mark.parametrize("kv", kvs)
# def test_example_check_kvs2(plan, kv):
#     # def test_example_check_kvs(kv, plan):
#     variables = plan["variables"]
#     k, v = kv
#     assert variables[k]["value"] == v
