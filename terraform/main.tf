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

# Random password for RDS
resource "random_password" "db_password" {
  length  = 32
  special = true
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
  bucket = "${var.app_name}-${var.environment}-storage-${random_id.bucket_suffix.hex}"
}

resource "aws_s3_bucket_versioning" "storage" {
  bucket = aws_s3_bucket.storage.id
  versioning_configuration {
    status = "Enabled"
  }
}

# SQS Queue
resource "aws_sqs_queue" "main" {
  name                      = "${var.app_name}-${var.environment}-queue"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 345600
}

# RDS PostgreSQL
resource "aws_db_instance" "main" {
  identifier = "${var.app_name}-${var.environment}-db"
  
  engine         = "postgres"
  engine_version = "13.13"
  instance_class = "db.t3.micro"
  
  allocated_storage = 20
  storage_type      = "gp2"
  storage_encrypted = true
  
  db_name  = "ducktickets"
  username = "ducktickets"
  password = random_password.db_password.result
  
  backup_retention_period = 1
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  skip_final_snapshot = true
  deletion_protection = false
  publicly_accessible = true
  
  tags = {
    Name = "${var.app_name}-${var.environment}-db"
  }
}

# Elastic Beanstalk Application
resource "aws_elastic_beanstalk_application" "main" {
  name        = var.app_name
  description = "DuckTickets Event Ticketing Platform"
}

# Elastic Beanstalk Environment
resource "aws_elastic_beanstalk_environment" "main" {
  name                = "${var.app_name}-${var.environment}"
  application         = aws_elastic_beanstalk_application.main.name
  solution_stack_name = "64bit Amazon Linux 2 v3.4.24 running Python 3.11"

  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name      = "InstanceType"
    value     = "t3.micro"
  }

  setting {
    namespace = "aws:autoscaling:asg"
    name      = "MinSize"
    value     = "1"
  }

  setting {
    namespace = "aws:autoscaling:asg"
    name      = "MaxSize"
    value     = "2"
  }

  setting {
    namespace = "aws:elasticbeanstalk:environment"
    name      = "EnvironmentType"
    value     = "SingleInstance"
  }

  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "ENVIRONMENT"
    value     = "homologation"
  }

  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "DATABASE_URL"
    value     = "postgresql://${aws_db_instance.main.username}:${random_password.db_password.result}@${aws_db_instance.main.endpoint}/${aws_db_instance.main.db_name}"
  }

  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "SECRET_KEY"
    value     = random_password.secret_key.result
  }

  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "AWS_REGION"
    value     = var.aws_region
  }

  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "S3_BUCKET"
    value     = aws_s3_bucket.storage.bucket
  }

  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "SQS_QUEUE_URL"
    value     = aws_sqs_queue.main.url
  }

  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "DEBUG"
    value     = "false"
  }

  setting {
    namespace = "aws:elasticbeanstalk:cloudwatch:logs"
    name      = "StreamLogs"
    value     = "true"
  }

  setting {
    namespace = "aws:elasticbeanstalk:cloudwatch:logs"
    name      = "DeleteOnTerminate"
    value     = "true"
  }

  setting {
    namespace = "aws:elasticbeanstalk:cloudwatch:logs"
    name      = "RetentionInDays"
    value     = "7"
  }
}

# Outputs
output "eb_environment_url" {
  description = "Elastic Beanstalk environment URL"
  value       = aws_elastic_beanstalk_environment.main.endpoint_url
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