#!/bin/bash
# Deploy script for DuckTickets

set -e

echo "🚀 Starting deployment..."

# Get instance ID
INSTANCE_ID=$(cd terraform && terraform output -raw ec2_instance_id 2>/dev/null || echo "i-0a84147a29fef2f37")

echo "📦 Deploying to instance: $INSTANCE_ID"

# Create deployment commands
cat > /tmp/deploy_commands.sh << 'EOF'
#!/bin/bash
set -e

echo "📥 Pulling latest code..."
cd /opt/ducktickets/app
sudo -u ducktickets git pull origin main

echo "🔧 Installing dependencies if needed..."
sudo -u ducktickets python3 -m pip install --user -r requirements.txt --quiet

echo "🗄️ Running migrations..."
sudo -u ducktickets /home/ducktickets/.local/bin/python3 -m alembic upgrade head

echo "🔄 Restarting application..."
sudo systemctl restart ducktickets

echo "✅ Checking application status..."
sleep 5
sudo systemctl status ducktickets --no-pager -l

echo "🎉 Deployment completed!"
EOF

# Copy and execute on instance
echo "📤 Uploading deployment script..."
aws ssm send-command \
    --instance-ids "$INSTANCE_ID" \
    --document-name "AWS-RunShellScript" \
    --parameters 'commands=["'"$(cat /tmp/deploy_commands.sh | base64 -w 0)"'" | base64 -d | bash]' \
    --output text --query 'Command.CommandId'

echo "✅ Deployment initiated! Check AWS Systems Manager for progress."

# Cleanup
rm /tmp/deploy_commands.sh