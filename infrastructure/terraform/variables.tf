# Terraform Variables
variable "aws_region" {
  description = "AWS Region"
  type        = string
  default     = "eu-west-1"
}

variable "cluster_name" {
  description = "EKS Cluster Name"
  type        = string
  default     = "agentic-trader-cluster"
}

variable "cluster_version" {
  description = "Kubernetes Version"
  type        = string
  default     = "1.28"
}

variable "db_password" {
  description = "RDS Database Password"
  type        = string
  sensitive   = true
}

variable "api_replicas" {
  description = "Number of API replicas"
  type        = number
  default     = 3
}

variable "environment" {
  description = "Deployment Environment"
  type        = string
  default     = "production"
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "trader.example.com"
}

variable "enable_monitoring" {
  description = "Enable Prometheus/Grafana monitoring"
  type        = bool
  default     = true
}
