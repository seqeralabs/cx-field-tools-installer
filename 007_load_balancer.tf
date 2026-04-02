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


## ------------------------------------------------------------------------------------
## NLB — Data Studios SSH
##
## WHY A SEPARATE NLB:
##   The ALB above is a Layer 7 (HTTP/HTTPS) load balancer. It cannot handle raw TCP
##   traffic. SSH operates at Layer 4 (raw TCP) on port 2222, so it requires a Network
##   Load Balancer (NLB) to pass TCP connections through to connect-proxy on the EC2
##   instance.
##
##   The NLB is only created when flag_enable_data_studio_ssh = true AND
##   flag_create_load_balancer = true. If flag_create_load_balancer = false, no NLB
##   is created — instead, a Route53 A record points connect-ssh.<tower_server_url>
##   directly to the EC2 instance IP (see 008_route53.tf aws_route53_record.ec2_ssh).
##   SSH still works in that case via direct EC2 access on port 2222.
##
## WHAT IT DOES:
##   - Creates an NLB listening on TCP port 2222
##   - Forwards connections to the EC2 instance port 2222 (connect-proxy SSH listener)
##   - Its DNS name is used by the connection_strings module to derive
##     tower_connect_ssh_url, which is rendered into TOWER_DATA_STUDIO_CONNECT_SSH_ADDRESS
##     in tower.env — this is the hostname Platform shows users in the UI as the SSH
##     address for Studio sessions
## ------------------------------------------------------------------------------------

resource "aws_lb" "nlb_ssh" {
  count = var.flag_enable_data_studio_ssh && var.flag_create_load_balancer ? 1 : 0

  name               = "${local.global_prefix}-ssh"
  load_balancer_type = "network"
  internal           = var.flag_make_instance_private == true || var.flag_private_tower_without_eice == true ? true : false
  subnets            = module.subnet_collector.subnet_ids_alb
}

resource "aws_lb_target_group" "nlb_ssh" {
  count = var.flag_enable_data_studio_ssh && var.flag_create_load_balancer ? 1 : 0

  name_prefix = "ssh22"
  port        = 2222
  protocol    = "TCP"
  vpc_id      = local.vpc_id
  target_type = "instance"

  health_check {
    protocol = "TCP"
    port     = "2222"
  }
}

resource "aws_lb_target_group_attachment" "nlb_ssh" {
  count = var.flag_enable_data_studio_ssh && var.flag_create_load_balancer ? 1 : 0

  target_group_arn = aws_lb_target_group.nlb_ssh[0].arn
  target_id        = aws_instance.ec2.id
  port             = 2222
}

resource "aws_lb_listener" "nlb_ssh" {
  count = var.flag_enable_data_studio_ssh && var.flag_create_load_balancer ? 1 : 0

  load_balancer_arn = aws_lb.nlb_ssh[0].arn
  port              = 2222
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.nlb_ssh[0].arn
  }
}
