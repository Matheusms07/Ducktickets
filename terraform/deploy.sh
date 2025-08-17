#!/bin/bash
# Terraform Deploy Script for DuckTickets HML

set -e

echo "🦆 DuckTickets - Terraform Deploy"
echo "================================="

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform not installed. Install from: https://terraform.io"
    exit 1
fi

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Run: aws configure"
    exit 1
fi

echo "✅ Prerequisites OK"

# Initialize Terraform
echo "🔧 Initializing Terraform..."
terraform init

# Plan deployment
echo "📋 Planning deployment..."
terraform plan -out=tfplan

# Apply deployment
echo "🚀 Deploying infrastructure..."
terraform apply tfplan

# Get outputs
echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo ""
echo "📊 Infrastructure Created:"
terraform output

echo ""
echo "🔑 Sensitive Information:"
echo "Database Password: $(terraform output -raw database_password)"
echo "Database Endpoint: $(terraform output -raw database_endpoint)"

echo ""
echo "📋 Next Steps:"
echo "1. Wait ~10 minutes for RDS to be ready"
echo "2. Deploy application code to Elastic Beanstalk"
echo "3. Run database migrations"
echo "4. Create admin user"

echo ""
echo "🌐 Application URL:"
echo "$(terraform output -raw eb_environment_url)"