%{ if flag_docker_logging_local == true ~}
{
    "log-driver": "local",
    "log-opts": {
      "max-size": "20m",
      "max-file": "5"
    },
    "default-address-pools": [{ "base":"${docker_cidr_range}","size":24 }]
}
%{ endif }
%{ if flag_docker_logging_journald == true ~}
{
    "log-level": "info",
    "log-driver": "journald",
    "default-address-pools": [{ "base":"${docker_cidr_range}","size":24 }]
}
%{ endif }
%{ if flag_docker_logging_jsonfile == true ~}
{
    "log-driver": "json-file",
    "log-opts": {
      "max-size": "10m",
      "max-file": "3"
    },
    "default-address-pools": [{ "base":"${docker_cidr_range}","size":24 }]
  }
%{ endif }