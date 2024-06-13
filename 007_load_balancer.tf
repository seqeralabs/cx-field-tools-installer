# https://registry.terraform.io/modules/terraform-aws-modules/alb/aws/latest
module "alb" {
  count = var.flag_create_load_balancer == true ? 1 : 0

  source  = "terraform-aws-modules/alb/aws"
  version = "8.7.0"

  name               = local.global_prefix
  load_balancer_type = "application"

  vpc_id          = local.vpc_id
  subnets         = local.subnet_ids_alb
  security_groups = [module.tower_alb_sg.security_group_id]
  internal        = var.flag_make_instance_private == true || var.flag_private_tower_without_eice == true ? true : false

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
      ssl_policy         = "ELBSecurityPolicy-TLS-1-2-2017-01"
    }
  ]

  target_groups = [
    {
      name_prefix      = "pref-"
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
  ]

  tags = {
    Environment = "Test"
  }
}
