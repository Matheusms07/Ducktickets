#!/bin/bash
# Schedule Automatic Stop/Start for DuckTickets HML

set -e

echo "⏰ DuckTickets - Schedule Auto Stop/Start"
echo "========================================="

# Create Lambda function for stopping
cat > lambda_stop.py << 'EOF'
import boto3
import json

def lambda_handler(event, context):
    eb = boto3.client('elasticbeanstalk')
    rds = boto3.client('rds')
    
    try:
        # Stop EB Environment
        eb.terminate_environment(
            EnvironmentName='ducktickets-eb-hml',
            TerminateResources=True
        )
        
        # Stop RDS
        rds.stop_db_instance(
            DBInstanceIdentifier='ducktickets-db-hml'
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps('Infrastructure stopped successfully')
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
EOF

# Create Lambda function for starting
cat > lambda_start.py << 'EOF'
import boto3
import json
import time

def lambda_handler(event, context):
    rds = boto3.client('rds')
    
    try:
        # Start RDS first
        rds.start_db_instance(
            DBInstanceIdentifier='ducktickets-db-hml'
        )
        
        # Wait for RDS to be available
        waiter = rds.get_waiter('db_instance_available')
        waiter.wait(DBInstanceIdentifier='ducktickets-db-hml')
        
        # Note: EB environment needs to be recreated manually
        # as it was terminated, not just stopped
        
        return {
            'statusCode': 200,
            'body': json.dumps('RDS started. Recreate EB environment manually.')
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
EOF

# Create zip files
zip lambda_stop.zip lambda_stop.py
zip lambda_start.zip lambda_start.py

# Create IAM role for Lambda
aws iam create-role \
    --role-name DuckTicketsSchedulerRole \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }' || echo "Role may already exist"

# Attach policies
aws iam attach-role-policy \
    --role-name DuckTicketsSchedulerRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam attach-role-policy \
    --role-name DuckTicketsSchedulerRole \
    --policy-arn arn:aws:iam::aws:policy/ElasticBeanstalkFullAccess

aws iam attach-role-policy \
    --role-name DuckTicketsSchedulerRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonRDSFullAccess

# Get account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create Lambda functions
echo "📦 Creating Lambda functions..."
aws lambda create-function \
    --function-name ducktickets-stop \
    --runtime python3.11 \
    --role arn:aws:iam::$ACCOUNT_ID:role/DuckTicketsSchedulerRole \
    --handler lambda_stop.lambda_handler \
    --zip-file fileb://lambda_stop.zip || echo "Function may already exist"

aws lambda create-function \
    --function-name ducktickets-start \
    --runtime python3.11 \
    --role arn:aws:iam::$ACCOUNT_ID:role/DuckTicketsSchedulerRole \
    --handler lambda_start.lambda_handler \
    --zip-file fileb://lambda_start.zip || echo "Function may already exist"

# Create EventBridge rules
echo "⏰ Creating schedules..."

# Stop at 11 PM UTC (6 PM EST) Monday-Friday
aws events put-rule \
    --name ducktickets-stop-schedule \
    --schedule-expression "cron(0 23 ? * MON-FRI *)" \
    --description "Stop DuckTickets HML at 11 PM UTC weekdays"

# Start at 12 PM UTC (7 AM EST) Monday-Friday  
aws events put-rule \
    --name ducktickets-start-schedule \
    --schedule-expression "cron(0 12 ? * MON-FRI *)" \
    --description "Start DuckTickets HML at 12 PM UTC weekdays"

# Add Lambda permissions for EventBridge
aws lambda add-permission \
    --function-name ducktickets-stop \
    --statement-id allow-eventbridge-stop \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:us-east-1:$ACCOUNT_ID:rule/ducktickets-stop-schedule || echo "Permission may already exist"

aws lambda add-permission \
    --function-name ducktickets-start \
    --statement-id allow-eventbridge-start \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:us-east-1:$ACCOUNT_ID:rule/ducktickets-start-schedule || echo "Permission may already exist"

# Create targets
aws events put-targets \
    --rule ducktickets-stop-schedule \
    --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:$ACCOUNT_ID:function:ducktickets-stop"

aws events put-targets \
    --rule ducktickets-start-schedule \
    --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:$ACCOUNT_ID:function:ducktickets-start"

# Cleanup temp files
rm lambda_stop.py lambda_start.py lambda_stop.zip lambda_start.zip

echo ""
echo "✅ Automatic Scheduling Configured!"
echo "==================================="
echo "📅 Schedule:"
echo "   • STOP: 11 PM UTC (6 PM EST) - Monday to Friday"
echo "   • START: 12 PM UTC (7 AM EST) - Monday to Friday"
echo ""
echo "💰 Cost Savings:"
echo "   • Weekends: Infrastructure stopped (save ~$20/weekend)"
echo "   • Nights: Infrastructure stopped (save ~$10/night)"
echo "   • Monthly savings: ~$200-300"
echo ""
echo "⚠️  Note: EB environment is terminated, not stopped"
echo "   Manual recreation needed after start"