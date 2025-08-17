#!/bin/bash
# AWS Setup Script for DuckTickets HML - Low Cost Configuration

set -e

echo "🦆 DuckTickets - AWS HML Setup (Low Cost)"
echo "========================================"

# Variables
APP_NAME="ducktickets"
ENV_NAME="ducktickets-hml"
REGION="us-east-1"
INSTANCE_TYPE="t3.micro"
DB_INSTANCE_CLASS="db.t3.micro"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Run: aws configure"
    exit 1
fi

echo "✅ AWS CLI configured"

# 1. Create S3 bucket for storage (if not exists)
echo "📦 Creating S3 bucket..."
BUCKET_NAME="${APP_NAME}-hml-storage-$(date +%s)"
aws s3 mb s3://$BUCKET_NAME --region $REGION || echo "Bucket may already exist"

# 2. Create RDS PostgreSQL (t3.micro for low cost)
echo "🗄️ Creating RDS PostgreSQL..."
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
echo "Generated DB Password: $DB_PASSWORD"

aws rds create-db-instance \
    --db-instance-identifier $ENV_NAME-db \
    --db-instance-class $DB_INSTANCE_CLASS \
    --engine postgres \
    --engine-version 13.13 \
    --master-username ducktickets \
    --master-user-password $DB_PASSWORD \
    --allocated-storage 20 \
    --storage-type gp2 \
    --vpc-security-group-ids default \
    --db-name ducktickets \
    --backup-retention-period 1 \
    --no-multi-az \
    --publicly-accessible \
    --region $REGION || echo "RDS may already exist"

# 3. Create SQS Queue
echo "📨 Creating SQS Queue..."
QUEUE_URL=$(aws sqs create-queue \
    --queue-name $ENV_NAME-queue \
    --region $REGION \
    --query 'QueueUrl' \
    --output text) || echo "Queue may already exist"

# 4. Initialize Elastic Beanstalk
echo "🚀 Initializing Elastic Beanstalk..."
eb init $APP_NAME --platform python-3.11 --region $REGION || echo "EB already initialized"

# 5. Create EB Environment
echo "🌍 Creating EB Environment..."
eb create $ENV_NAME \
    --instance-type $INSTANCE_TYPE \
    --platform python-3.11 \
    --single-instance || echo "Environment may already exist"

# 6. Set environment variables
echo "⚙️ Setting environment variables..."
eb setenv \
    ENVIRONMENT=homologation \
    SECRET_KEY=$(openssl rand -base64 32) \
    DATABASE_URL="postgresql://ducktickets:$DB_PASSWORD@$ENV_NAME-db.cluster-xxxxx.$REGION.rds.amazonaws.com:5432/ducktickets" \
    AWS_REGION=$REGION \
    S3_BUCKET=$BUCKET_NAME \
    SQS_QUEUE_URL=$QUEUE_URL \
    DEBUG=false

echo ""
echo "🎉 AWS HML Setup Complete!"
echo "=========================="
echo "📊 Resources Created:"
echo "   • EC2: t3.micro (single instance)"
echo "   • RDS: db.t3.micro PostgreSQL"
echo "   • S3: $BUCKET_NAME"
echo "   • SQS: $QUEUE_URL"
echo ""
echo "💰 Estimated Monthly Cost: ~$25-35 USD"
echo ""
echo "🔑 Database Password: $DB_PASSWORD"
echo "⚠️  Save this password securely!"
echo ""
echo "📋 Next Steps:"
echo "   1. Update DATABASE_URL with actual RDS endpoint"
echo "   2. Run: eb deploy"
echo "   3. Run: eb open"