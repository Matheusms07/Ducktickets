#!/bin/bash
# Deploy DuckTickets to EC2

set -e

# Get EC2 info from Terraform
EC2_IP=$(cd terraform && terraform output -raw ec2_public_ip)
DB_PASSWORD=$(cd terraform && terraform output -raw database_password)
DB_ENDPOINT=$(cd terraform && terraform output -raw database_endpoint)

echo "🦆 DuckTickets - Deploy to EC2"
echo "=============================="
echo "EC2 IP: $EC2_IP"

# Wait for EC2 to be ready
echo "⏳ Waiting for EC2 to be ready..."
sleep 30

# Create deployment package
echo "📦 Creating deployment package..."
tar -czf ducktickets-deploy.tar.gz \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='terraform' \
  --exclude='deploy' \
  --exclude='ducktickets.db' \
  .

# Copy files to EC2
echo "📤 Uploading files to EC2..."
scp -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa ducktickets-deploy.tar.gz ec2-user@$EC2_IP:/tmp/ || {
  echo "❌ SCP failed. Trying without key..."
  scp -o StrictHostKeyChecking=no ducktickets-deploy.tar.gz ec2-user@$EC2_IP:/tmp/
}

# Deploy on EC2
echo "🚀 Deploying on EC2..."
ssh -o StrictHostKeyChecking=no ec2-user@$EC2_IP << EOF
  # Extract files
  sudo rm -rf /opt/ducktickets/app
  sudo mkdir -p /opt/ducktickets/app
  cd /opt/ducktickets/app
  sudo tar -xzf /tmp/ducktickets-deploy.tar.gz
  sudo chown -R ducktickets:ducktickets /opt/ducktickets

  # Update environment
  sudo tee /opt/ducktickets/.env > /dev/null << ENV
ENVIRONMENT=homologation
DATABASE_URL=postgresql://ducktickets:$DB_PASSWORD@$DB_ENDPOINT/ducktickets
SECRET_KEY=$(openssl rand -base64 32)
AWS_REGION=us-east-1
S3_BUCKET=ducktickets-s3-hml-a52f3678
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/243429551092/ducktickets-sqs-hml
DEBUG=false
ALLOWED_ORIGINS=http://$EC2_IP,http://ec2-35-173-219-67.compute-1.amazonaws.com
ENV

  # Install dependencies
  cd /opt/ducktickets/app
  sudo -u ducktickets python3.11 -m pip install --user -r requirements.txt
  sudo -u ducktickets python3.11 -m pip install --user gunicorn psycopg2-binary

  # Run migrations
  sudo -u ducktickets python3.11 -m alembic upgrade head

  # Create admin user
  sudo -u ducktickets python3.11 scripts/create_admin.py

  # Start services
  sudo systemctl daemon-reload
  sudo systemctl enable ducktickets
  sudo systemctl start ducktickets
  sudo systemctl restart nginx

  echo "✅ Deploy completed!"
EOF

# Cleanup
rm ducktickets-deploy.tar.gz

echo ""
echo "🎉 Deploy Complete!"
echo "=================="
echo "🌐 Application URL: http://$EC2_IP"
echo "🔑 Admin Login: super_admin@ducktickets.com / 12qwaszx"
echo ""
echo "📋 Next Steps:"
echo "1. Test the application"
echo "2. Check logs: ssh ec2-user@$EC2_IP 'sudo journalctl -u ducktickets -f'"
echo "3. Monitor status: ssh ec2-user@$EC2_IP 'sudo systemctl status ducktickets'"