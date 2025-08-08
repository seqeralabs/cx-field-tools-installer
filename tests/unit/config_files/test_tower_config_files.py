import pytest
import subprocess
import json
import os
import tempfile
import time
from pathlib import Path

from types import SimpleNamespace

from tests.utils.local import root, test_tfvars_target, test_tfvars_override_target, test_case_override_target
from tests.utils.local import prepare_plan, run_terraform_apply, execute_subprocess
from tests.utils.local import parse_key_value_file, read_file, read_yaml, read_json, write_file
from tests.utils.local import get_reconciled_tfvars

from tests.utils.local import ssm_tower, ssm_groundswell, ssm_seqerakit, ssm_wave_lite

from testcontainers.mysql import MySqlContainer


## ------------------------------------------------------------------------------------
## Tower Config File Checks
## ------------------------------------------------------------------------------------
# NOTE: To avoid creating VPC assets, use an existing VPC in the account the AWS provider is configured to use.

def generate_namespaced_dictionaries(dict: dict) -> tuple:

    """
    WARNING!!!!!!
      - Plan keys are in Python dictionary form, so JSON "true" becomes True.  AFFECTS: `outputs` and `vars`
      - Config file values are directly cracked from HCL so they are "true".
    """

    vars_dict = dict["variables"]
    outputs_dict = dict["planned_values"]["outputs"]

    with open('tests/datafiles/ssm_sensitive_values_tower_testing.json', 'r') as f:
        tower_secrets = json.load(f)

    with open('tests/datafiles/ssm_sensitive_values_groundswell_testing.json', 'r') as f:
        groundswell_secrets = json.load(f)

    with open('tests/datafiles/ssm_sensitive_values_seqerakit_testing.json', 'r') as f:
        seqerakit_secrets = json.load(f)

    with open('tests/datafiles/ssm_sensitive_values_wave_lite_testing.json', 'r') as f:
        wave_lite_secrets = json.load(f)
    

    # https://dev.to/taqkarim/extending-simplenamespace-for-nested-dictionaries-58e8
    # Avoids noisy dict notation ([""]) and constant repetition of `.value`.
    # Variables have only one key (values); outputs may have 3 keys (sensitive, type, value).
    # Example: `vars.tower_contact_email`
    vars_flattened = {k: v.get("value", v) for k,v in vars_dict.items()}
    outputs_flattened = {k: v.get("value", v) for k,v in outputs_dict.items()}

    tower_secrets_flattened = {k: v.get("value", v) for k,v in tower_secrets.items()}
    groundswell_secrets_flattened = {k: v.get("value", v) for k,v in groundswell_secrets.items()}
    seqerakit_secrets_flattened = {k: v.get("value", v) for k,v in seqerakit_secrets.items()}
    wave_lite_secrets_flattened = {k: v.get("value", v) for k,v in wave_lite_secrets.items()}
    
    # vars = json.loads(json.dumps(vars_flattened), object_hook=lambda item: SimpleNamespace(**item))
    # outputs = json.loads(json.dumps(outputs_flattened), object_hook=lambda item: SimpleNamespace(**item))
    # Only namespace the top level, preserve nested dictionaries as regular dicts
    # Problem is that nested values like data_studios_options show up like:
    # vscode-1-101-2-0-8-5=namespace(container='public.cr.seqera.io/platform/data-studio-vscode:1.101.2-0.8.5', icon='vscode', qualifier='VSCODE-1-101-2-0-8-5', status='recommended', tool='vscode')
    # and this breaks the 'terraform console' template submission
    vars = SimpleNamespace(**vars_flattened)
    outputs = SimpleNamespace(**outputs_flattened)

    tower_secrets_sn = SimpleNamespace(**tower_secrets_flattened)
    groundswell_secrets_sn = SimpleNamespace(**groundswell_secrets_flattened)
    seqerakit_secrets_sn = SimpleNamespace(**seqerakit_secrets_flattened)
    wave_lite_secrets_sn = SimpleNamespace(**wave_lite_secrets_flattened)

    # Group into two lists to make return disaggregation easier
    return ([vars, outputs, vars_dict, outputs_dict], 
            [tower_secrets_sn, groundswell_secrets_sn, seqerakit_secrets_sn, wave_lite_secrets_sn])


def test_poc(backup_tfvars, config_baseline_settings_default):
    """
    Trying to create files directly via Terraform console.
    """
    start_time = time.time()
    plan, secrets = generate_namespaced_dictionaries(config_baseline_settings_default)
    vars, outputs, vars_dict, _ = plan
    tower_secrets, groundswell_secrets, seqerakit_secrets, wave_lite_secrets = secrets

    # Transform template files into parseable JSON
    command = "./hcl2json 009_define_file_templates.tf > 009_define_file_templates.json"
    result = execute_subprocess(command)
    templatefile_json = read_json("009_define_file_templates.json")

    # This part a big magical, from Claude: Here's how it works:
    # 1. re.sub(pattern, replace_var, input_str) finds every occurrence of var.something
    # 2. For each match, it calls replace_var(match)
    # 3. replace_var extracts the variable name and returns the replacement value
    # 4. re.sub substitutes each match with the returned value
    # So for your input string, it will automatically find and replace var.app_name, var.flag_create_hosts_file_entry, and var.flag_do_not_use_https in a single call.
    import re

    def replace_vars_in_templatefile(input_str, vars_obj, type) -> str:
        """
        input_str : The value of a key extracted from JSONified 009_define_file_templates.tf
        vars_obj  : The SimpleNamespace object returned by generate_namespaced_dictionaries()
        type      : The prefix we are looking to replace.

        NOTE: This relies upon the emission of TF Locals values during testing via an extra outputs file definition
        (created by tests/datafiles/generate_core_data.sh)
        """

        def replace_var(match):
            try:
                var_name = match.group(1)
                if hasattr(vars_obj, var_name):
                    value = getattr(vars_obj, var_name)
                    if isinstance(value, str):
                        return f'"{value}"'
                    elif isinstance(value, bool):
                        return str(value).lower()
                    else:
                        return str(value)
            except IndexError:
                return match.group(0)  # Return original if var not found

        # The regex re.sub() function handles the "looping" automatically. Finds all matches of the defined pattern in the string 
        # and calls the replace_var function for each.
        if type == "module.connection_strings":
            pattern = r'module.connection_strings\.(\w+)'
            return re.sub(pattern, replace_var, input_str)

        elif type == "tower_secrets":
            pattern = r'local\.tower_secrets\["([^"]+)"\]\["[^"]+"\]'
            return re.sub(pattern, replace_var, input_str)
        
        elif type == "groundswell_secrets":
            pattern = r'local\.groundswell_secrets\["([^"]+)"\]\["[^"]+"\]'
            return re.sub(pattern, replace_var, input_str)
        
        elif type == "seqerakit_secrets":
            pattern = r'local\.seqerakit_secrets\["([^"]+)"\]\["[^"]+"\]'
            return re.sub(pattern, replace_var, input_str)
        
        elif type == "wave_lite_secrets":
            pattern = r'local\.wave_lite_secrets\["([^"]+)"\]\["[^"]+"\]'
            return re.sub(pattern, replace_var, input_str)
        
        # Keeping these in just-in-case they are ever needed in future
        elif type == "tfvar":
            pattern = r'var\.(\w+)'
            return re.sub(pattern, replace_var, input_str)
        
        elif type == "local":
            pattern = r'local\.(\w+)'
            return re.sub(pattern, replace_var, input_str)
        else:
            return "Error"
        
    def sub_templatefile_inputs(input_str):

        # BACKGROUND:
        # I'm sourcing the templatefile string directly from 009. A normal plan/apply would have all the input values availabe at execution.
        # This is slow, however, so I'm trying to use the much faster 'terraform console' approach. Console appears to have access to 'tfvars' 
        # and necessary 'locals', but not to the outputs of called modules (emitted file is "known after apply").
        #
        # To make this work, I need to run a 'terraform plan' (full) to generate all outputs (inclusive of module outputs), which can then 
        # be used for substitution in the templatefile string passed by 'terraform console'. This feels like a Rube Goldberg, but it gets 
        # test execution down from 30+ seconds (everytime) to ~4 seconds (first time, cacheable). 
        # 
        # TBD what happens with secrets
        # 
        # '\n' must be replace in  the extracted 009 payload so it can be passed to 'terraform console' via subprocess call.

        # Had to re-enable this for tower.sql but it breaks tower.env (the data_studio_options). Why?
        # result = replace_vars_in_templatefile(input_str, vars, "tfvar")
        # result = replace_vars_in_templatefile(result, outputs, "local")
        result = replace_vars_in_templatefile(input_str, outputs, "module.connection_strings")
        result = replace_vars_in_templatefile(result, tower_secrets, "tower_secrets")
        result = replace_vars_in_templatefile(result, groundswell_secrets, "groundswell_secrets")
        result = replace_vars_in_templatefile(result, seqerakit_secrets, "seqerakit_secrets")
        result = replace_vars_in_templatefile(result, wave_lite_secrets, "wave_lite_secrets")
        result = result.replace("\n", "")   # MUST REMOVE NEW LINES OR CONSOLE CALL BREAKS.
        # TODO: Figure out secrets

        return result
    
    def prepare_templatefile_payload(key, outputs):
        # The hcl2json conversion of 009 to JSON wraps the 'templatefile(...)' string we need with '${..}'.
        # The wrapper needs to be removed or else it breaks 'terraform console'.
        payload = templatefile_json["locals"][0][key]
        payload = payload[2:-1]
        payload = sub_templatefile_inputs(payload)
        return payload
    
    def write_populated_templatefile(outfile, payload):
        """
        Example of how this calls 'terraform console':
          > terraform console <<< 'templatefile("assets/src/ansible/06_run_seqerakit.yml.tpl", { app_name = "abc", flag_create_hosts_file_entry = false, flag_do_not_use_https = true })'
        
        'terraform console' command needs single quotes on outside and double-quotes within.
        """
        payload = subprocess.run(
            ["terraform", "console"],
            input=str(payload),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        output = payload.stdout

        # Strip '<<EOT' and 'EOT' appending to start and end of multi-line payload emitted by 'terraform console'.
        if output.startswith("<<EOT"):
            lines = output.splitlines()
            output = "\n".join(lines[1:-1])

        write_file(outfile, output)

    # TODO:
    #   1) Generate hash of tfvars variables and do cache check to speed this up.
    #   2) If cache miss, emit generated files as <CACHE_VALUE>_<FILENAME> and stick in 'tests/.templatfile_cache'.

    # NOTE:
    #  - Logic varies a bit on read due to kind of file (e.g. YAML vs KV vs SQL)

    # ansible_06_run_seqerakit
    result = prepare_templatefile_payload("ansible_06_run_seqerakit", outputs)
    outfile = "graham2.yml"
    write_populated_templatefile(outfile, result)
    content = read_yaml(outfile)
    print(content)

    # tower.env
    result = prepare_templatefile_payload("tower_env", outputs)
    outfile = "graham3.env"
    write_populated_templatefile(outfile, result)
    content = parse_key_value_file(outfile)
    print(content)

    # tower.sql
    result = prepare_templatefile_payload("tower_sql", outputs)
    outfile = "graham4.sql"
    write_populated_templatefile(outfile, result)
    content = read_file(outfile)
    print(content)

    # cleanse_and_configure
    result = prepare_templatefile_payload("cleanse_and_configure_host", outputs)
    outfile = "graham5.sh"
    write_populated_templatefile(outfile, result)
    content = read_file(outfile)
    print(content)

    end_time = time.time() - start_time
    print(f"{end_time=}")


    Path("009_define_file_templates.json").unlink(missing_ok=True)


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
def test_default_config_tower_env(backup_tfvars, config_baseline_settings_default):  # teardown_tf_state_all):
    """
    Test the target tower.env generated from default test terraform.tfvars and base-override.auto.tfvars.
    """

    # Given
    print("Testing tower.env generated from default settings.")

    # When
    vars, outputs, vars_dict, _ = generate_namespaced_dictionaries(config_baseline_settings_default)
    tower_env_file = parse_key_value_file(f"{root}/assets/target/tower_config/tower.env")
    keys = tower_env_file.keys()

    # ------------------------------------------------------------------------------------
    # Test tower.env - assert all core keys exist
    # ------------------------------------------------------------------------------------
    # TODO: Refactor this to be more compact / efficient
    entries = {
        "TOWER_ENABLE_AWS_SSM"        : "true",
        "LICENSE_SERVER_URL"          : "https://licenses.seqera.io",
        "TOWER_CONTACT_EMAIL"         : vars.tower_contact_email,
        "TOWER_ENABLE_PLATFORMS"      : vars.tower_enable_platforms,
        "TOWER_ROOT_USERS"            : vars.tower_root_users,
        "TOWER_DB_DRIVER"             : vars.tower_db_driver,
        "TOWER_DB_DIALECT"            : vars.tower_db_dialect,
        "TOWER_DB_MIN_POOL_SIZE"      : vars.tower_db_min_pool_size,  # str()
        "TOWER_DB_MAX_POOL_SIZE"      : vars.tower_db_max_pool_size,  # str()
        "TOWER_DB_MAX_LIFETIME"       : vars.tower_db_max_lifetime,   # str()

        "TOWER_SERVER_URL"            : outputs.tower_server_url,
        "TOWER_DB_URL"                : outputs.tower_db_url,
        "FLYWAY_LOCATIONS"            : vars.flyway_locations,
        "TOWER_REDIS_URL"             : outputs.tower_redis_url,
        "WAVE_SERVER_URL"             : outputs.tower_wave_url,
    }

    for k,v  in entries.items():
        assert tower_env_file[k] == str(v)

    # ------------------------------------------------------------------------------------
    # Test always-present conditionals
    # ------------------------------------------------------------------------------------
    entries = {
        "TOWER_ENABLE_AWS_SES"        : vars.flag_use_aws_ses_iam_integration,
        "TOWER_ENABLE_UNSAFE_MODE"    : vars.flag_do_not_use_https,
        "TOWER_ENABLE_WAVE"           : vars.flag_use_wave or vars.flag_use_wave_lite,
        "TOWER_ENABLE_GROUNDSWELL"    : vars.flag_enable_groundswell,
        "TOWER_DATA_EXPLORER_ENABLED" : vars.flag_data_explorer_enabled
    }

    for k,v in entries.items():
        assert tower_env_file[k] == ("true" if v else "false")

    # ------------------------------------------------------------------------------------
    # Test tower.env - assert some core keys NOT present
    # ------------------------------------------------------------------------------------
    entries = [
        "TOWER_DB_USER", "TOWER_DB_PASSWORD", "TOWER_SMTP_USER", "TOWER_SMTP_PASSWORD"
    ]

    for k in entries:
        assert k not in keys

    # ------------------------------------------------------------------------------------
    # Test sometimes-present conditionals
    # Entries are the key, value, and controlling condition
    # ------------------------------------------------------------------------------------
    entries = [
        ("TOWER_SMTP_HOST", 
                vars.tower_smtp_host, 
                vars.flag_use_existing_smtp
        ),
        ("TOWER_SMTP_PORT", 
                vars.tower_smtp_port, 
                vars.flag_use_existing_smtp
        ),
        ("GROUNDSWELL_SERVER_URL", 
                "http://groundswell:8090", 
                vars.flag_enable_groundswell
        ),
        ("TOWER_DATA_EXPLORER_CLOUD_DISABLED_WORKSPACES", 
                vars.data_explorer_disabled_workspaces, 
                vars.flag_data_explorer_enabled
        ),
        ("TOWER_DATA_STUDIO_ENABLE_PATH_ROUTING", 
                "false", 
                vars.flag_enable_data_studio and not vars.flag_studio_enable_path_routing
        ),
        ("TOWER_DATA_STUDIO_ALLOWED_WORKSPACES", 
                vars.data_studio_eligible_workspaces, 
                vars.flag_enable_data_studio and vars.flag_limit_data_studio_to_some_workspaces
        ),
        ("TOWER_DATA_STUDIO_CONNECT_URL", 
                outputs.tower_connect_server_url, 
                vars.flag_enable_data_studio
        ),
        ("TOWER_OIDC_PEM_PATH", 
                "/data-studios-rsa.pem", 
                vars.flag_enable_data_studio
        ),
        ("TOWER_OIDC_REGISTRATION_INITIAL_ACCESS_TOKEN", 
                "ipsemlorem", 
                vars.flag_enable_data_studio
        )
    ]

    for entry in entries:
        k,v,condition = entry
        if condition:
            assert tower_env_file[k] == v
        else:
            assert k not in keys


    # Data Studio Edgecase
    # Need to use original vars_dict because can't iterate through SimpleNamespace
    qualifiers = ["ICON", "REPOSITORY", "TOOL", "STATUS"]
    if vars.flag_enable_data_studio:
        for studio in vars_dict["data_studio_options"]["value"]:
            for qualifier in qualifiers:
                key = f"TOWER_DATA_STUDIO_TEMPLATES_{studio}_{qualifier}"
                # EDGECASE: Called it 'container' in terrafrom tfvars, but setting is REPOSITORY
                if qualifier == "REPOSITORY":
                    value = vars_dict["data_studio_options"]["value"][studio]["container"]
                else:
                    value = vars_dict["data_studio_options"]["value"][studio][qualifier.lower()]
                assert tower_env_file[key.upper()] == value


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
def test_default_config_tower_yml(backup_tfvars, config_baseline_settings_default):  # teardown_tf_state_all):
    """
    Test the target tower.yml generated from default test terraform.tfvars and base-override.auto.tfvars.
    """

    # Given
    print("Testing tower.yml generated from default settings.")

    # When
    vars, _, _, _ = generate_namespaced_dictionaries(config_baseline_settings_default)
    tower_yml_file = read_yaml(f"{root}/assets/target/tower_config/tower.yml")

    # ------------------------------------------------------------------------------------
    # Test tower.yml
    # ------------------------------------------------------------------------------------
    entries = {
        tower_yml_file["mail"]["smtp"]["auth"]                                  : vars.tower_smtp_auth,
        tower_yml_file["mail"]["smtp"]["starttls"]["enable"]                    : vars.tower_smtp_starttls_enable,
        tower_yml_file["mail"]["smtp"]["starttls"]["required"]                  : vars.tower_smtp_starttls_required,
        tower_yml_file["mail"]["smtp"]["ssl"]["protocols"]                      : vars.tower_smtp_ssl_protocols,
        tower_yml_file["micronaut"]["application"]["name"]                      : vars.app_name,
        tower_yml_file["tower"]["cron"]["audit-log"]["clean-up"]["time-offset"] : f"{vars.tower_audit_retention_days}d"
    }

    for k,v in entries.items():
        assert k == v

    # Edgecases
    if vars.flag_disable_email_login:
        assert "disable-email" in tower_yml_file["tower"]["auth"].keys()
    else:
        assert "auth" not in tower_yml_file["tower"].keys()

    if vars.flag_enable_data_studio and not vars.flag_limit_data_studio_to_some_workspaces:
        assert "allowed-workspaces" in tower_yml_file["tower"]["data-studio"].keys()
    else:
        assert "data-studio" not in tower_yml_file["tower"].keys()

    # Remove middle whitespace from vars since it seems to be stripped from the template interpolation.
    key = tower_yml_file["tower"]["trustedEmails"]
    tower_root_users = vars.tower_root_users.replace(" ", "")
    assert tower_root_users in key
    tower_email_trusted_orgs = vars.tower_email_trusted_orgs.replace(" ", "")
    assert tower_email_trusted_orgs in key
    tower_email_trusted_users = vars.tower_email_trusted_users.replace(" ", "")
    assert tower_email_trusted_users in key


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
def test_default_config_data_studios_env(backup_tfvars, config_baseline_settings_default):
    """
    Test the target data-studio.env generated from default test terraform.tfvars and base-override.auto.tfvars.
    """

    # Given
    print("Testing data-studio.env generated from default settings.")

    # When
    vars, outputs, _, _ = generate_namespaced_dictionaries(config_baseline_settings_default)
    ds_env_file = parse_key_value_file(f"{root}/assets/target/tower_config/data-studios.env")
    keys = ds_env_file.keys()

    # ------------------------------------------------------------------------------------
    # Test data-studios.env - assert all core keys exist
    # ------------------------------------------------------------------------------------
    entries = {
        "PLATFORM_URL"                              : f"https://{vars.tower_server_url}",
        "CONNECT_HTTP_PORT"                         : 9090,    # str()
        "CONNECT_TUNNEL_URL"                        : "connect-server:7070",
        "CONNECT_PROXY_URL"                         : f"https://connect.{vars.tower_server_url}",
        "CONNECT_REDIS_ADDRESS"                     : "redis:6379",
        "CONNECT_REDIS_DB"                          : 1,
        "CONNECT_OIDC_CLIENT_REGISTRATION_TOKEN"    : "ipsemlorem"
    }

    for k,v in entries.items():
        assert ds_env_file[k] == str(v)

    # ------------------------------------------------------------------------------------
    # Test always-present conditionals
    # ------------------------------------------------------------------------------------
    # TODO: Figure out how to use local.studio_uses_distroless for better targeting.
    if "CONNECT_LOG_LEVEL" in keys:
        assert "CONNECT_SERVER_LOG_LEVEL" not in keys
    
    if "CONNECT_SERVER_LOG_LEVEL":
        assert "CONNECT_LOG_LEVEL" in keys


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
def test_default_config_tower_sql(backup_tfvars, config_baseline_settings_default):
    """
    Test the target tower.sql generated from default test terraform.tfvars and base-override.auto.tfvars.
    """

    # Given
    vars, _, _, _ = generate_namespaced_dictionaries(config_baseline_settings_default)

    # Get values for comparison
    ssm_data = read_json(ssm_tower)
    sql_content = read_file(f"{root}/assets/target/tower_config/tower.sql")

    db_database_name = vars.db_database_name
    expected_user = ssm_data["TOWER_DB_USER"]["value"]
    expected_password = ssm_data["TOWER_DB_PASSWORD"]["value"]

    # ------------------------------------------------------------------------------------
    # Test tower.sql - validate all interpolated variables are properly replaced
    # ------------------------------------------------------------------------------------
    entries = [
        f"CREATE DATABASE {db_database_name};",
        f"ALTER DATABASE {db_database_name} CHARACTER SET utf8 COLLATE utf8_bin;",
        f'GRANT ALL PRIVILEGES ON {db_database_name}.* TO {expected_user}@"%";',
        f'CREATE USER "{expected_user}" IDENTIFIED BY "{expected_password}";'
    ]

    for entry in entries:
        assert entry in sql_content

    # Additional validation: ensure no template variables remain
    assert "${db_database_name}" not in sql_content
    assert "${db_tower_user}" not in sql_content
    assert "${db_tower_password}" not in sql_content


@pytest.mark.local
@pytest.mark.db
@pytest.mark.mysql_container
@pytest.mark.long
@pytest.mark.testcontainer
def test_tower_sql_mysql_container_execution(backup_tfvars, config_baseline_settings_default):
    """
    Test that tower.sql successfully populates a MySQL8 database using Testcontainers.
    This validates the SQL file can create the database, user, and grant permissions.

    NOTE:
    Container DB cant be connected to via master creds like standard RDS.
    Emulate by creating one user "test", then run the script that we'd normally run against RDS with the master user.
    Then try to log in with the "tower" user.

    Cant use `mysql_container.get_container_host_ip()` because it returns `localhost` and we need the host's actual IP.
    """

    # Given
    vars, _, _, _ = generate_namespaced_dictionaries(config_baseline_settings_default)
    ssm_data = read_json(ssm_tower)
    sql_content = read_file(f"{root}/assets/target/tower_config/tower.sql")

    # Note: Hack to emulate RDS master user / password.
    # TODO: Use the master user / password from the SSM values. WARNING: DONT CHANGE THESE OR TEST FAILS.
    mock_master_user = "root"
    mock_master_password = "test"
    mock_db_name = "test"

    tower_db_user = ssm_data["TOWER_DB_USER"]["value"]
    tower_db_password = ssm_data["TOWER_DB_PASSWORD"]["value"]
    tower_db_name = vars.db_database_name

    # When - Execute SQL against MySQL container
    with (
        MySqlContainer("mysql:8.0", root_password=mock_master_password)
        .with_env("MYSQL_USER", mock_master_user)
        .with_env("MYSQL_PASSWORD", mock_master_password)
        .with_env("MYSQL_DATABASE", mock_db_name)
        .with_bind_ports(3306, 3306)
    ) as mysql_container:
        # Create temporary SQL file for docker volume mount
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as temp_sql:
            temp_sql.write(sql_content)
            temp_sql_path = temp_sql.name

        try:
            # Emulate execution of RDS prepping script in Ansilble.
            # NOTE: Since we cant change the container master user from 'root', fudging login with another "master" user.
            #   This is a hack, but it serves its purpose given the constraints.
            docker_cmd = f"""
                docker run --rm -t -v {temp_sql_path}:/tower.sql \
                  -e MYSQL_PWD={mock_master_password} --entrypoint /bin/bash \
                  --add-host host.docker.internal:host-gateway mysql:8.0 \
                  -c 'mysql --host host.docker.internal --port=3306 --user={mock_master_user} < tower.sql'
            """
            result = subprocess.run(docker_cmd, shell=True, capture_output=True, text=True, timeout=60)
            assert result.returncode == 0

            # Then - Verify database operations using MySQL container commands
            def run_mysql_query(query, user=mock_master_user, password=mock_master_password, database=None):
                """Helper function to run MySQL queries using container commands"""

                # Create temporary SQL file for docker volume mount (avoids nested quotes nightmare)
                with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as query_sql:
                    query_sql.write(query)
                    query_sql_path = query_sql.name

                mysql_cmd = f"""
                    docker run --rm -t -v {query_sql_path}:/query.sql \
                      -e MYSQL_PWD={password} --entrypoint /bin/bash \
                      --add-host host.docker.internal:host-gateway mysql:8.0 \
                      -c 'mysql --host host.docker.internal --port=3306 --user={user} --silent --skip-column-names < query.sql'
                """
                result = subprocess.run(mysql_cmd, shell=True, capture_output=True, text=True, timeout=30)
                assert result.returncode == 0
                return result.stdout.strip()

            # Verify database creation
            db_result = run_mysql_query(f"SHOW DATABASES LIKE '{tower_db_name}';")
            assert db_result == tower_db_name

            # Verify user creation
            user_result = run_mysql_query(f"SELECT user FROM mysql.user WHERE user='{tower_db_user}';")
            assert user_result == tower_db_user

            # Verify user permissions
            grants_result = run_mysql_query(f"SHOW GRANTS FOR '{tower_db_user}'@'%';")
            assert "ALL PRIVILEGES" in grants_result
            assert f"`{tower_db_name}`" in grants_result

            # Verify connection with new user credentials by running a simple query
            test_result = run_mysql_query(
                "SELECT 1;", user=tower_db_user, password=tower_db_password, database=tower_db_name
            )
            assert test_result == "1"

        finally:
            # Clean up temporary SQL file
            if os.path.exists(temp_sql_path):
                os.unlink(temp_sql_path)


# ------------------------------------------------------------------------------------
# CUSTOM CONFIG TESTS
# ------------------------------------------------------------------------------------
@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
def test_custom_config_files_01(backup_tfvars, config_baseline_settings_custom_01):
    """
    Test the target tower.env generated from default test terraform.tfvars and base-override.auto.tfvars,
    PLUS custom overrides.

    - Data Studios active & Path routing active
    """

    # When
    tower_env_file = parse_key_value_file(f"{root}/assets/target/tower_config/tower.env")
    ds_env_file = parse_key_value_file(f"{root}/assets/target/tower_config/data-studios.env")


    # ------------------------------------------------------------------------------------
    # Test conditionals - Tower Env File And Data Studios Env file
    # ------------------------------------------------------------------------------------
    assert tower_env_file["TOWER_DATA_STUDIO_ENABLE_PATH_ROUTING"]  == "true"
    assert tower_env_file["TOWER_DATA_STUDIO_CONNECT_URL"]          == "https://connect-example.com"
    assert ds_env_file["CONNECT_PROXY_URL"]                         == "https://connect-example.com"


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
def test_custom_config_files_02(backup_tfvars, config_baseline_settings_custom_02):
    """
    Test the target tower.env generated from default test terraform.tfvars and base-override.auto.tfvars,
    PLUS custom overrides.

    - Data Studios active & Path routing inactive
    """

    # When
    tower_env_file = parse_key_value_file(f"{root}/assets/target/tower_config/tower.env")
    ds_env_file = parse_key_value_file(f"{root}/assets/target/tower_config/data-studios.env")


    # ------------------------------------------------------------------------------------
    # Test conditionals - Tower Env File And Data Studios Env file
    # ------------------------------------------------------------------------------------
    assert tower_env_file["TOWER_DATA_STUDIO_ENABLE_PATH_ROUTING"]  == "false"
    assert tower_env_file["TOWER_DATA_STUDIO_CONNECT_URL"]          == "https://connect.autodc.dev-seqera.net"
    assert ds_env_file["CONNECT_PROXY_URL"]                         == "https://connect.autodc.dev-seqera.net"


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
def test_custom_config_files_03(backup_tfvars, config_baseline_settings_custom_03):
    """
    Test the target tower.env generated from default test terraform.tfvars and base-override.auto.tfvars,
    PLUS custom overrides.

    - Data Studios inactive & Path routing inactive
    """

    # When
    tower_env_file = parse_key_value_file(f"{root}/assets/target/tower_config/tower.env")
    tower_env_file_keys = tower_env_file.keys()

    ds_env_file = parse_key_value_file(f"{root}/assets/target/tower_config/data-studios.env")
    ds_env_file_keys = ds_env_file.keys()


    # ------------------------------------------------------------------------------------
    # Test conditionals - Tower Env File And Data Studios Env file
    # ------------------------------------------------------------------------------------
    assert "TOWER_DATA_STUDIO_ENABLE_PATH_ROUTING" not in tower_env_file_keys
    assert "TOWER_DATA_STUDIO_CONNECT_URL" not in tower_env_file_keys

    assert "CONNECT_PROXY_URL" in ds_env_file_keys


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
def test_custom_config_docker_compose_with_reverse_proxy(backup_tfvars, config_baseline_settings_custom_docker_compose_reverse_proxy):
    """
    Test the target docker-compose.yml generated from default test terraform.tfvars and base-override.auto.tfvars,
    PLUS custom overrides.
    """

    # When
    # n/a

    dc_file = read_yaml(f"{root}/assets/target/docker_compose/docker-compose.yml")

    # ------------------------------------------------------------------------------------
    # Test data-studios.env - assert all core keys exist
    # ------------------------------------------------------------------------------------
    assert "reverseproxy" in dc_file["services"].keys()


@pytest.mark.local
@pytest.mark.config_keys
@pytest.mark.vpc_existing
@pytest.mark.long
def test_custom_config_docker_compose_with_no_https(backup_tfvars, config_baseline_settings_custom_docker_compose_no_https):
    """
    Test the target docker-compose.yml generated from default test terraform.tfvars and base-override.auto.tfvars,
    PLUS custom overrides.
    """

    # When
    # n/a

    dc_file = read_yaml(f"{root}/assets/target/docker_compose/docker-compose.yml")

    # ------------------------------------------------------------------------------------
    # Test data-studios.env - assert all core keys exist
    # ------------------------------------------------------------------------------------
    assert "reverseproxy" not in dc_file["services"].keys()
