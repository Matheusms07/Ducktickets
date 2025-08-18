#!/bin/bash
# Stop DuckTickets HML Infrastructure (Save Money)

set -e

echo "🛑 DuckTickets - Stop Infrastructure"
echo "===================================="

# Get environment name
ENV_NAME="ducktickets-eb-hml"
DB_IDENTIFIER="ducktickets-db-hml"

echo "📊 Current Status:"
echo "   Environment: $ENV_NAME"
echo "   Database: $DB_IDENTIFIER"
echo ""

# Stop Elastic Beanstalk Environment
echo "⏸️ Stopping Elastic Beanstalk..."
aws elasticbeanstalk terminate-environment \
    --environment-name $ENV_NAME \
    --terminate-resources

# Stop RDS Database
echo "⏸️ Stopping RDS Database..."
aws rds stop-db-instance \
    --db-instance-identifier $DB_IDENTIFIER

echo ""
echo "✅ Infrastructure Stopped!"
echo "========================="
echo "💰 Cost Savings:"
echo "   • EC2: $0/month (stopped)"
echo "   • RDS: ~$3/month (stopped, storage only)"
echo "   • S3/SQS: ~$1/month (minimal usage)"
echo ""
echo "📊 Total while stopped: ~$4/month"
echo ""
echo "⚠️  Note: EB environment is TERMINATED (not just stopped)"
echo "   Use './start.sh' to recreate it"