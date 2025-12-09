#!/usr/bin/env python3

import re
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import List

import yaml

base_import_dir = Path(__file__).resolve().parents[2]
if base_import_dir not in sys.path:
    sys.path.append(str(base_import_dir))

from installer.utils.extractors import tf_vars_json_payload
from installer.utils.logger import logger
from installer.utils.subnets import get_all_subnets

sys.tracebacklimit = 0
# -------------------------------------------------------------------------------
# NOTES:
# -------------------------------------------------------------------------------
#  1. See comments in utils/helpers.py for reasons why we created our own hacky tfvars parser.


# -------------------------------------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------------------------------------
def log_error_and_exit(message: str):
    logger.error(message)
    exit(1)


def only_one_true_set(flags: List) -> None:
    """Ensure only 1 entry per flag grouping is `true`. Aggregate values of all specified values and then count."""
    values = [flag for flag in flags]
    if values.count(True) != 1:
        log_error_and_exit(f"Only one of these flags may be true: {str(flags)}.")


def subnet_privacy(tfvars_subnets: List, vpc_subnets: List, qualifier: str) -> None:
    """Compare VPC subnets privacy vs CIDRs defined in tfvars for various components."""
    try:
        assert set(tfvars_subnets).issubset(set(vpc_subnets))
    except AssertionError:
        log_error_and_exit(qualifier)


def ensure_dependency_populated(flag: bool, child: str, qualifier: str) -> None:
    """If a flag is set, ensure dependent keys also set."""

    if flag:
        try:
            assert "REPLACE_ME" not in child, f"[ERROR]: {qualifier}"
            logger.debug(f"[OK]: {qualifier}")
        except AssertionError:
            log_error_and_exit(qualifier)
    else:
        logger.debug(f"[SKIP]: {qualifier}")


# -------------------------------------------------------------------------------
# GROUPING FUNCTIONS
# -------------------------------------------------------------------------------
def verify_only_one_true_set(data: SimpleNamespace):
    """Check that related config blocks only have 1 true and * false."""
    only_one_true_set([data.flag_create_new_vpc, data.flag_use_existing_vpc])
    only_one_true_set(
        [
            data.flag_create_external_db,
            data.flag_use_existing_external_db,
            data.flag_use_container_db,
        ]
    )
    only_one_true_set([data.flag_create_external_redis, data.flag_use_container_redis])
    only_one_true_set(
        [
            data.flag_create_load_balancer,
            data.flag_use_private_cacert,
            data.flag_do_not_use_https,
        ]
    )
    only_one_true_set([data.flag_use_aws_ses_iam_integration, data.flag_use_existing_smtp])


def verify_sensitive_keys(data: SimpleNamespace, data_dictionary: dict):
    """Check that sensitive keys are not defined in tfvars file."""
    sensitive_keys = [
        "db_root_user",
        "db_root_password",
        "tower_db_user",
        "tower_db_password",
        "tower_redis_password",
        "tower_jwt_secret",
        "tower_crypto_secretkey",
        "tower_license",
        "tower_smtp_user",
        "tower_smtp_password",
        "swell_db_user",
        "swell_db_password",
    ]

    data_keys = data_dictionary.keys()
    for key in sensitive_keys:
        if key in data_keys:
            log_error_and_exit(f" Do not specify `{key}`. This value will be sourced from SSM.")


def verify_tfvars_config_dependencies(data: SimpleNamespace):
    """Ensure dependent keys are a populated if a flag is active."""
    # VPC Dependency checks
    ensure_dependency_populated(
        data.flag_use_existing_vpc,
        data.vpc_existing_id,
        "`vpc_existing_id` value is missing.",
    )
    ensure_dependency_populated(
        data.flag_create_load_balancer,
        data.alb_certificate_arn,
        "`alb_certificate_arn` value is missing.",
    )

    # DNS dependency checks
    ensure_dependency_populated(
        data.flag_create_route53_private_zone,
        data.new_route53_private_zone_name,
        "`new_route53_private_zone_name` value is missing.",
    )
    ensure_dependency_populated(
        data.flag_use_existing_route53_public_zone,
        data.existing_route53_public_zone_name,
        "`existing_route53_public_zone_name` value is missing.",
    )
    ensure_dependency_populated(
        data.flag_use_existing_route53_private_zone,
        data.existing_route53_private_zone_name,
        "`existing_route53_private_zone_name` value is missing.",
    )


def verify_tower_server_url(data: SimpleNamespace):
    """Verify the tower server url is correctly configured."""

    if data.tower_server_url.startswith("http"):
        log_error_and_exit("Field `tower_server_url` must not have a prefix.")

    if data.tower_server_port != "8000":
        logger.warning(
            "Tower instance not using default port (8000). Ensure Docker-Compose file is updated accordingly."
        )


def verify_tower_root_users(data: SimpleNamespace):
    """Ensure at least one root user is specified."""
    if data.tower_root_users in ["REPLACE_ME", ""]:
        log_error_and_exit("Please populate `tower_root_user` with at least one email address.")


def verify_tower_self_signed_certs(data: SimpleNamespace):
    """Check self-signed certificate settings (if necessary)."""
    if data.flag_use_private_cacert:
        if not data.private_cacert_bucket_prefix.startswith("s3://"):
            log_error_and_exit(" Field `private_cacert_bucket_prefix` must start with `s3://`")


def verify_tower_groundswell(data: SimpleNamespace):
    """Check Groundwell validity."""
    if data.flag_enable_groundswell:
        if data.tower_container_version < "v23.3.0":
            log_error_and_exit(" Groundswell is only available in Tower 23.3.0+")


def verify_docker_daemon_loggin(data: SimpleNamespace):
    """Check Docker Daemon logging configuration."""
    logging_flags = [
        data.flag_docker_logging_local,
        data.flag_docker_logging_journald,
        data.flag_docker_logging_jsonfile,
    ]
    trues = [bool(i) for i in logging_flags]
    if trues.count(True) != 1:
        log_error_and_exit("Choose one and only one docker logging flag to be true.")


def verify_email_login_disablement(data: SimpleNamespace):
    """Check email login disablement scenarios."""
    if data.flag_disable_email_login:
        if data.tower_container_version < "v23.4.5":
            log_error_and_exit(" You cannot disable email login in versions earlier than 23.4.5")

        oidc_flags = [
            data.flag_oidc_use_generic,
            data.flag_oidc_use_google,
            data.flag_oidc_use_github,
        ]
        if not any(oidc_flags):
            log_error_and_exit(" Email login cannot be disabled if you dont have an OIDC alternative configured.")

        if data.flag_run_seqerakit:
            logger.warning("Seqerakit step cannot execute if email login is not active.")


def verify_subnet_privacy(data: SimpleNamespace):
    """Check that the assigned subnets in tfvars match the intended privacy of the Tower instance."""
    logger.info("Retrieving subnet information from AWS Account.")
    public_subnets, private_subnets = get_all_subnets("aws")

    # TO DO: Reduce verbosity by creating a `partial`-type function to make `data.vpc_new_ec2_subnets` DRY.
    if data.flag_create_new_vpc:
        if data.flag_make_instance_public:
            subnet_privacy(
                data.vpc_new_ec2_subnets,
                public_subnets,
                "`vpc_new_ec2_subnets` must contain public subnets.",
            )
        else:
            subnet_privacy(
                data.vpc_new_ec2_subnets,
                private_subnets,
                "`vpc_new_ec2_subnets` must contain private subnets.",
            )

    if data.flag_use_existing_vpc:
        if data.flag_make_instance_public:
            subnet_privacy(
                data.vpc_existing_ec2_subnets,
                public_subnets,
                "`vpc_existing_ec2_subnets` must contain public subnets.",
            )
        else:
            subnet_privacy(
                data.vpc_existing_ec2_subnets,
                private_subnets,
                "`vpc_existing_ec2_subnets` must contain private subnets.",
            )

    # Check that the assigned ALB subnets in tfvars match the intended privacy of the Tower instance.
    if data.flag_create_load_balancer:
        if data.flag_create_new_vpc:
            subnet_privacy(
                data.vpc_new_alb_subnets,
                public_subnets,
                "`vpc_new_alb_subnets` must contain public subnets.",
            )
        else:
            # subnet_privacy(
            #     data.vpc_existing_alb_subnets,
            #     public_subnets,
            #     "`vpc_existing_alb_subnets` must contain public subnets.",
            # )
            pass

    if data.flag_make_instance_private:
        logger.warning(
            "`flag_make_instance_private` is active; please note that assets in other VPCs will be unlikely to access your Tower instance."
        )


def verify_ses_integration(data: SimpleNamespace):
    """Check SES integration settings."""

    if data.flag_use_aws_ses_iam_integration:
        if data.tower_container_version < "v23.2.0":
            log_error_and_exit("SES IAM integration requires Tower 23.2.0+.")

        if "amazonaws.com" not in data.tower_smtp_host:
            log_error_and_exit("SES integration requires SES SMTP endpoint.")

        if data.tower_smtp_port != "587":
            log_error_and_exit("SES integration requires port 587. Please fix.")


def verify_route53_integration(data: SimpleNamespace):
    """Check DNS settings."""

    # Catching multiple checks with same `except` since message is the same.
    try:
        if data.flag_create_route53_private_zone:
            assert data.new_route53_private_zone_name in data.tower_server_url

        if data.flag_use_existing_route53_public_zone:
            assert data.existing_route53_public_zone_name in data.tower_server_url

        if data.flag_use_existing_route53_private_zone:
            assert data.existing_route53_private_zone_name in data.tower_server_url

    except AssertionError:
        log_error_and_exit("`tower_server_url` does not match DNS zone.")


def verify_ingress_and_egress(data: SimpleNamespace, data_dictionary: dict):
    """Issue reminders if ingress/egress rules seem overly loose."""

    if data.sg_ingress_cidrs == "0.0.0.0/0":
        logger.warning("`sg_ingress_cidrs` is completely open (HTTPs) . Consider tightening.")

    if data.sg_ssh_cidrs == "0.0.0.0/0":
        logger.warning("`sg_ssh_cidrs` ingress is completly open (SSH). Consider tightening.")

    # Forgoing `data...` approeach beause I'm too dumb to figure out how to get a variable name as a string.
    egress_sgs = [
        "sg_egress_eice",
        "sg_egress_tower_ec2",
        "sg_egress_tower_alb",
        "sg_egress_batch_ec2",
        "sg_egress_interface_endpoint",
    ]
    for sg in egress_sgs:
        if data_dictionary[sg] == ["all-all"]:
            logger.warning(f"`{sg}` allows egress everywhere. Consider tightening.")


def verify_flow_logs(data: SimpleNamespace):
    """Issue reminder about Flow logs cost."""
    if (data.flag_create_new_vpc) and (data.enable_vpc_flow_logs):
        logger.warning("You have VPC Flow Logs activated. This will generate extra costs.")


def verify_ami_update_behaviour(data: SimpleNamespace):
    """Check AMI update logic."""
    if data.ec2_update_ami_if_available:
        logger.info(
            "Your EC2 AMI will update as newer images are available. This means your VM will occasionally be destroyed and recreated."
        )

        if data.flag_use_container_db:
            logger.warning(
                "Your docker db container will destroyed when you EC2 AMI is updated. Ensure this fits your intention."
            )


def verify_database_configuration(data: SimpleNamespace):
    """Verify / Warn about various database configuration items."""

    if (data.db_engine == "mysql") and ("8" in data.db_engine_version):
        logger.warning("MySQL 8 may need TOWER_DB_URL connection string modifiers.")

    if (data.tower_db_url.startswith("jdbc:")) or (data.tower_db_url.startswith("mysql:")):
        log_error_and_exit("Do not include protocol in `tower_db_url`. Start with hostname.")

    if data.tower_db_driver != "org.mariadb.jdbc.Driver":
        log_error_and_exit("Field `tower_db_driver` must be `org.mariadb.jdbc.Driver`.")

    if data.tower_db_dialect != "io.seqera.util.MySQL55DialectCollateBin":
        log_error_and_exit("Field `tower_db_dialect` must be `org.mariadb.jdbc.Driver`.")

    if data.flag_use_container_db:
        if data.tower_db_url != "db:3306":
            logger.warning(
                "You are using a non-standard db container name or port. Ensure Docker-Compose config is updated accordingly."
            )

    if data.flag_use_existing_external_db:
        logger.warning(
            "You are using a pre-existing external database. Please ensure you create the database, user, and append the database name to `tower_db_url`."
        )

    if data.db_deletion_protection:
        logger.info(
            "You have Deletion Protection enabled for your external DB. This will affect easy teardown during testing."
        )
    elif not data.db_deletion_protection:
        logger.warning(
            "You have not enabled Deletion Protection on your external DB. This is HIGHLY recommended for Production instances. If you want this, set `db_deletion_protection` to true."
        )

    if data.skip_final_snapshot:
        logger.warning(
            "You have disabled a final snapshot of your external DB. Enablement of this feature is recommended for Production."
        )
    elif not data.skip_final_snapshot:
        logger.warning(
            "You have enabled a final snapshot on your external DB. This will affect easy teardwon during testing."
        )

    if data.flag_use_container_db and data.tower_db_url != "db:3306":
        logger.warning(
            f"You are using a non-standard DNS entry for your container db. Please verify if `tower_db_url` should really be '{data.tower_db_url}'."
        )

    if data.flag_use_existing_external_db and data.tower_db_url == "db:3306":
        log_error_and_exit(
            "You are using the container db DNS for your external RDS instance. Please change `tower_db_url`."
        )


def verify_docker_version(data: SimpleNamespace):
    """Make sure MySQL 5.6 is not present"""
    yaml.sort_base_mapping_type_on_output = False

    with open("assets/src/docker_compose/docker-compose.yml.tpl") as file:
        # PYYAML fails with `yaml.scanner.ScannerError` due to Terraform templating. Switching to less elegant alternative.
        # dcfile = yaml.safe_load(file)
        # image = dcfile['services']['db']['image']
        lines = file.readlines()

        for line in lines:
            if "mysql:5.6" in line:
                log_error_and_exit(
                    "MySQL 5.6 is obsolete. Please chooses MySQL 5.7 or higher in your docker-compose file."
                )

    if "5.6" in data.db_engine_version:
        log_error_and_exit("MySQL 5.6 is obsolete. Please chooses MySQL 5.7 in `db_engine_version`.")


def verify_data_studio(data: SimpleNamespace):
    """Verify fields related to Data Studio."""

    if data.flag_enable_data_studio:
        if data.tower_container_version < "v24.1.0":
            log_error_and_exit(
                "`tower_container_version` must bv24.1.0 or higher to set `flag_enable_data_studio` to true."
            )

        if data.tower_container_version < "v24.3.0" and data.data_studio_container_version >= "0.7.8":
            log_error_and_exit(
                "`data_studio_container_version` cannot be 0.7.8+ when `tower_container_version` is less than v24.3.0."
            )

        if data.flag_limit_data_studio_to_some_workspaces:
            # https://www.geeksforgeeks.org/python-check-whether-string-contains-only-numbers-or-not/
            # if re.match('[0-9]*$', data.data_studio_eligible_workspaces):
            if not re.findall(r"[0-9]+,[0-9]+", data.data_studio_eligible_workspaces):
                log_error_and_exit("`data_studio_eligible_workspaces may only be populated by digits and commas.")

        if data.flag_use_private_cacert:
            logger.warning("Please see documentation to understand how to make private certs work with Studios images.")

        # Deferred until better solution comes along to get TF locals
        # - Add check that CONNECT_PROXY_URL and TOWER_DATA_STUDIO_CONNECT_URL are the same.
        # - Add check that CONNECT_PROXY_URL and TOWER_DATA_STUDIO_CONNECT_URL are only one subdomain deeper than Tower server URL

        if data.flag_studio_enable_path_routing:
            if data.tower_container_version < "v25.2.0":
                log_error_and_exit(
                    "To use Studios path-based routing, `tower_container_version` must be at least '25.2.0'."
                )

            if data.data_studio_container_version < "0.8.2":
                log_error_and_exit(
                    "To use Studios path-based routing, `data_studio_container_version` must be at least '0.8.2'."
                )

            if len(data.data_studio_path_routing_url) == 0:
                # Note: This isn't super but better than nothing.
                # TODO: Find package to validate it's a legit domain.
                log_error_and_exit(
                    "When `flag_studio_enable_path_routing` is true, `data_studio_path_routing_url` must be set."
                )

            logger.warning(
                "Reminder: Studios path-based routing will ony work for VSCode / R / Jupyter with Connect client >= 0.8.4"
            )


def verify_not_v24_1_0(data: SimpleNamespace):
    """Verify that user has not selected Tower v24.1.0 (due to serialization bug)."""
    if data.tower_container_version == "v24.1.0":
        log_error_and_exit("Tower version 24.1.0 has a fatal serialization flaw. Please use v24.1.3 or higher.")


def verify_not_v24_1_1(data: SimpleNamespace):
    """Verify that user has not selected Tower v24.1.1 (memory leak)."""
    if data.tower_container_version == "v24.1.1":
        log_error_and_exit("Tower version 24.1.1 has Micronaut framework flaw. Please use v24.1.3 or higher.")


def verify_not_v24_1_2(data: SimpleNamespace):
    """Verify that user has not selected Tower v24.1.2 (Redis TLS issue)."""
    if data.tower_container_version == "v24.1.2":
        log_error_and_exit("Tower version 24.1.2 has a TLS flaw. Please use v24.1.3 or higher.")


def verify_if_v24_1_3(data: SimpleNamespace):
    """Warn that Tower v24.1.3 cannot connect to Redis securely."""
    if data.tower_container_version == "v24.1.3":
        logger.warning(
            "Tower version 24.1.3 cannot connect to Redis via TLS (i.e. `rediss://`). Please use v24.1.4 or higher if necessary."
        )


def verify_if_v24_1_4(data: SimpleNamespace):
    """Warn that Tower v24.1.4 has email problem."""
    if data.tower_container_version == "v24.1.4":
        oidc_flags = [
            data.flag_oidc_use_generic,
            data.flag_oidc_use_google,
            data.flag_oidc_use_github,
        ]
        if any(oidc_flags):
            logger.warning("Tower version 24.1.4 cannot send emails. You will only be able to use your OIDC option.")
        else:
            log_error_and_exit("Tower version 24.1.4 cannot send emails. Please use v24.1.5 or higher.")


def verify_connect_version_tls(data: SimpleNamespace):
    """Warn that Tower v24.1.4 cannot connect to Redis securely."""
    if data.data_studio_container_version == "0.7.0":
        logger.warning(
            "Connect v0.7.0 cannot connect to Redis via TLS (i.e. `rediss://`). Please use v0.7.3 or higher if necessary."
        )


def verify_alb_settings(data: SimpleNamespace):
    """Verify that user does not have contradictory settings in case of ALB vs. no ALB."""
    if data.flag_use_private_cacert and data.flag_make_instance_private_behind_public_alb:
        log_error_and_exit(
            "Use of private cert on EC2 cannot work with `flag_make_instance_private_behind_alb = true`. Please set only one of the options to true."
        )


def verify_redis_version(data: SimpleNamespace):
    """Warn that versions of Seqera Platform >= 24.2 will default to Redis v7.0 container image."""

    if data.tower_container_version >= "v24.2.0":
        if data.flag_use_container_redis:
            logger.warning("Seqera Platform version >= 24.2.0 uses a Redis v7.0 container (previously Redis v6.0).")

        if data.flag_create_external_redis:
            # TO DO
            # As of Jan 9/25, the external redis are hardcoded into the `003-database.tf` file.
            # This uses a redis 7.0 as baseline and thus is compliant to the needs of 24.2.2.
            # In future this may need to change if Tower demands require a version > Redis 7.0 OR we
            # choose to make the external redis values configurable.
            logger.warning("The external Elasticache instance is hardcoded to use Redis 7.0.")

    else:
        logger.warning("When you upgrade to Seqera Platform >= v24.2, a Redis version >= 6.2 will be required.")


def verify_wave(data: SimpleNamespace):
    if (data.flag_use_wave == True) and (data.flag_use_wave_lite == True):
        log_error_and_exit("`flag_use_wave` and `flag_use_wave_lite` cannot both be set to true.")

    if data.flag_use_wave_lite == True:
        if data.flag_use_private_cacert:
            logger.warning("Please see documentation to understand how to make private certs work with Wave-Lite.")


def verify_ssh_access(data: SimpleNamespace):
    # VM needs to be sitting in public subnet in order to connect to it by SSH directly (instead of EICE).
    # I often try this with VM in private subnet and it takes awhile to figure out why. Adding check.
    if data.flag_make_instance_public == True:
        if data.flag_create_new_vpc == True:
            if data.vpc_new_ec2_subnets[0] not in data.vpc_new_public_subnets:
                log_error_and_exit(
                    "You have set `flag_make_instance_public = true` but your EC2 is in a private subnet. SSH will fail. Please fix."
                )

        if data.flag_use_existing_vpc == True:
            logger.warning(
                "You have set `flag_make_instance_public = true`. Please ensure `vpc_existing_ec2_subnets` is populated by a public subnet CIDR."
            )


def verify_production_deployment(data: SimpleNamespace):
    if (data.flag_create_external_db == False) or (data.flag_create_external_redis == False):
        logger.warning(
            "WARNING: You are running Seqera Platform without a managed DB/Redis. This does not align to Seqera-recommended Production deployment best practices and can result in system instability."
        )

    if (data.flag_use_wave_lite == True) and (
        (data.flag_create_external_db == False) or (data.flag_create_external_redis == False)
    ):
        logger.warning(
            "WARNING: You are running Wave Lite without a managed DB/Redis. This does not align to Seqera-recommended Production deployment best practices and can result in system instability."
        )


def verify_insecure_platform(data: SimpleNamespace):
    if data.flag_do_not_use_https:
        if data.flag_enable_data_studio:
            log_error_and_exit("Studios requires a secure Seqera Platform endpoint.")

        if data.flag_use_wave_lite:
            log_error_and_exit("Wave-Lite requires a secure Seqera Platform endpoint.")


def warn_about_user_workspaces(data: SimpleNamespace):
    """Warn that disabling user workspaces in Platform < v24.2.0 will disable User Credetials & Secrets."""

    if data.tower_container_version < "v24.2.0":
        logger.warning(
            "Your Platform version will cause User Credentials & User Secrets to stop working if you disable personal workspaces."
        )


def warn_if_entra_id_error_possible(data: SimpleNamespace):
    """Warn using a Platform version < 25.3, with Entra ID (Azure AD), will fail if extra config snippet not uncommented."""

    if (data.tower_container_version < "v25.3") and data.flag_oidc_use_generic:
        logger.warning(
            "If you are using Entra ID (Azure AD) as your IDP, please consult text related to Issue 267 in `tower.yml` for a mandatory configuration change."
        )


# -------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n")
    logger.info("Beginning tfvars configuration check.".upper())

    # Generate dictionary from tfvars then convert to SimpleNamespace for cleaner dot-notation access.
    # Kept the two objects different for convenience when .keys() method is required.
    data_dictionary = tf_vars_json_payload
    data = SimpleNamespace(**data_dictionary)

    # Check minimum container version
    if not ((data.tower_container_version).startswith("v")) or (data.tower_container_version < "v23.1.0"):
        log_error_and_exit("Tower version minimum is 23.1.0 (for Parameter Store integration).")

    # Check known problem Tower versions
    print("\n")
    # logger.info("Verifying Seqera Platform Enterprise versions")
    logger.info("Verifying Seqera Platform Enterprise versions")
    logger.info("-" * 50)
    verify_not_v24_1_0(data)
    verify_not_v24_1_1(data)
    verify_not_v24_1_2(data)
    verify_if_v24_1_3(data)
    verify_if_v24_1_4(data)
    verify_connect_version_tls(data)
    verify_redis_version(data)

    # Verify tfvars fields
    print("\n")
    logger.info("Verifying TFVARS file")
    logger.info("-" * 50)
    verify_only_one_true_set(data)
    verify_sensitive_keys(data, data_dictionary)
    verify_tfvars_config_dependencies(data)
    verify_docker_version(data)

    # Verify Tower application configurations
    print("\n")
    logger.info("Verifying Tower configurations")
    logger.info("-" * 50)
    verify_tower_root_users(data)
    verify_tower_self_signed_certs(data)
    verify_tower_server_url(data)
    verify_tower_groundswell(data)
    verify_docker_daemon_loggin(data)
    verify_email_login_disablement(data)

    # Verify AWS integrations
    print("\n")
    logger.info("Verifying AWS Integrations")
    logger.info("-" * 50)
    verify_subnet_privacy(data)
    verify_ses_integration(data)
    verify_route53_integration(data)
    verify_ingress_and_egress(data, data_dictionary)
    verify_flow_logs(data)
    verify_alb_settings(data)

    # Verify Public/Private Subnet settings
    print("\n")
    logger.info("Verifying Subnet settings")
    logger.info("-" * 50)
    verify_ssh_access(data)

    # Verify data studio settings
    print("\n")
    logger.info("Verifying Data Studio settings")
    logger.info("-" * 50)
    verify_data_studio(data)

    # Verify database settings (last since this is the most critical component and most likely to be seen)
    print("\n")
    logger.info("Verifying Database settings")
    logger.info("-" * 50)
    verify_ami_update_behaviour(data)
    verify_database_configuration(data)

    # Verify Wave settings
    print("\n")
    logger.info("Verifying Wave settings")
    logger.info("-" * 50)
    verify_wave(data)

    # Verify alignment to Production Best Practice
    print("\n")
    logger.info("Verifying alignment to Production Best Practices")
    logger.info("-" * 50)
    verify_production_deployment(data)
    verify_insecure_platform(data=data)

    # Issue Warnings (if applicable)
    warn_about_user_workspaces(data)
    warn_if_entra_id_error_possible(data)

    print("\n")
    logger.info("Finished tfvars configuration check.")

    exit()


# 23.4.3
# TO DO
#  - migrate-db
#  - Mandatory bootstrap values
#  - Improve logic for value cleansing for these checks.
#  - `tower_enable_platforms`
#  - Check `tower_db_min_pool_size`, `tower_db_max_pool_size`, `tower_db_max_lifetime`,
#  - Check ALB cert for legit ARN syntax.
#  - `tower_root_user` values are valid email format and comma-delimited.
#  - Custom OIDC
#  - SEQERAKIT
#  - DNS Reminder `flag_create_route53_record`
#  - Add proper email string check
# - Non-EC2 Subnets in VPC CIDR
# - AZs and Region
# - Pre-existing IAM role
# - EBS encryption key
# - DNS hosted zones
#    - Check existing public / private hosted zones exist if specified in tfvars.

# Don't have access to existing public / private subnets as of yet. Maybe need to add boto3 to get?
# TO DO:
#   1. Improve detection of public vs private subnets via route table access to an internet gateway and/or tagging.
#      For Seqera testing purposes, auto-assignment of IP on launch is good enough - comes back in subnet payload and our test
#      VPC is configured to auto-assign.
#   2. Add RDS subnet check
#   3. Add Redis subent check
