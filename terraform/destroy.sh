#!/bin/bash
# Terraform Destroy Script for DuckTickets HML

set -e

echo "🦆 DuckTickets - Terraform Destroy"
echo "=================================="

echo "⚠️  WARNING: This will destroy ALL infrastructure!"
echo "   • Elastic Beanstalk Environment"
echo "   • RDS PostgreSQL Database"
echo "   • S3 Bucket (and all files)"
echo "   • SQS Queue"
echo ""

read -p "Are you sure? Type 'yes' to continue: " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Aborted"
    exit 1
fi

echo "🗑️ Destroying infrastructure..."
terraform destroy -auto-approve

echo ""
echo "✅ All resources destroyed!"
echo "💰 No more AWS charges for this environment"