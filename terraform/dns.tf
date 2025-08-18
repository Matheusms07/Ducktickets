# Route53 DNS Configuration

# Hosted Zone (only if create_route53 is true)
resource "aws_route53_zone" "main" {
  count = var.create_route53 ? 1 : 0
  
  name = var.domain_name
  
  tags = {
    Name = "${var.app_name}-zone"
    Environment = var.environment
  }
}

# A Record pointing to Elastic IP
resource "aws_route53_record" "main" {
  count = var.domain_name != "" ? 1 : 0
  
  zone_id = var.create_route53 ? aws_route53_zone.main[0].zone_id : data.aws_route53_zone.existing[0].zone_id
  name    = var.environment == "prod" ? var.domain_name : "${var.environment}.${var.domain_name}"
  type    = "A"
  ttl     = 300
  records = [aws_eip.main.public_ip]
}

# WWW CNAME (for production)
resource "aws_route53_record" "www" {
  count = var.domain_name != "" && var.environment == "prod" ? 1 : 0
  
  zone_id = var.create_route53 ? aws_route53_zone.main[0].zone_id : data.aws_route53_zone.existing[0].zone_id
  name    = "www.${var.domain_name}"
  type    = "CNAME"
  ttl     = 300
  records = [var.domain_name]
}

# Data source for existing hosted zone
data "aws_route53_zone" "existing" {
  count = var.domain_name != "" && !var.create_route53 ? 1 : 0
  
  name         = var.domain_name
  private_zone = false
}

# SSL Certificate (ACM)
resource "aws_acm_certificate" "main" {
  count = var.domain_name != "" ? 1 : 0
  
  domain_name       = var.environment == "prod" ? var.domain_name : "${var.environment}.${var.domain_name}"
  validation_method = "DNS"
  
  subject_alternative_names = var.environment == "prod" ? ["www.${var.domain_name}"] : []
  
  lifecycle {
    create_before_destroy = true
  }
  
  tags = {
    Name = "${var.app_name}-cert-${var.environment}"
  }
}

# Certificate validation
resource "aws_route53_record" "cert_validation" {
  for_each = var.domain_name != "" ? {
    for dvo in aws_acm_certificate.main[0].domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}
  
  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = var.create_route53 ? aws_route53_zone.main[0].zone_id : data.aws_route53_zone.existing[0].zone_id
}

resource "aws_acm_certificate_validation" "main" {
  count = var.domain_name != "" ? 1 : 0
  
  certificate_arn         = aws_acm_certificate.main[0].arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}