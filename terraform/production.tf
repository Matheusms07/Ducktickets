# Production Environment Configuration

variable "enable_auto_deploy" {
  description = "Enable automatic deployment on instance creation"
  type        = bool
  default     = false
}

variable "instance_type_prod" {
  description = "Instance type for production"
  type        = string
  default     = "t3.small"
}

variable "environment_type" {
  description = "Environment type (hml, prod)"
  type        = string
  default     = "hml"
}

# Production-specific resources
resource "aws_launch_template" "prod" {
  count = var.environment_type == "prod" ? 1 : 0
  
  name_prefix   = "${var.app_name}-prod-"
  image_id      = "ami-0c02fb55956c7d316"
  instance_type = var.instance_type_prod
  
  vpc_security_group_ids = [aws_security_group.ec2.id]
  iam_instance_profile {
    name = aws_iam_instance_profile.ec2_profile.name
  }
  
  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    database_url = "postgresql://${aws_db_instance.main.username}:${random_password.db_password.result}@${aws_db_instance.main.endpoint}/${aws_db_instance.main.db_name}"
    secret_key   = random_password.secret_key.result
    aws_region   = var.aws_region
    s3_bucket    = aws_s3_bucket.storage.bucket
    sqs_queue_url = aws_sqs_queue.main.url
    environment  = "prod"
    domain_name  = var.domain_name
  }))
  
  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.app_name}-prod"
      Environment = "production"
      AutoDeploy = var.enable_auto_deploy
    }
  }
}

# Auto Scaling Group for Production
resource "aws_autoscaling_group" "prod" {
  count = var.environment_type == "prod" ? 1 : 0
  
  name                = "${var.app_name}-prod-asg"
  vpc_zone_identifier = [data.aws_subnet.default.id]
  target_group_arns   = var.enable_auto_deploy ? [aws_lb_target_group.prod[0].arn] : []
  health_check_type   = "ELB"
  
  min_size         = 1
  max_size         = 3
  desired_capacity = 1
  
  launch_template {
    id      = aws_launch_template.prod[0].id
    version = "$Latest"
  }
  
  tag {
    key                 = "Name"
    value               = "${var.app_name}-prod-asg"
    propagate_at_launch = false
  }
}

# Load Balancer for Production
resource "aws_lb" "prod" {
  count = var.environment_type == "prod" && var.enable_auto_deploy ? 1 : 0
  
  name               = "${var.app_name}-prod-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.ec2.id]
  subnets            = [data.aws_subnet.default.id, data.aws_subnet.default_b.id]
  
  enable_deletion_protection = false
}

resource "aws_lb_target_group" "prod" {
  count = var.environment_type == "prod" && var.enable_auto_deploy ? 1 : 0
  
  name     = "${var.app_name}-prod-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.default.id
  
  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/healthz"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }
}

resource "aws_lb_listener" "prod" {
  count = var.environment_type == "prod" && var.enable_auto_deploy ? 1 : 0
  
  load_balancer_arn = aws_lb.prod[0].arn
  port              = "80"
  protocol          = "HTTP"
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.prod[0].arn
  }
}

# Data sources for default VPC
data "aws_vpc" "default" {
  default = true
}

data "aws_subnet" "default" {
  vpc_id            = data.aws_vpc.default.id
  availability_zone = "${var.aws_region}a"
  default_for_az    = true
}

data "aws_subnet" "default_b" {
  vpc_id            = data.aws_vpc.default.id
  availability_zone = "${var.aws_region}b"
  default_for_az    = true
}