#!/bin/bash
# Check DuckTickets HML Infrastructure Status

set -e

echo "📊 DuckTickets - Infrastructure Status"
echo "======================================"

# Check Elastic Beanstalk
echo "🌐 Elastic Beanstalk:"
EB_STATUS=$(aws elasticbeanstalk describe-environments \
    --environment-names ducktickets-hml \
    --query 'Environments[0].Status' \
    --output text 2>/dev/null || echo "NotFound")

if [ "$EB_STATUS" = "Ready" ]; then
    echo "   ✅ Running"
    EB_URL=$(aws elasticbeanstalk describe-environments \
        --environment-names ducktickets-hml \
        --query 'Environments[0].EndpointURL' \
        --output text)
    echo "   🌐 URL: http://$EB_URL"
elif [ "$EB_STATUS" = "NotFound" ]; then
    echo "   ❌ Terminated/Not Created"
else
    echo "   ⏳ Status: $EB_STATUS"
fi

# Check RDS
echo ""
echo "🗄️ RDS Database:"
DB_STATUS=$(aws rds describe-db-instances \
    --db-instance-identifier ducktickets-hml-db \
    --query 'DBInstances[0].DBInstanceStatus' \
    --output text 2>/dev/null || echo "NotFound")

if [ "$DB_STATUS" = "available" ]; then
    echo "   ✅ Running"
elif [ "$DB_STATUS" = "stopped" ]; then
    echo "   ⏸️ Stopped"
elif [ "$DB_STATUS" = "NotFound" ]; then
    echo "   ❌ Not Found"
else
    echo "   ⏳ Status: $DB_STATUS"
fi

# Check S3
echo ""
echo "📦 S3 Bucket:"
S3_BUCKET=$(terraform output -raw s3_bucket 2>/dev/null || echo "unknown")
if [ "$S3_BUCKET" != "unknown" ]; then
    S3_EXISTS=$(aws s3 ls s3://$S3_BUCKET 2>/dev/null && echo "exists" || echo "not-found")
    if [ "$S3_EXISTS" = "exists" ]; then
        echo "   ✅ Active: $S3_BUCKET"
    else
        echo "   ❌ Not Found: $S3_BUCKET"
    fi
else
    echo "   ❓ Unknown (run terraform output)"
fi

# Check SQS
echo ""
echo "📨 SQS Queue:"
SQS_URL=$(terraform output -raw sqs_queue_url 2>/dev/null || echo "unknown")
if [ "$SQS_URL" != "unknown" ]; then
    SQS_EXISTS=$(aws sqs get-queue-attributes --queue-url "$SQS_URL" 2>/dev/null && echo "exists" || echo "not-found")
    if [ "$SQS_EXISTS" = "exists" ]; then
        echo "   ✅ Active"
    else
        echo "   ❌ Not Found"
    fi
else
    echo "   ❓ Unknown (run terraform output)"
fi

# Cost estimation
echo ""
echo "💰 Current Estimated Cost:"
if [ "$EB_STATUS" = "Ready" ] && [ "$DB_STATUS" = "available" ]; then
    echo "   💸 ~$25-35/month (fully running)"
elif [ "$EB_STATUS" = "NotFound" ] && [ "$DB_STATUS" = "stopped" ]; then
    echo "   💰 ~$4/month (infrastructure stopped)"
elif [ "$EB_STATUS" = "NotFound" ] && [ "$DB_STATUS" = "available" ]; then
    echo "   💸 ~$18/month (EB stopped, RDS running)"
else
    echo "   ❓ Variable (mixed states)"
fi

echo ""
echo "🎛️ Available Commands:"
echo "   ./start.sh  - Start infrastructure"
echo "   ./stop.sh   - Stop infrastructure"
echo "   ./status.sh - Check status (this command)"