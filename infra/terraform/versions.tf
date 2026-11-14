terraform {
  required_version = ">= 1.7.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
  backend "s3" {}
}
variable "region" { type = string; default = "us-east-1" }
variable "endpoint" { type = string; default = "http://localhost:4566" }
variable "local_emulation" { type = bool; default = true }
variable "enable_network" { type = bool; default = false }
provider "aws" {
  region = var.region
  access_key = var.local_emulation ? "test" : null
  secret_key = var.local_emulation ? "test" : null
  skip_credentials_validation = var.local_emulation
  skip_metadata_api_check = var.local_emulation
  skip_requesting_account_id = var.local_emulation
  s3_use_path_style = var.local_emulation
  endpoints {
    dynamodb = var.local_emulation ? var.endpoint : null
    s3 = var.local_emulation ? var.endpoint : null
    cloudwatch = var.local_emulation ? var.endpoint : null
    logs = var.local_emulation ? var.endpoint : null
    ec2 = var.local_emulation ? var.endpoint : null
    apigateway = var.local_emulation ? var.endpoint : null
  }
}
