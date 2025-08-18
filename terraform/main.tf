terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "hml"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "ducktickets"
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = ""
}

variable "create_route53" {
  description = "Create Route53 hosted zone and records"
  type        = bool
  default     = false
}

# Random password for RDS
resource "random_password" "db_password" {
  length  = 32
  special = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "random_password" "secret_key" {
  length  = 32
  special = true
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# S3 Bucket
resource "aws_s3_bucket" "storage" {
  bucket = "${var.app_name}-s3-${var.environment}-${random_id.bucket_suffix.hex}"
}

resource "aws_s3_bucket_versioning" "storage" {
  bucket = aws_s3_bucket.storage.id
  versioning_configuration {
    status = "Enabled"
  }
}

# SQS Queue
resource "aws_sqs_queue" "main" {
  name                      = "${var.app_name}-sqs-${var.environment}"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 345600
}

# RDS PostgreSQL (Private Subnet)
resource "aws_db_instance" "main" {
  identifier = "${var.app_name}-db-${var.environment}"
  
  engine         = "postgres"
  engine_version = "15.8"
  instance_class = "db.t3.micro"
  
  allocated_storage = 20
  storage_type      = "gp3"
  storage_encrypted = true
  
  db_name  = "ducktickets"
  username = "ducktickets"
  password = random_password.db_password.result
  
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  
  backup_retention_period = 1
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  skip_final_snapshot = true
  deletion_protection = false
  publicly_accessible = false
  
  tags = {
    Name = "${var.app_name}-db-${var.environment}"
  }
}

# Security groups defined in vpc.tf

# IAM Role for EC2 SSM
resource "aws_iam_role" "ec2_ssm_role" {
  name = "${var.app_name}-ec2-ssm-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# Attach SSM policy
resource "aws_iam_role_policy_attachment" "ec2_ssm_policy" {
  role       = aws_iam_role.ec2_ssm_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Instance profile
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.app_name}-ec2-profile"
  role = aws_iam_role.ec2_ssm_role.name
}

# Elastic IP
resource "aws_eip" "main" {
  domain = "vpc"
  
  tags = {
    Name = "${var.app_name}-eip-${var.environment}"
  }
}

# EC2 Instance
resource "aws_instance" "main" {
  ami           = "ami-0c02fb55956c7d316" # Amazon Linux 2023
  instance_type = "t3.micro"
  
  root_block_device {
    volume_type = "gp3"
    volume_size = 8
    encrypted   = true
  }
  
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.ec2.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  
  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    database_url = "postgresql://${aws_db_instance.main.username}:${random_password.db_password.result}@${aws_db_instance.main.endpoint}/${aws_db_instance.main.db_name}"
    secret_key   = random_password.secret_key.result
    aws_region   = var.aws_region
    s3_bucket    = aws_s3_bucket.storage.bucket
    sqs_queue_url = aws_sqs_queue.main.url
    environment  = var.environment
    domain_name  = var.domain_name
  }))

  tags = {
    Name = "${var.app_name}-ec2-${var.environment}"
  }
}

# Associate Elastic IP
resource "aws_eip_association" "main" {
  instance_id   = aws_instance.main.id
  allocation_id = aws_eip.main.id
}

# Outputs
output "ec2_public_ip" {
  description = "EC2 instance public IP"
  value       = aws_instance.main.public_ip
}

output "ec2_public_dns" {
  description = "EC2 instance public DNS"
  value       = aws_instance.main.public_dns
}

output "elastic_ip" {
  description = "Elastic IP address"
  value       = aws_eip.main.public_ip
}

output "domain_url" {
  description = "Domain URL"
  value       = var.domain_name != "" ? "https://${var.environment == "prod" ? var.domain_name : "${var.environment}.${var.domain_name}"}" : "http://${aws_eip.main.public_ip}"
}

output "nameservers" {
  description = "Route53 nameservers (if created)"
  value       = var.create_route53 ? aws_route53_zone.main[0].name_servers : []
}

output "database_endpoint" {
  description = "RDS database endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "database_password" {
  description = "RDS database password"
  value       = random_password.db_password.result
  sensitive   = true
}

output "s3_bucket" {
  description = "S3 bucket name"
  value       = aws_s3_bucket.storage.bucket
}

output "sqs_queue_url" {
  description = "SQS queue URL"
  value       = aws_sqs_queue.main.url
}