# https://registry.terraform.io/modules/terraform-aws-modules/alb/aws/latest
module "alb" {
  count = var.flag_create_load_balancer == true ? 1 : 0

  source  = "terraform-aws-modules/alb/aws"
  version = "8.7.0"

  name               = local.global_prefix
  load_balancer_type = "application"

  vpc_id          = local.vpc_id
  subnets         = module.subnet_collector.subnet_ids_alb
  security_groups = [module.sg_alb_core[0].security_group_id]
  internal        = var.flag_make_instance_private == true || var.flag_private_tower_without_eice == true ? true : false

  # Suppress useless blank security group
  create_security_group = false

  # Do not keep or breaks Tower audit logging.
  # https://registry.terraform.io/modules/terraform-aws-modules/alb/aws/latest
  enable_xff_client_port = false

  # Fixes tfsec warning
  # https://aquasecurity.github.io/tfsec/latest/checks/aws/elb/drop-invalid-headers/
  drop_invalid_header_fields = true


  # access_logs = {
  #   bucket              = "my-alb-logs"
  # }

  http_tcp_listeners = [
    {
      port        = 80
      protocol    = "HTTP"
      action_type = "redirect"

      redirect = {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }
  ]

  https_listeners = [
    {
      port               = 443
      protocol           = "HTTPS"
      certificate_arn    = var.alb_certificate_arn
      target_group_index = 0
      # Fixes tfsec warning about "An outdated SSL policy is in use by a load balancer."
      # https://aquasecurity.github.io/tfsec/v1.0.8/checks/aws/elb/use-secure-tls-policy/
      # Flag appears undocumented in ALB module code examples and input variables.
      ssl_policy = "ELBSecurityPolicy-TLS-1-2-2017-01"
    }
  ]

  target_groups = concat(
    [
      # Tower target group (always present)
      {
        name_prefix      = "p8000"
        backend_protocol = "HTTP"
        backend_port     = 8000
        target_type      = "instance"
        targets = {
          my_target = {
            target_id = aws_instance.ec2.id
            port      = 8000
          }
        }
      }
    ],
    # Connect target group (conditional)
    var.flag_enable_data_studio ? [
      {
        name_prefix      = "p9090"
        backend_protocol = "HTTP"
        backend_port     = 9090
        target_type      = "instance"
        targets = {
          my_target = {
            target_id = aws_instance.ec2.id
            port      = 9090
          }
        }
      }
    ] : [],
    # Wave-Lite target group (conditional)
    var.flag_use_wave_lite ? [
      {
        name_prefix      = "p9099"
        backend_protocol = "HTTP"
        backend_port     = 9099
        target_type      = "instance"
        targets = {
          my_target = {
            target_id = aws_instance.ec2.id
            port      = 9099
          }
        }
      }
    ] : []
  )

  https_listener_rules = concat(
    [
      # Always present rules
      {
        https_listener_index = 0
        priority             = 5000
        actions = [{
          type               = "forward"
          target_group_index = 0
        }]
        conditions = [{
          host_headers = [var.tower_server_url]
        }]
      }
    ],
    # (Conditional) Connect
    var.flag_enable_data_studio ? [
      {
        https_listener_index = 0
        priority             = 5010
        actions = [{
          type               = "forward"
          target_group_index = 1
        }]
        conditions = [{
          host_headers = [module.connection_strings.tower_connect_wildcard_dns]
        }]
      }
    ] : [],
    # (Conditional) Wave-Lite
    var.flag_use_wave_lite ? [
      {
        https_listener_index = 0
        priority             = 5001
        actions = [{
          type = "forward"
          # If data studio not activate, Wave-Lite target group will be at index 1. If both activate, its at index 2.
          target_group_index = var.flag_enable_data_studio ? 2 : 1
        }]
        conditions = [{
          host_headers = [module.connection_strings.tower_wave_dns]
        }]
      }
    ] : []
  )

  tags = {
    Environment = "Test"
  }
}
