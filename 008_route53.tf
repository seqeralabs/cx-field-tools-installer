## ------------------------------------------------------------------------------------
## Hosted Zone retrieval
## ------------------------------------------------------------------------------------
data "aws_route53_zone" "public" {
  count = var.flag_use_existing_route53_public_zone == true ? 1 : 0

  name = var.existing_route53_public_zone_name
}


data "aws_route53_zone" "private" {
  count = var.flag_use_existing_route53_private_zone == true ? 1 : 0

  name         = var.existing_route53_private_zone_name
  vpc_id       = local.vpc_id
  private_zone = true
}


## ------------------------------------------------------------------------------------
## Hosted Zone Generation
## ------------------------------------------------------------------------------------
resource "aws_route53_zone" "private" {
  count = var.flag_create_route53_private_zone == true ? 1 : 0

  name = var.new_route53_private_zone_name
  vpc {
    vpc_id = local.vpc_id
  }
}


## ------------------------------------------------------------------------------------
## Route53 A Record Generation
##   Note: If no Route53 records are generated, an entry will be added to the EC2 hosts file
## ------------------------------------------------------------------------------------
resource "aws_route53_record" "alb" {
  count = local.dns_create_alb_record == true ? 1 : 0

  zone_id = local.dns_zone_id
  name    = var.tower_server_url
  type    = "A"

  alias {
    name                   = module.alb[0].lb_dns_name
    zone_id                = module.alb[0].lb_zone_id
    evaluate_target_health = true
  }
}


resource "aws_route53_record" "ec2" {
  count = local.dns_create_ec2_record == true ? 1 : 0

  zone_id = local.dns_zone_id
  name    = var.tower_server_url
  type    = "A"

  ttl     = "5"
  records = [local.dns_instance_ip]
}

# Tower Connect
resource "aws_route53_record" "alb_connect" {
  count = local.dns_create_alb_record == true ? 1 : 0

  zone_id = local.dns_zone_id
  # name    = local.tower_connect_dns
  name    = local.tower_connect_wildcard_dns
  type    = "A"

  alias {
    name                   = module.alb[0].lb_dns_name
    zone_id                = module.alb[0].lb_zone_id
    evaluate_target_health = true
  }
}


resource "aws_route53_record" "ec2_connect" {
  count = local.dns_create_ec2_record == true ? 1 : 0

  zone_id = local.dns_zone_id
  # name    = local.tower_connect_dns
  name    = local.tower_connect_wildcard_dns
  type    = "A"

  ttl     = "5"
  records = [local.dns_instance_ip]
}


resource "aws_route53_record" "alb_wave" {
  count = local.dns_create_alb_record == true && var.flag_use_wave_lite == true ? 1 : 0

  zone_id = local.dns_zone_id
  # name    = local.tower_connect_dns
  name    = local.tower_wave_dns
  type    = "A"

  alias {
    name                   = module.alb[0].lb_dns_name
    zone_id                = module.alb[0].lb_zone_id
    evaluate_target_health = true
  }
}
