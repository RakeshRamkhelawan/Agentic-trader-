# Production Environment Configuration

terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
  }

  backend "s3" {
    bucket         = "agentic-trader-tfstate-prod"
    key            = "terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "agentic-trader-tflock-prod"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = "production"
      Project     = "agentic-trader"
      ManagedBy   = "terraform"
    }
  }
}

# Primary Region - US East
module "eks_primary" {
  source = "../../modules/eks"

  cluster_name       = "agentic-trader-prod"
  environment        = "prod"
  kubernetes_version = "1.29"
  aws_region         = var.aws_region

  vpc_cidr = "10.0.0.0/16"

  node_instance_types = ["t3.large", "t3a.large"]
  node_desired_size   = 3
  node_min_size       = 2
  node_max_size       = 10

  spot_enabled = false

  domain_name = "agentic-trader.com"

  tags = {
    Environment = "production"
    Region      = "primary"
  }
}

# Secondary Region - EU West (for disaster recovery)
module "eks_dr" {
  source = "../../modules/eks"
  providers = {
    aws = aws.eu-west
  }

  cluster_name       = "agentic-trader-prod-dr"
  environment        = "prod"
  kubernetes_version = "1.29"
  aws_region         = "eu-west-1"

  vpc_cidr = "10.1.0.0/16"

  node_instance_types = ["t3.medium", "t3a.medium"]
  node_desired_size   = 2
  node_min_size       = 1
  node_max_size       = 5

  spot_enabled = true

  domain_name = "agentic-trader.com"

  tags = {
    Environment = "production"
    Region      = "dr"
  }
}

# Secondary AWS Provider for DR region
provider "aws" {
  alias  = "eu-west"
  region = "eu-west-1"

  default_tags {
    tags = {
      Environment = "production"
      Project     = "agentic-trader"
      ManagedBy   = "terraform"
    }
  }
}

# Global Accelerator for multi-region traffic management
resource "aws_globalaccelerator_accelerator" "main" {
  name            = "agentic-trader"
  ip_address_type = "IPV4"
  enabled         = true
}

resource "aws_globalaccelerator_listener" "https" {
  accelerator_arn = aws_globalaccelerator_accelerator.main.id
  client_affinity = "SOURCE_IP"
  protocol        = "TCP"

  port_range {
    from_port = 443
    to_port   = 443
  }
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "main" {
  enabled = true
  comment = "Agentic Trader CDN"

  origin {
    domain_name = module.eks_primary.cluster_endpoint
    origin_id   = "eks-primary"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "eks-primary"

    forwarded_values {
      query_string = true
      headers      = ["Origin", "Access-Control-Request-Headers", "Access-Control-Request-Method"]

      cookies {
        forward = "all"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = false
    acm_certificate_arn            = aws_acm_certificate.main.arn
    ssl_support_method             = "sni-only"
    minimum_protocol_version       = "TLSv1.2_2021"
  }
}

# ACM Certificate
resource "aws_acm_certificate" "main" {
  domain_name               = "agentic-trader.com"
  subject_alternative_names = ["*.agentic-trader.com"]
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

# WAF WebACL
resource "aws_wafv2_web_acl" "main" {
  name        = "agentic-trader-prod"
  description = "WAF rules for production"
  scope       = "CLOUDFRONT"

  default_action {
    allow {}
  }

  rule {
    name     = "RateLimit"
    priority = 1

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesCommonRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "agentic-trader-waf"
    sampled_requests_enabled   = true
  }
}
