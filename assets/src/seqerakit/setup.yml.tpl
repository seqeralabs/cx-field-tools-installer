organizations:
  - name: "${seqerakit_org_name}"
    full-name: "${seqerakit_org_fullname}"
    description: "Description for ${seqerakit_org_name}"
    location: 'Global'
    website: "${seqerakit_org_url}"
    overwrite: False

workspaces:
  - name: "${seqerakit_workspace_name}"
    full-name: "${seqerakit_workspace_fullname}"
    organization: "${seqerakit_org_name}"
    description: 'Workspace for ${seqerakit_workspace_name}'
    visibility: 'PRIVATE'
    overwrite: False

teams:
  - name: "${seqerakit_team_name}"
    organization: "${seqerakit_org_name}"
    description: "Description for ${seqerakit_team_name}"
    members: [ ${seqerakit_team_members } ]
    overwrite: False

participants:
  - name: "${seqerakit_team_name}"
    type: 'TEAM'
    workspace: "${seqerakit_org_name}/${seqerakit_workspace_name}"
    role: 'ADMIN'
    overwrite: False

credentials:
%{~ if seqerakit_flag_credential_create_aws == true }
  - type: 'aws'
    name: 'aws_credentials'
    workspace: "${seqerakit_org_name}/${seqerakit_workspace_name}"
    access-key: $SEQERAKIT_AWS_ACCESS_KEY_ID
    secret-key: $SEQERAKIT_AWS_SECRET_ACCESS_KEY
    %{~ if seqerakit_flag_credential_use_aws_role == true ~}
    assume-role-arn: $SEQERAKIT_AWS_ASSUME_ROLE_ARN
    %{~ endif ~}
    overwrite: False
%{ endif ~}

%{~ if seqerakit_flag_credential_create_docker == true }
  - type: 'container-reg'
    name: 'dockerhub_credentials'
    workspace: "${seqerakit_org_name}/${seqerakit_workspace_name}"
    username: $SEQERAKIT_DOCKER_USER
    password: $SEQERAKIT_DOCKER_PASSWORD
    registry: 'docker.io'
    overwrite: False
%{ endif ~}

%{~ if seqerakit_flag_credential_create_github == true }
  - type: 'github'
    name: 'github_credentials'
    workspace: "${seqerakit_org_name}/${seqerakit_workspace_name}"
    username: $SEQERAKIT_GITHUB_USER
    password: $SEQERAKIT_GITHUB_TOKEN
    overwrite: False
%{ endif ~}

# Compute env to be injected post-rendering

pipelines:
  - name: 'hello-world'
    url: 'https://github.com/nextflow-io/hello'
    workspace: "${seqerakit_org_name}/${seqerakit_workspace_name}"
    description: 'Tiny hello world pipeline composed of four tasks.'
    compute-env: "${seqerakit_compute_env_name}"
    work-dir: "${seqerakit_workdir}"
    revision: 'master'
    config: './pipelines/nextflow.config'
    pre-run: './pipelines/pre_run.txt'
    post-run: './pipelines/post_run.txt'
    overwrite: False

  - name: 'nf-core-rnaseq-test'
    url: 'https://github.com/nf-core/rnaseq'
    workspace: "${seqerakit_org_name}/${seqerakit_workspace_name}"
    description: 'RNA sequencing analysis pipeline using STAR, RSEM, HISAT2 or Salmon with gene/isoform counts and extensive quality control.'
    compute-env: "${seqerakit_compute_env_name}"
    work-dir: "${seqerakit_workdir}"
    profile: 'test'
    labels: 'profile_test'
    revision: '3.12.0'
    params:
      outdir: "${seqerakit_outdir}"
    config: './pipelines/nextflow.config'
    pre-run: './pipelines/pre_run.txt'
    overwrite: False

  - name: 'nf-core-rnaseq-test-full'
    url: 'https://github.com/nf-core/rnaseq'
    workspace: "${seqerakit_org_name}/${seqerakit_workspace_name}"
    description: 'RNA sequencing analysis pipeline using STAR, RSEM, HISAT2 or Salmon with gene/isoform counts and extensive quality control.'
    compute-env: "${seqerakit_compute_env_name}"
    work-dir: "${seqerakit_workdir}"
    profile: 'test_full'
    labels: 'profile_test_full'
    revision: '3.12.0'
    params:
      outdir: "${seqerakit_outdir}"
    config: './pipelines/nextflow.config'
    pre-run: './pipelines/pre_run.txt'
    overwrite: False

%{~ if seqerakit_flag_credential_create_codecommit == true }
  # CodeCommitTest
  - name: 'cc-test'
    url: 'https://git-codecommit.us-east-1.amazonaws.com/v1/repos/grahamhello'
    workspace: "${seqerakit_org_name}/${seqerakit_workspace_name}"
    description: 'CodeCommit testing pipeline'
    compute-env: "${seqerakit_compute_env_name}"
    work-dir: "${seqerakit_workdir}"
    revision: 'main'
    overwrite: False
%{ endif ~}



launch:
  - name: 'hello-world-launchpad'
    workspace: "${seqerakit_org_name}/${seqerakit_workspace_name}"
    pipeline: 'hello-world'

