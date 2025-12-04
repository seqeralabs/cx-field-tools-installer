import pytest

from tests.utils.local import generate_namespaced_dictionaries
from tests.utils.terraform.executor import prepare_plan

"""
These tests used to validate the outputs emitted by Terraform plan (with particular focus on those emitted by module.connection_strings).

When making any change to the `connection_strings` module, this should be run as a sanity check prior to full config file testing, since the 
config file testing relies on these same outputs. A mistake found and fixed here, avoids a mistake downstream that is harder to generate and fix.

NOTE: Module outputs may not be available if you do a targeted plan and/or don't call them out as root level outputs. To compensate for this:
  1) All tests here make use of a full `terrform plan`. This takes a bit longer for the 1st time run, but we cache the JSON output so n+1 is much faster.
  2) We make use of `tests/012_testing_outputs.tf` to define outputs that are desired for testing purposes (e.g. various service's DNS) but not really 
     necessary for clients. As of Aug 22/25, I'm dumping these all out in the customer-facing outputs but intended to migrate several to the testing-only
     view (to occur in a discrete branch TBD). 
"""


## ------------------------------------------------------------------------------------
## MARK: Baseline
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.outputs
def test_outputs_baseline_all_enabled(session_setup):
    """Conduct baseline assertions when all SP services turned on."""

    tf_modifiers = """#NONE"""
    plan = prepare_plan(tf_modifiers)
    plan_artefacts, secrets = generate_namespaced_dictionaries(plan)
    vars, outputs, _, _ = plan_artefacts

    # Run assertions
    assert outputs["aws_account_id"] == "N/A"
    assert outputs["aws_caller_arn"] == "N/A"
    assert outputs["aws_caller_user"] == "N/A"

    assert outputs["tower_base_url"] == "autodc.dev-seqera.net"
    assert outputs["tower_server_url"] == "https://autodc.dev-seqera.net"
    assert outputs["tower_api_endpoint"] == "https://autodc.dev-seqera.net/api"

    assert outputs["tower_db_dns"] == "db"
    assert (
        outputs["tower_db_url"]
        == "jdbc:mysql://db:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true"
    )

    assert outputs["tower_redis_dns"] == "redis"
    assert outputs["tower_redis_url"] == "redis://redis:6379"

    assert outputs["swell_db_dns"] == "db"
    assert outputs["swell_db_url"] == "mysql://db:3306/swell"

    assert outputs["tower_connect_dns"] == "connect.autodc.dev-seqera.net"
    assert outputs["tower_connect_wildcard_dns"] == "*.autodc.dev-seqera.net"
    assert outputs["tower_connect_server_url"] == "https://connect.autodc.dev-seqera.net"
    assert outputs["tower_connect_redis_url"] == "redis:6379"

    assert outputs["tower_wave_dns"] == "wave.autodc.dev-seqera.net"
    assert outputs["tower_wave_url"] == "https://wave.autodc.dev-seqera.net"
    assert outputs["wave_lite_db_dns"] == "wave-db"
    assert outputs["wave_lite_db_url"] == "jdbc:postgresql://wave-db:5432/wave"
    assert outputs["wave_lite_redis_dns"] == "wave-redis"
    assert outputs["wave_lite_redis_url"] == "redis://wave-redis:6379"

    """
    Outputs we don't worry about
      - ec2_ssh_key
      - aws_ec2_private_ip
      - aws_ec2_public_ip
    """


@pytest.mark.local
@pytest.mark.outputs
def test_outputs_baseline_all_disabled(session_setup):
    """Conduct baseline assertions when all SP services turned on."""

    # TODO: Get rid of email disabling. This should be a discrete check.
    tf_modifiers = """
        flag_use_aws_ses_iam_integration    = false
        flag_use_existing_smtp              = true
        flag_enable_groundswell             = false
        flag_data_explorer_enabled          = false
        flag_enable_data_studio             = false
        flag_use_wave                       = false
        flag_use_wave_lite                  = false
    """
    plan = prepare_plan(tf_modifiers)
    plan_artefacts, secrets = generate_namespaced_dictionaries(plan)
    vars, outputs, _, _ = plan_artefacts

    # Run assertions
    assert outputs["aws_account_id"] == "N/A"
    assert outputs["aws_caller_arn"] == "N/A"
    assert outputs["aws_caller_user"] == "N/A"

    assert outputs["tower_base_url"] == "autodc.dev-seqera.net"
    assert outputs["tower_server_url"] == "https://autodc.dev-seqera.net"
    assert outputs["tower_api_endpoint"] == "https://autodc.dev-seqera.net/api"

    assert outputs["tower_db_dns"] == "db"
    assert (
        outputs["tower_db_url"]
        == "jdbc:mysql://db:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true"
    )

    assert outputs["tower_redis_dns"] == "redis"
    assert outputs["tower_redis_url"] == "redis://redis:6379"

    assert outputs["swell_db_dns"] == "N/A"
    assert outputs["swell_db_url"] == "N/A"

    assert outputs["tower_connect_dns"] == "N/A"
    assert outputs["tower_connect_wildcard_dns"] == "N/A"
    assert outputs["tower_connect_server_url"] == "N/A"
    assert outputs["tower_connect_redis_url"] == "N/A"

    assert outputs["tower_wave_dns"] == "N/A"
    assert outputs["tower_wave_url"] == "N/A"
    assert outputs["wave_lite_db_dns"] == "N/A"
    assert outputs["wave_lite_db_url"] == "N/A"
    assert outputs["wave_lite_redis_dns"] == "N/A"
    assert outputs["wave_lite_redis_url"] == "N/A"

    """
    Outputs we don't worry about
      - ec2_ssh_key
      - aws_ec2_private_ip
      - aws_ec2_public_ip
    """


## ------------------------------------------------------------------------------------
## MARK: No HTTPS
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.outputs
def test_outputs_no_https_all_enabled(session_setup):
    """Conduct baseline assertions when all SP services turned on."""

    tf_modifiers = """
        flag_create_load_balancer                       = false
        flag_do_not_use_https                           = true
    """
    plan = prepare_plan(tf_modifiers)
    plan_artefacts, secrets = generate_namespaced_dictionaries(plan)
    vars, outputs, _, _ = plan_artefacts

    # Run assertions
    assert outputs["aws_account_id"] == "N/A"
    assert outputs["aws_caller_arn"] == "N/A"
    assert outputs["aws_caller_user"] == "N/A"

    assert outputs["tower_base_url"] == "autodc.dev-seqera.net"
    assert outputs["tower_server_url"] == "http://autodc.dev-seqera.net:8000"
    assert outputs["tower_api_endpoint"] == "http://autodc.dev-seqera.net:8000/api"

    assert outputs["tower_db_dns"] == "db"
    assert (
        outputs["tower_db_url"]
        == "jdbc:mysql://db:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true"
    )

    assert outputs["tower_redis_dns"] == "redis"
    assert outputs["tower_redis_url"] == "redis://redis:6379"

    assert outputs["swell_db_dns"] == "db"
    assert outputs["swell_db_url"] == "mysql://db:3306/swell"

    assert outputs["tower_connect_dns"] == "N/A"
    assert outputs["tower_connect_wildcard_dns"] == "N/A"
    assert outputs["tower_connect_server_url"] == "N/A"
    assert outputs["tower_connect_redis_url"] == "N/A"

    assert outputs["tower_wave_dns"] == "N/A"
    assert outputs["tower_wave_url"] == "N/A"
    assert outputs["wave_lite_db_dns"] == "N/A"
    assert outputs["wave_lite_db_url"] == "N/A"
    assert outputs["wave_lite_redis_dns"] == "N/A"
    assert outputs["wave_lite_redis_url"] == "N/A"

    """
    Outputs we don't worry about
      - ec2_ssh_key
      - aws_ec2_private_ip
      - aws_ec2_public_ip
    """


@pytest.mark.local
@pytest.mark.outputs
def test_outputs_no_https_all_disabled(session_setup):
    """Conduct baseline assertions when all SP services turned on."""

    tf_modifiers = """
        flag_create_load_balancer                       = false
        flag_do_not_use_https                           = true

        flag_enable_groundswell                         = false
        flag_enable_data_studio                         = false
        flag_use_wave_lite                              = false
    """
    plan = prepare_plan(tf_modifiers)

    plan, secrets = generate_namespaced_dictionaries(plan)
    vars, outputs, vars_dict, _ = plan

    # Run assertions
    assert outputs["aws_account_id"] == "N/A"
    assert outputs["aws_caller_arn"] == "N/A"
    assert outputs["aws_caller_user"] == "N/A"

    assert outputs["tower_base_url"] == "autodc.dev-seqera.net"
    assert outputs["tower_server_url"] == "http://autodc.dev-seqera.net:8000"
    assert outputs["tower_api_endpoint"] == "http://autodc.dev-seqera.net:8000/api"

    assert outputs["tower_db_dns"] == "db"
    assert (
        outputs["tower_db_url"]
        == "jdbc:mysql://db:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true"
    )

    assert outputs["tower_redis_dns"] == "redis"
    assert outputs["tower_redis_url"] == "redis://redis:6379"

    assert outputs["swell_db_dns"] == "N/A"
    assert outputs["swell_db_url"] == "N/A"

    assert outputs["tower_connect_dns"] == "N/A"
    assert outputs["tower_connect_wildcard_dns"] == "N/A"
    assert outputs["tower_connect_server_url"] == "N/A"
    assert outputs["tower_connect_redis_url"] == "N/A"

    assert outputs["tower_wave_dns"] == "N/A"
    assert outputs["tower_wave_url"] == "N/A"
    assert outputs["wave_lite_db_dns"] == "N/A"
    assert outputs["wave_lite_db_url"] == "N/A"
    assert outputs["wave_lite_redis_dns"] == "N/A"
    assert outputs["wave_lite_redis_url"] == "N/A"

    """
    Outputs we don't worry about
      - ec2_ssh_key
      - aws_ec2_private_ip
      - aws_ec2_public_ip
    """


## ------------------------------------------------------------------------------------
## MARK: Connect Path-Routing
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.outputs
def test_outputs_connect_alb_pathrouting(session_setup):
    """Test Conect path-based routing. Ensure default 'connect.' is not present."""
    # Given
    tf_modifiers = """
        flag_create_load_balancer                       = true
        flag_do_not_use_https                           = false

        flag_studio_enable_path_routing                 = true
        data_studio_path_routing_url                    = "autoconnect.example.com"
    """

    # When
    plan = prepare_plan(tf_modifiers)
    plan_artefacts, secrets = generate_namespaced_dictionaries(plan)
    vars, outputs, _, _ = plan_artefacts

    # Then
    assert outputs["tower_connect_dns"] == "autoconnect.example.com"
    assert outputs["tower_connect_wildcard_dns"] == "autoconnect.example.com"
    assert outputs["tower_connect_server_url"] == "https://autoconnect.example.com"


@pytest.mark.local
@pytest.mark.outputs
def test_outputs_connect_ec2_pathrouting(session_setup):
    """Test Conect path-based routing. Ensure default 'connect.' is not present."""
    # Given
    tf_modifiers = """
        flag_create_load_balancer                       = true
        flag_do_not_use_https                           = false

        flag_studio_enable_path_routing                 = true
        data_studio_path_routing_url                    = "autoconnect.example.com"
    """

    # When
    plan = prepare_plan(tf_modifiers)
    plan_artefacts, secrets = generate_namespaced_dictionaries(plan)
    vars, outputs, _, _ = plan_artefacts

    # Then
    assert outputs["tower_connect_dns"] == "autoconnect.example.com"
    assert outputs["tower_connect_wildcard_dns"] == "autoconnect.example.com"
    assert outputs["tower_connect_server_url"] == "https://autoconnect.example.com"
