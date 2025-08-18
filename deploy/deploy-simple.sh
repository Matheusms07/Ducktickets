#!/bin/bash
# Simple Deploy via AWS Systems Manager

set -e

# Get EC2 info
EC2_IP=$(cd terraform && terraform output -raw ec2_public_ip)
EC2_INSTANCE_ID=$(cd terraform && terraform show -json | jq -r '.values.root_module.resources[] | select(.type=="aws_instance") | .values.id')
DB_PASSWORD=$(cd terraform && terraform output -raw database_password)
DB_ENDPOINT=$(cd terraform && terraform output -raw database_endpoint)

echo "🦆 DuckTickets - Deploy via SSM"
echo "==============================="
echo "EC2 IP: $EC2_IP"
echo "Instance ID: $EC2_INSTANCE_ID"

# Create deployment script
cat > /tmp/deploy-commands.sh << 'DEPLOY_SCRIPT'
#!/bin/bash
set -e

# Update system
sudo yum update -y

# Install dependencies
sudo yum install -y python3.11 python3.11-pip git nginx

# Create app user if not exists
sudo useradd -m -s /bin/bash ducktickets || true
sudo usermod -aG wheel ducktickets || true

# Create app directory
sudo mkdir -p /opt/ducktickets/app
sudo chown -R ducktickets:ducktickets /opt/ducktickets

# Clone repository
cd /opt/ducktickets
sudo -u ducktickets git clone https://github.com/Matheusms07/Ducktickets.git app || {
  cd app
  sudo -u ducktickets git pull origin main
}

# Install Python dependencies
cd /opt/ducktickets/app
sudo -u ducktickets python3.11 -m pip install --user -r requirements.txt
sudo -u ducktickets python3.11 -m pip install --user gunicorn psycopg2-binary PyJWT passlib[bcrypt] bleach

# Create environment file
sudo tee /opt/ducktickets/.env > /dev/null << 'ENV'
ENVIRONMENT=homologation
DATABASE_URL=PLACEHOLDER_DB_URL
SECRET_KEY=PLACEHOLDER_SECRET
AWS_REGION=us-east-1
S3_BUCKET=ducktickets-s3-hml-a52f3678
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/243429551092/ducktickets-sqs-hml
DEBUG=false
ALLOWED_ORIGINS=http://PLACEHOLDER_IP
ENV

# Create systemd service
sudo tee /etc/systemd/system/ducktickets.service > /dev/null << 'SERVICE'
[Unit]
Description=DuckTickets FastAPI Application
After=network.target

[Service]
Type=simple
User=ducktickets
Group=ducktickets
WorkingDirectory=/opt/ducktickets/app
Environment=PATH=/home/ducktickets/.local/bin:/usr/bin
EnvironmentFile=/opt/ducktickets/.env
ExecStart=/home/ducktickets/.local/bin/gunicorn app.main:app -w 2 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICE

# Configure Nginx
sudo tee /etc/nginx/conf.d/ducktickets.conf > /dev/null << 'NGINX'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/ducktickets/app/static/;
    }
}
NGINX

# Enable services
sudo systemctl enable nginx
sudo systemctl start nginx
sudo systemctl daemon-reload
sudo systemctl enable ducktickets

echo "✅ Setup completed!"
DEPLOY_SCRIPT

# Replace placeholders and execute
sed -i.bak "s|PLACEHOLDER_DB_URL|postgresql://ducktickets:$DB_PASSWORD@$DB_ENDPOINT/ducktickets|g" /tmp/deploy-commands.sh
sed -i.bak "s|PLACEHOLDER_SECRET|$(openssl rand -base64 32)|g" /tmp/deploy-commands.sh
sed -i.bak "s|PLACEHOLDER_IP|$EC2_IP|g" /tmp/deploy-commands.sh

# Execute via SSM
echo "🚀 Executing deployment..."
aws ssm send-command \
    --instance-ids $EC2_INSTANCE_ID \
    --document-name "AWS-RunShellScript" \
    --parameters "commands=[\"$(cat /tmp/deploy-commands.sh | base64 -w 0)\"]" \
    --query 'Command.CommandId' \
    --output text > /tmp/command-id.txt

COMMAND_ID=$(cat /tmp/command-id.txt)
echo "Command ID: $COMMAND_ID"

# Wait for completion
echo "⏳ Waiting for deployment to complete..."
aws ssm wait command-executed \
    --command-id $COMMAND_ID \
    --instance-id $EC2_INSTANCE_ID

# Get results
echo "📋 Deployment Results:"
aws ssm get-command-invocation \
    --command-id $COMMAND_ID \
    --instance-id $EC2_INSTANCE_ID \
    --query 'StandardOutputContent' \
    --output text

# Run migrations and create admin
echo "🔧 Running migrations and creating admin..."
aws ssm send-command \
    --instance-ids $EC2_INSTANCE_ID \
    --document-name "AWS-RunShellScript" \
    --parameters 'commands=["cd /opt/ducktickets/app && sudo -u ducktickets /home/ducktickets/.local/bin/python3.11 -m alembic upgrade head && sudo -u ducktickets /home/ducktickets/.local/bin/python3.11 scripts/create_admin.py && sudo systemctl start ducktickets"]' \
    --query 'Command.CommandId' \
    --output text > /tmp/command-id2.txt

COMMAND_ID2=$(cat /tmp/command-id2.txt)
aws ssm wait command-executed --command-id $COMMAND_ID2 --instance-id $EC2_INSTANCE_ID

echo ""
echo "🎉 Deploy Complete!"
echo "=================="
echo "🌐 Application URL: http://$EC2_IP"
echo "🔑 Admin Login: super_admin@ducktickets.com / 12qwaszx"

# Cleanup
rm -f /tmp/deploy-commands.sh /tmp/command-id.txt /tmp/command-id2.txt