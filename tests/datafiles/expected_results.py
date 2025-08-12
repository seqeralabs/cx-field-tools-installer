"""
Generate two sets of baseline value sets.
  1. Settings when all features / assets activated.
  2. Setting when all features / assets deactivated.

  Does not include edgecases like private CA reverseproxy.
"""

import ast
import json

## ------------------------------------------------------------------------------------
## MARK: Config - All Active
## ------------------------------------------------------------------------------------
def generate_tower_env_entries_all_active(overrides={}):
    baseline = {
        "present": {
            "TOWER_ENABLE_AWS_SSM"        : "true",
            "LICENSE_SERVER_URL"          : "https://licenses.seqera.io",
            "TOWER_SERVER_URL"            : "https://autodc.dev-seqera.net",
            "TOWER_CONTACT_EMAIL"         : "graham.wright@seqera.io",
            "TOWER_ENABLE_PLATFORMS"      : "awsbatch-platform,slurm-platform",
            "TOWER_ROOT_USERS"            : "graham.wright@seqera.io,gwright99@hotmail.com",
            "TOWER_DB_URL"                : "jdbc:mysql://db:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true",
            "TOWER_DB_DRIVER"             : "org.mariadb.jdbc.Driver",
            "TOWER_DB_DIALECT"            : "io.seqera.util.MySQL55DialectCollateBin",
            "TOWER_DB_MIN_POOL_SIZE"      : 5,
            "TOWER_DB_MAX_POOL_SIZE"      : 10,
            "TOWER_DB_MAX_LIFETIME"       : 18000000,
            "FLYWAY_LOCATIONS"            : "classpath:db-schema/mysql",
            "TOWER_REDIS_URL"             : "redis://redis:6379",
            "TOWER_ENABLE_UNSAFE_MODE"    : "false",
            # OIDC
            # MAIL
            "TOWER_ENABLE_AWS_SES"        : "true",
            # WAVE
            "TOWER_ENABLE_WAVE"           : "true",
            "WAVE_SERVER_URL"             : "https://wave.autodc.dev-seqera.net",
            # GROUNDSWELL
            "TOWER_ENABLE_GROUNDSWELL"  : "true",
            "GROUNDSWELL_SERVER_URL"    : "http://groundswell:8090",
            # DATA_EXPLORER
            "TOWER_DATA_EXPLORER_ENABLED"                   : "true",
            "TOWER_DATA_EXPLORER_CLOUD_DISABLED_WORKSPACES" : "",
            # DATA_STUDIOS
            "TOWER_DATA_STUDIO_ENABLE_PATH_ROUTING"         : "false",
            "TOWER_DATA_STUDIO_CONNECT_URL"                 : "https://connect.autodc.dev-seqera.net",
            "TOWER_OIDC_PEM_PATH"                           : "/data-studios-rsa.pem",
            "TOWER_OIDC_REGISTRATION_INITIAL_ACCESS_TOKEN"  : "ipsemlorem",

            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-0_ICON"          : "jupyter",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-0_REPOSITORY"    : "public.cr.seqera.io/platform/data-studio-jupyter:4.2.5-0.8.0",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-0_TOOL"          : "jupyter",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-0_STATUS"        : "deprecated",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-5_ICON"          : "jupyter",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-5_REPOSITORY"    : "public.cr.seqera.io/platform/data-studio-jupyter:4.2.5-0.8.5",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-5_TOOL"          : "jupyter",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-5_STATUS"        : "recommended",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-8-5_ICON"         : "rstudio",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-8-5_REPOSITORY"   : "public.cr.seqera.io/platform/data-studio-ride:2025.04.1-0.8.5",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-8-5_TOOL"         : "rstudio",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-8-5_STATUS"       : "recommended",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-8-5_ICON"         : "vscode",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-8-5_REPOSITORY"   : "public.cr.seqera.io/platform/data-studio-vscode:1.101.2-0.8.5",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-8-5_TOOL"         : "vscode",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-8-5_STATUS"       : "recommended",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-83-0-0-8-0_ICON"          : "vscode",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-83-0-0-8-0_REPOSITORY"    : "public.cr.seqera.io/platform/data-studio-vscode:1.83.0-0.8.0",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-83-0-0-8-0_TOOL"          : "vscode",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-83-0-0-8-0_STATUS"        : "deprecated",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R0-0-8-0_ICON"            : "xpra",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R0-0-8-0_REPOSITORY"      : "public.cr.seqera.io/platform/data-studio-xpra:6.0-r0-1-0.8.0",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R0-0-8-0_TOOL"            : "xpra",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R0-0-8-0_STATUS"          : "recommended",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R2-1-0-8-5_ICON"          : "xpra",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R2-1-0-8-5_REPOSITORY"    : "public.cr.seqera.io/platform/data-studio-xpra:6.2.0-r2-1-0.8.5",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R2-1-0-8-5_TOOL"          : "xpra",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R2-1-0-8-5_STATUS"        : "recommended",
            "# TOWER_DATA_STUDIO_ALLOWED_WORKSPACES"                        : "DO_NOT_UNCOMMENT",
        },
        "omitted": {
            # DB                      Never generated in file
            "TOWER_DB_USER"             : "",
            "TOWER_DB_PASSWORD"         : "",
            # OIDC
            # MAIL                    Not present if SES active
            "TOWER_SMTP_USER"           : "",
            "TOWER_SMTP_PASSWORD"       : "",
            "TOWER_SMTP_HOST"           : "",
            "TOWER_SMTP_PORT"           : "",
            # WAVE
            # GROUNDSWELL
            # DATA_EXPLORER
            # DATA_STUDIOS
            "# STUDIOS_NOT_ENABLED"     : "DO_NOT_UNCOMMENT",
        }
    }
    baseline = purge_baseline_of_specified_overrides(baseline, overrides)
    return {**baseline, **overrides}


def generate_tower_yml_entries_all_active(overrides={}):
    baseline = {
        # PROBLEM - Leftside will resolve to True multiple times. Earlier keys overwritten by later keys.
        "present": {
            'mail.smtp.auth'                                : True,
            'mail.smtp.starttls.enable'                     : True,
            'mail.smtp.starttls.required'                   : True,
            'mail.smtp.ssl.protocols'                       : "TLSv1.2",
            'micronaut.application.name'                    : "tower-testing",
            'tower.cron.audit-log.clean-up.time-offset'     : "1095d",
            'tower.data-studio.allowed-workspaces'          : None,
            'tower.trustedEmails[0]'                        : "'graham.wright@seqera.io,gwright99@hotmail.com'",
            'tower.trustedEmails[1]'                        : "'*@abc.com,*@def.com'",
            'tower.trustedEmails[2]'                        : "'123@abc.com,456@def.com'",
        },
        "omitted": {  # GET RID OF KEYS
            "tower.auth"                                    : 'N/A',
        }
    }
    baseline = purge_baseline_of_specified_overrides(baseline, overrides)
    return {**baseline, **overrides}


def generate_data_studios_env_entries_all_active(overrides={}):
    baseline = {
        "present": {
            "PLATFORM_URL"                              : f"https://autodc.dev-seqera.net",
            "CONNECT_HTTP_PORT"                         : 9090,    # str()
            "CONNECT_TUNNEL_URL"                        : "connect-server:7070",
            "CONNECT_PROXY_URL"                         : f"https://connect.autodc.dev-seqera.net",
            "CONNECT_REDIS_ADDRESS"                     : "redis:6379",
            "CONNECT_REDIS_DB"                          : 1,
            "CONNECT_OIDC_CLIENT_REGISTRATION_TOKEN"    : "ipsemlorem"
        },
        "omitted": {
            "# STUDIOS_NOT_ENABLED"                     : "DO_NOT_UNCOMMENT",
        }
    }
    baseline = purge_baseline_of_specified_overrides(baseline, overrides)
    return {**baseline, **overrides}


def generate_tower_sql_entries_all_active(overrides={}):
    # I know it's a bit dumb to have kv pairs here since we only care about keys buuut ... it helps consistency.
    baseline = {
        "present": {
            f"""CREATE DATABASE tower;"""                                               : "n/a",
            f"""ALTER DATABASE tower CHARACTER SET utf8 COLLATE utf8_bin;"""            : "n/a",
            f"""CREATE USER "tower_test_user" IDENTIFIED BY "tower_test_password";"""   : "n/a",
            f"""GRANT ALL PRIVILEGES ON tower.* TO tower_test_user@"%";"""              : "n/a"
        },
        "omitted": {}
    }
    baseline = purge_baseline_of_specified_overrides(baseline, overrides)
    return {**baseline, **overrides}


def generate_docker_compose_yml_entries_all_active(overrides={}):
    # I know it's a bit dumb to have kv pairs here since we only care about keys buuut ... it helps consistency.
    baseline = {
        "present": {},
        "omitted": {
            "services.reverseproxy"  : 'reverseproxy'
        }
    }
    baseline = purge_baseline_of_specified_overrides(baseline, overrides)
    return {**baseline, **overrides}


def generate_baseline_entries_all_active(template_files, overrides):

    entries = {
        "tower_env"         : generate_tower_env_entries_all_active(overrides["tower_env"]),
        "tower_yml"         : generate_tower_yml_entries_all_active(overrides["tower_yml"]),
        "data_studios_env"  : generate_data_studios_env_entries_all_active(overrides["data_studios_env"]),
        "tower_sql"         : generate_tower_sql_entries_all_active(overrides["tower_sql"]),
        "docker_compose"    : generate_docker_compose_yml_entries_all_active( overrides["docker_compose"]),

    }
    return entries


## ------------------------------------------------------------------------------------
## MARK: Config - All Disabled
## ------------------------------------------------------------------------------------
def generate_tower_env_entries_all_disabled(overrides={}):
    baseline = {
        "present": {
            "TOWER_ENABLE_AWS_SSM"        : "true",
            "LICENSE_SERVER_URL"          : "https://licenses.seqera.io",
            "TOWER_SERVER_URL"            : "https://autodc.dev-seqera.net",
            "TOWER_CONTACT_EMAIL"         : "graham.wright@seqera.io",
            "TOWER_ENABLE_PLATFORMS"      : "awsbatch-platform,slurm-platform",
            "TOWER_ROOT_USERS"            : "graham.wright@seqera.io,gwright99@hotmail.com",
            "TOWER_DB_URL"                : "jdbc:mysql://db:3306/tower?allowPublicKeyRetrieval=true&useSSL=false&permitMysqlScheme=true",
            "TOWER_DB_DRIVER"             : "org.mariadb.jdbc.Driver",
            "TOWER_DB_DIALECT"            : "io.seqera.util.MySQL55DialectCollateBin",
            "TOWER_DB_MIN_POOL_SIZE"      : 5,
            "TOWER_DB_MAX_POOL_SIZE"      : 10,
            "TOWER_DB_MAX_LIFETIME"       : 18000000,
            "FLYWAY_LOCATIONS"            : "classpath:db-schema/mysql",
            "TOWER_REDIS_URL"             : "redis://redis:6379",
            "TOWER_ENABLE_UNSAFE_MODE"    : "false",
            # OIDC
            # MAIL
            "TOWER_ENABLE_AWS_SES"        : "false",
            "TOWER_SMTP_HOST"             : "email-smtp.us-east-1.amazonaws.com",
            "TOWER_SMTP_PORT"             : "587",
            # WAVE
            "TOWER_ENABLE_WAVE"           : "false",
            "WAVE_SERVER_URL"             : "N/A",
            # GROUNDSWELL
            "TOWER_ENABLE_GROUNDSWELL"    : "false",
            # DATA_EXPLORER
            "TOWER_DATA_EXPLORER_ENABLED" : "false",
            # DATA_STUDIOS
            "# STUDIOS_NOT_ENABLED"       : "DO_NOT_UNCOMMENT",
        },
        "omitted": {
            # DB                      Never generated in file
            "TOWER_DB_USER"               : "",
            "TOWER_DB_PASSWORD"           : "",
            # OIDC
            # MAIL                    Not present if SES active
            "TOWER_SMTP_USER"             : "",
            "TOWER_SMTP_PASSWORD"         : "",
            # GROUNDSWELL
            "GROUNDSWELL_SERVER_URL"      : "http://groundswell:8090",
            # DATA_EXPLORER
            "TOWER_DATA_EXPLORER_CLOUD_DISABLED_WORKSPACES" : "",
            # WAVE
            # GROUNDSWELL
            # DATA_EXPLORER
            # DATA_STUDIOS
            "TOWER_DATA_STUDIO_ENABLE_PATH_ROUTING"         : "",
            "TOWER_DATA_STUDIO_CONNECT_URL"                 : "",
            "TOWER_OIDC_PEM_PATH"                           : "",
            "TOWER_OIDC_REGISTRATION_INITIAL_ACCESS_TOKEN"  : "",

            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-0_ICON"          : "",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-0_REPOSITORY"    : "",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-0_TOOL"          : "",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-0_STATUS"        : "",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-5_ICON"          : "",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-5_REPOSITORY"    : "",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-5_TOOL"          : "",
            "TOWER_DATA_STUDIO_TEMPLATES_JUPYTER-4-2-5-0-8-5_STATUS"        : "",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-8-5_ICON"         : "",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-8-5_REPOSITORY"   : "",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-8-5_TOOL"         : "",
            "TOWER_DATA_STUDIO_TEMPLATES_RIDE-2025-04-1-0-8-5_STATUS"       : "",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-8-5_ICON"         : "",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-8-5_REPOSITORY"   : "",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-8-5_TOOL"         : "",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-101-2-0-8-5_STATUS"       : "",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-83-0-0-8-0_ICON"          : "",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-83-0-0-8-0_REPOSITORY"    : "",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-83-0-0-8-0_TOOL"          : "",
            "TOWER_DATA_STUDIO_TEMPLATES_VSCODE-1-83-0-0-8-0_STATUS"        : "",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R0-0-8-0_ICON"            : "",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R0-0-8-0_REPOSITORY"      : "",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R0-0-8-0_TOOL"            : "",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R0-0-8-0_STATUS"          : "",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R2-1-0-8-5_ICON"          : "",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R2-1-0-8-5_REPOSITORY"    : "",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R2-1-0-8-5_TOOL"          : "",
            "TOWER_DATA_STUDIO_TEMPLATES_XPRA-6-0-R2-1-0-8-5_STATUS"        : "",
            "# TOWER_DATA_STUDIO_ALLOWED_WORKSPACES"                        : ""
        }
    }
    baseline = purge_baseline_of_specified_overrides(baseline, overrides)
    return {**baseline, **overrides}


def generate_tower_yml_entries_all_disabled(overrides={}):
    baseline = {
        # PROBLEM - Leftside will resolve to True multiple times. Earlier keys overwritten by later keys.
        "present": {
            'mail.smtp.auth'                                : True,
            'mail.smtp.starttls.enable'                     : True,
            'mail.smtp.starttls.required'                   : True,
            'mail.smtp.ssl.protocols'                       : "TLSv1.2",
            'micronaut.application.name'                    : "tower-testing",
            'tower.cron.audit-log.clean-up.time-offset'     : "1095d",
            'tower.trustedEmails[0]'                        : "'graham.wright@seqera.io,gwright99@hotmail.com'",
            'tower.trustedEmails[1]'                        : "'*@abc.com,*@def.com'",
            'tower.trustedEmails[2]'                        : "'123@abc.com,456@def.com'",
        },
        "omitted": {  # GET RID OF KEYS
            "tower.auth"                                    : '',
            'tower.data-studio'                             : '',
        }
    }
    baseline = purge_baseline_of_specified_overrides(baseline, overrides)
    return {**baseline, **overrides}


def generate_data_studios_env_entries_all_disabled(overrides={}):
    baseline = {
        "present": {
            "# STUDIOS_NOT_ENABLED"                     : "DO_NOT_UNCOMMENT",
        },
        "omitted": {
            "PLATFORM_URL"                              : "",
            "CONNECT_HTTP_PORT"                         : "",
            "CONNECT_TUNNEL_URL"                        : "",
            "CONNECT_PROXY_URL"                         : "",
            "CONNECT_REDIS_ADDRESS"                     : "",
            "CONNECT_REDIS_DB"                          : "",
            "CONNECT_OIDC_CLIENT_REGISTRATION_TOKEN"    : "",
        }
    }
    baseline = purge_baseline_of_specified_overrides(baseline, overrides)
    return {**baseline, **overrides}


def generate_tower_sql_entries_all_disabled(overrides={}):
    # I know it's a bit dumb to have kv pairs here since we only care about keys buuut ... it helps consistency.
    baseline = {
        "present": {
            f"""CREATE DATABASE tower;"""                                               : "n/a",
            f"""ALTER DATABASE tower CHARACTER SET utf8 COLLATE utf8_bin;"""            : "n/a",
            f"""CREATE USER "tower_test_user" IDENTIFIED BY "tower_test_password";"""   : "n/a",
            f"""GRANT ALL PRIVILEGES ON tower.* TO tower_test_user@"%";"""              : "n/a"
        },
        "omitted": {}
    }
    baseline = purge_baseline_of_specified_overrides(baseline, overrides)
    return {**baseline, **overrides}


def generate_docker_compose_yml_entries_all_disabled(overrides={}):
    # I know it's a bit dumb to have kv pairs here since we only care about keys buuut ... it helps consistency.
    baseline = {
        "present": {},
        "omitted": {
            "services.reverseproxy"  : '',
        }
    }
    baseline = purge_baseline_of_specified_overrides(baseline, overrides)
    return {**baseline, **overrides}


def generate_baseline_entries_all_disabled(template_files, overrides):

    entries = {
        "tower_env"         : generate_tower_env_entries_all_disabled(overrides["tower_env"]),
        "tower_yml"         : generate_tower_yml_entries_all_disabled(overrides["tower_yml"]),
        "data_studios_env"  : generate_data_studios_env_entries_all_disabled(overrides["data_studios_env"]),
        "tower_sql"         : generate_tower_sql_entries_all_disabled(overrides["tower_sql"]),
        "docker_compose"    : generate_docker_compose_yml_entries_all_disabled( overrides["docker_compose"]),

    }
    return entries

## ------------------------------------------------------------------------------------
## MARK: Helpers - Purge overrides
## ------------------------------------------------------------------------------------
def purge_baseline_of_specified_overrides(baseline, overrides):
    """Overrides could be inverse of baseline. Purge baseline of matches so subsequent merge is clean."""
    print(f"{overrides=}")
    if len(overrides.keys()) > 0:
        for key in overrides["present"].keys():
            try:
                baseline["omitted"].pop(key)
            except KeyError:
                pass

        for key in overrides["omitted"].keys():
            try:
                baseline["present"].pop(key)
            except KeyError:
                pass

    return baseline
