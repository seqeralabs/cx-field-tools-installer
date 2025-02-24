%{ if flag_private_tower_without_eice == true  || flag_make_instance_public == true ~}
Host ${app_name}
    Hostname ${dns_instance_ip}
    User ${user}
    IdentityFile ${pemfile}
    StrictHostKeyChecking no
    # Explicit mitigation for CVE-2025-26465. See: https://github.com/seqeralabs/cx-field-tools-installer/issues/180
    VerifyHostKeyDNS no
%{~ else ~}
Host ${app_name}
    Hostname ${node_id}
    User ${user}
    IdentityFile ${pemfile}
    ProxyCommand aws --region ${region} --profile ${profile} ec2-instance-connect open-tunnel --instance-id %h
    StrictHostKeyChecking no
    # Explicit mitigation for CVE-2025-26465. See: https://github.com/seqeralabs/cx-field-tools-installer/issues/180
    VerifyHostKeyDNS no
%{ endif }
