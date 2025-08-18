#!/bin/bash
# Start DuckTickets HML Infrastructure

set -e

echo "▶️ DuckTickets - Start Infrastructure"
echo "====================================="

DB_IDENTIFIER="ducktickets-db-hml"

# Start RDS Database
echo "▶️ Starting RDS Database..."
aws rds start-db-instance \
    --db-instance-identifier $DB_IDENTIFIER

echo "⏳ Waiting for database to be available..."
aws rds wait db-instance-available \
    --db-instance-identifier $DB_IDENTIFIER

# Recreate Elastic Beanstalk Environment
echo "▶️ Recreating Elastic Beanstalk Environment..."
terraform apply -target=aws_elastic_beanstalk_environment.main -auto-approve

echo ""
echo "✅ Infrastructure Started!"
echo "========================="
echo "🌐 Application URL:"
terraform output -raw eb_environment_url

echo ""
echo "📋 Next Steps:"
echo "1. Wait ~5 minutes for EB to be ready"
echo "2. Deploy latest code if needed"
echo "3. Test application"