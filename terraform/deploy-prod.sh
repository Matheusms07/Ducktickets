#!/bin/bash
# Deploy DuckTickets Production Environment

set -e

echo "🦆 DuckTickets - Production Deploy"
echo "=================================="

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Run: aws configure"
    exit 1
fi

echo "✅ AWS CLI configured"

# Initialize Terraform
echo "🔧 Initializing Terraform..."
terraform init

# Plan production deployment
echo "📋 Planning production deployment..."
terraform plan -var-file="terraform.tfvars.prod" -out=prod.tfplan

echo ""
echo "⚠️  PRODUCTION DEPLOYMENT PLAN READY"
echo "===================================="
echo ""
echo "📊 This will create:"
echo "   • Production RDS PostgreSQL"
echo "   • Auto Scaling Group (1-3 instances)"
echo "   • Application Load Balancer"
echo "   • Auto-deployment enabled"
echo ""
echo "💰 Estimated cost: ~$80-120/month"
echo ""

read -p "Continue with production deployment? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

# Apply production deployment
echo "🚀 Deploying production infrastructure..."
terraform apply prod.tfplan

# Get outputs
echo ""
echo "🎉 Production Deployment Complete!"
echo "================================="
echo ""
terraform output

echo ""
echo "📋 Post-Deployment Steps:"
echo "1. Wait ~10 minutes for auto-deployment to complete"
echo "2. Configure DNS to point to Load Balancer"
echo "3. Setup SSL certificate (Let's Encrypt/ACM)"
echo "4. Configure monitoring and alerts"
echo "5. Setup backup strategy"

echo ""
echo "🔧 Management Commands:"
echo "   terraform output                    # View all outputs"
echo "   aws logs tail /aws/ec2/user-data   # View deployment logs"
echo "   ./status.sh                        # Check infrastructure status"