import pytest


"""
These tests validate the outputs emitted by `module.connection_strings` for a representative
set of scenarios. They're a sanity check before the broader templatefile-content tests, since
the templatefile tests rely on the same module outputs being correct.

After the precompute refactor, `module.connection_strings.*` values are resolved in parallel
at session setup (one `terraform console` call per scenario) and cached to
`tests/.scenario_cache/{hash}/outputs.json`. The `scenario_outputs` fixture reads that file.

The previous version of this file also asserted on `aws_account_id`/`aws_caller_arn`/
`aws_caller_user` — those always evaluate to "N/A" in mock mode (per the
`var.use_mocks ? "N/A" : data.aws_caller_identity.current[0].X` ternary in `012_outputs.tf`).
Asserting that a mock returns its mock value tests nothing useful, so those assertions are
dropped along with the `terraform plan` / AWS-credential dependency they imposed.
"""


## ------------------------------------------------------------------------------------
## MARK: Baseline
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.outputs
def test_outputs_baseline_all_enabled(scenario_outputs):
    """Conduct baseline assertions when all SP services turned on."""
    outputs = scenario_outputs

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


@pytest.mark.local
@pytest.mark.outputs
@pytest.mark.tfvars("""
    flag_use_aws_ses_iam_integration    = false
    flag_use_existing_smtp              = true
    flag_enable_groundswell             = false
    flag_data_explorer_enabled          = false
    flag_enable_data_studio             = false
    flag_use_wave                       = false
    flag_use_wave_lite                  = false
""")
def test_outputs_baseline_all_disabled(scenario_outputs):
    """Conduct baseline assertions when all SP services turned off."""
    outputs = scenario_outputs

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


## ------------------------------------------------------------------------------------
## MARK: No HTTPS
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.outputs
@pytest.mark.tfvars("""
    flag_create_load_balancer                       = false
    flag_do_not_use_https                           = true
""")
def test_outputs_no_https_all_enabled(scenario_outputs):
    """No-https variant when all SP services are on."""
    outputs = scenario_outputs

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


@pytest.mark.local
@pytest.mark.outputs
@pytest.mark.tfvars("""
    flag_create_load_balancer                       = false
    flag_do_not_use_https                           = true

    flag_enable_groundswell                         = false
    flag_enable_data_studio                         = false
    flag_use_wave_lite                              = false
""")
def test_outputs_no_https_all_disabled(scenario_outputs):
    """No-https variant when SP services are off."""
    outputs = scenario_outputs

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


## ------------------------------------------------------------------------------------
## MARK: Connect Path-Routing
## ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.outputs
@pytest.mark.tfvars("""
    flag_create_load_balancer                       = true
    flag_do_not_use_https                           = false

    flag_studio_enable_path_routing                 = true
    data_studio_path_routing_url                    = "autoconnect.example.com"
""")
def test_outputs_connect_alb_pathrouting(scenario_outputs):
    """Test Connect path-based routing. Ensure default 'connect.' is not present."""
    outputs = scenario_outputs

    assert outputs["tower_connect_dns"] == "autoconnect.example.com"
    assert outputs["tower_connect_wildcard_dns"] == "autoconnect.example.com"
    assert outputs["tower_connect_server_url"] == "https://autoconnect.example.com"


@pytest.mark.local
@pytest.mark.outputs
@pytest.mark.tfvars("""
    flag_create_load_balancer                       = true
    flag_do_not_use_https                           = false

    flag_studio_enable_path_routing                 = true
    data_studio_path_routing_url                    = "autoconnect.example.com"
""")
def test_outputs_connect_ec2_pathrouting(scenario_outputs):
    """Test Connect path-based routing in the EC2-direct variant."""
    outputs = scenario_outputs

    assert outputs["tower_connect_dns"] == "autoconnect.example.com"
    assert outputs["tower_connect_wildcard_dns"] == "autoconnect.example.com"
    assert outputs["tower_connect_server_url"] == "https://autoconnect.example.com"
