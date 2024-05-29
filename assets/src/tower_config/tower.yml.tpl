# NOTE: 
# - Fields with `###` comment/reference only. DO NOT enable (values come from other sources (i.e. tower.env and AWS SSM).
# - Fields with `#` can be enabled as needed after Tower is installed.

# Duration of Tower sign-in email link validity
auth:
  mail:
    duration: 30m


# Logger settings (subset) added here to make it easier to tweak as needed
logger:
  levels:
    com.amazonaws: DEBUG          # Use to surface Data Explorer events
    io.micronaut.security: DEBUG
    io.seqera.tower: DEBUG
    io.seqera.tower.security.oidc: DEBUG


mail:
  ### from: ${TOWER_CONTACT_EMAIL}
  smtp:
    ### host: ${TOWER_SMTP_HOST}
    ### port: ${TOWER_SMTP_PORT}
    ### user: ${TOWER_SMTP_USER}
    ### password: ${TOWER_SMTP_PASSWORD}
    auth: ${tower_smtp_auth}
    starttls:
      # `starttls` should be enabled with a production SMTP host
      enable: ${tower_smtp_starttls_enable}
      required: ${tower_smtp_starttles_required }
    ssl:
      protocols: "${tower_smtp_ssl_protocols}"


micronaut:
  application:
    name: ${app_name}

  http:
    client:
      read-timeout: 30s

  security:
    redirect:
      login-success : "/auth?success=true"
      login-failure : "/auth?success=false"

    # WARNING! Do not disable `refresh-token.enabled`. User and pipeline authentication affected equally - breaks long pipelines. (Last updated: March 2/24)
    token:
      jwt:
        # Tower embeds an access-refresh tokens pair in the head job when launching a pipeline.
        # Access token used by Nextflow to authenticate with Tower. 
        # Defaults: Access Token: 1 hour  | Refresh Token:  6 hours
        #
        # Refresh-token expiry may require bumping if your job takes too long to be scheduled (i.e. 6h+).
        # Ensure the `tower.ephemeral.duration` value exceeds the lifespan of your refresh token expiration as well.
        generator:
          access-token:
            expiration: 3600                                # Duration in seconds (ANOMALY: Integer only!) dont add time unit at end!
          refresh-token:
            enabled: true                                   # true | false
            expiration: 6h                                  # Duration is integer + unit (e.g. 6h | 1d)


### The tower scope is used for providing config for your Tower Enterprise installation
tower:

  # As of Tower v23.4.5, the email login option can be disabled.
  # Note: There must be an active OIDC integration configured or else this flag will be ignored.
  auth:
    disable-email: false

  admin:
    # Control user access to personal (i.e. non-Org-based) Workspace.
    user-workspace-enabled: true

  # Tower exposes a unique 1-time-calleable API endpoint at the start of a pipeline run.
  # Nextflow calls this endpoint to retrieve sensitive values / overly-large content that cant/shouldnt be added to a Job request API call. 
  # Linked to `micronaut.token.jwt.generator` token values (api token duration & api endpoint duration).
  ephemeral:
    duration: 8h                                            # Example values: 1m, 8h, 1d. Default: 8h

  dataset:
    max-file-size: 10MB
    allowed-extensions:
      - csv
      - tsv
    allowed-media-types:
      - text/csv
      - text/tab-separated-values

  navbar:
    menus:
      - label: "Docs"
        url: "https://docs.seqera.io"

  trustedEmails:
    - "'${tower_root_users}'"
    - "'${tower_email_trusted_orgs}'"
    - "'${tower_email_trusted_users}'"

  ### Tower instance-wide configuration for authentication. 
  # For further information, see https://help.tower.nf/latest/enterprise/configuration/authentication/
  # auth:
  #   google:
  #     allow-list:
  #       - "*@org.xyz"
  #   oidc:
  #     allow-list:
  #       - "*@org.xyz"

  ### Tower instance-wide configuration for SCM providers. 
  # For further information, see https://help.tower.nf/latest/enterprise/configuration/overview
  # scm:
  #   providers:
  #     github:
  #       user: <YOUR GITHUB USER NAME>
  #       password: <YOUR GITHUB ACCESS TOKEN OR PASSWORD>
  #     gitlab:
  #       user: <YOUR GITLAB USER NAME>
  #       password: <YOUR GITLAB PASSWORD>
  #       token: <YOUR GITLAB TOKEN>
  #     bitbucket:
  #       user: <YOUR BITBUCKET USER NAME>
  #       password: <YOUR BITBUCKET TOKEN OR PASSWORD>