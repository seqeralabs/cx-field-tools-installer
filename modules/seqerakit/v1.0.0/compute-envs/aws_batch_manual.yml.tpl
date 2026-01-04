compute-envs:
  - type: aws-batch 
    config-mode: manual
    name: "${seqerakit_compute_env_name}"
    workspace: "${seqerakit_org_name}/${seqerakit_workspace_name}"
    credentials: 'aws_credentials'
    work-dir: ${seqerakit_workdir}
    region: ${aws_region}
    head-queue: ${seqerakit_aws_manual_head_queue}
    compute-queue: ${seqerakit_aws_manual_compute_queue}
    fusion-v2: ${use_fusion_v2}
    wave: ${use_wave}
    wait: 'AVAILABLE'
    overwrite: True