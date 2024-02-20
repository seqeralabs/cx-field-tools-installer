compute-envs:
  - type: aws-batch
    config-mode: forge
    name: "${seqerakit_compute_env_name}"
    workspace: "${seqerakit_org_name}/${seqerakit_workspace_name}"
    credentials: 'aws_credentials'
    region: "${aws_region}"
    work-dir: "${seqerakit_workdir}"
    provisioning-model: SPOT
    fusion-v2: ${use_fusion_v2}
    wave: ${use_wave}
    fargate: False
    fast-storage: ${use_fast_storage}
    instance-types: "${instance_types}"
    no-ebs-auto-scale: True
    max-cpus: 500
    wait: AVAILABLE
    # List needed for JSON payloads but breaks tw when using YAML (needs comma-delimited string)
    # Don't `jsonencode` or else it'll create `"a", "b"` instead of "a,b"
    # subnets: [ ${join(", ", [for id in subnets: jsonencode(id)])} ]
    subnets: ${join(",", [for id in subnets: id])}
    vpc-id: "${vpc_id}"
    # List needed for JSON payloads but breaks tw when using YAML (needs comma-delimited string)
    # Don't `jsonencode` or else it'll create `"a", "b"` instead of "a,b"
    # security-groups: [ ${join(", ", [for id in securityGroups: jsonencode(id)])} ]
    security-groups: ${join(",", [for id in securityGroups: id])}
    key-pair: ${ec2KeyPair}