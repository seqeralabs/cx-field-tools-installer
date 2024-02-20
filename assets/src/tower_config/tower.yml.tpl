# NOTE: 
# - Fields with `###` comment/reference only. DO NOT enable (values come from other sources (i.e. tower.env and AWS SSM).
# - Fields with `#` can be enabled as needed after Tower is installed.

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

# Do not use for now because - while it works - may be breaking pipelines (Feb 20/24)
#    token:
#      jwt:
#        # Controls behaviour of access token (seconds) and refresh token
#        generator:
#          access-token:
#            expiration: 3600
#          refresh-token:
#            enabled: true

mail:
  ### from: ${TOWER_CONTACT_EMAIL}
  smtp:
    ### host: ${TOWER_SMTP_HOST}
    ### port: ${TOWER_SMTP_PORT}
    ### user: ${TOWER_SMTP_USER}
    ### password: ${TOWER_SMTP_PASSWORD}

    auth: ${tower_smtp_auth}
    starttls:
      enable: ${tower_smtp_starttls_enable}
      required: ${tower_smtp_starttles_required }
    ssl:
      protocols: "${tower_smtp_ssl_protocols}"

### Duration of Tower sign-in email link validity
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

### The tower scope is used for providing config for your Tower Enterprise installation
tower:
  admin:
    # Control whether users have access to their personal (i.e. non-Org-based) Workspace.
    user-workspace-enabled: true

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
