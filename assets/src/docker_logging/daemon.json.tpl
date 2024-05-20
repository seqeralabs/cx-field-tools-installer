%{ if flag_docker_logging_local == true ~}
{
    "log-driver": "local",
    "log-opts": {
      "max-size": "20m",
      "max-file": "5"
    }
  }
%{ endif }