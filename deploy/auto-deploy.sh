#!/bin/bash
# Auto Deploy DuckTickets to EC2

set -e

# Get info from Terraform
EC2_IP=$(cd terraform && terraform output -raw ec2_public_ip)
DB_PASSWORD=$(cd terraform && terraform output -raw database_password)
DB_ENDPOINT=$(cd terraform && terraform output -raw database_endpoint)

echo "🦆 Auto Deploy DuckTickets"
echo "=========================="
echo "EC2 IP: $EC2_IP"

# Wait for EC2 to be ready
echo "⏳ Waiting for EC2 to be ready..."
sleep 60

# Create complete deployment script
cat > /tmp/full-deploy.sh << EOF
#!/bin/bash
set -e

echo "🔧 Starting deployment..."

# Update system
sudo yum update -y

# Install dependencies
sudo yum install -y python3.11 python3.11-pip git nginx

# Create app user
sudo useradd -m -s /bin/bash ducktickets 2>/dev/null || true
sudo usermod -aG wheel ducktickets

# Create app directory
sudo mkdir -p /opt/ducktickets/app
sudo chown -R ducktickets:ducktickets /opt/ducktickets

# Clone repository
cd /opt/ducktickets
if [ -d "app/.git" ]; then
    cd app
    sudo -u ducktickets git pull origin main
else
    sudo -u ducktickets git clone https://github.com/Matheusms07/Ducktickets.git app
fi

# Install Python dependencies
cd /opt/ducktickets/app
sudo -u ducktickets python3.11 -m pip install --user -r requirements.txt
sudo -u ducktickets python3.11 -m pip install --user gunicorn psycopg2-binary PyJWT passlib[bcrypt] bleach

# Create environment file
sudo tee /opt/ducktickets/.env > /dev/null << 'ENV'
ENVIRONMENT=homologation
DATABASE_URL=postgresql://ducktickets:$DB_PASSWORD@$DB_ENDPOINT/ducktickets
SECRET_KEY=\$(openssl rand -base64 32)
AWS_REGION=us-east-1
S3_BUCKET=ducktickets-s3-hml-a52f3678
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/243429551092/ducktickets-sqs-hml
DEBUG=false
ALLOWED_ORIGINS=http://$EC2_IP
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
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static/ {
        alias /opt/ducktickets/app/static/;
    }
}
NGINX

# Run migrations
cd /opt/ducktickets/app
sudo -u ducktickets /home/ducktickets/.local/bin/python3.11 -m alembic upgrade head

# Create admin user
sudo -u ducktickets /home/ducktickets/.local/bin/python3.11 scripts/create_admin.py

# Start services
sudo systemctl enable nginx
sudo systemctl start nginx
sudo systemctl daemon-reload
sudo systemctl enable ducktickets
sudo systemctl start ducktickets

echo "✅ Deployment completed!"
echo "🌐 Application should be available at: http://$EC2_IP"
echo "🔑 Admin login: super_admin@ducktickets.com / 12qwaszx"
EOF

# Execute deployment
echo "🚀 Executing deployment on EC2..."
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=30 ec2-user@$EC2_IP 'bash -s' < /tmp/full-deploy.sh

# Cleanup
rm /tmp/full-deploy.sh

echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo "🌐 Application URL: http://$EC2_IP"
echo "🔑 Admin Login: super_admin@ducktickets.com / 12qwaszx"
echo ""
echo "📋 Check Status:"
echo "ssh ec2-user@$EC2_IP 'sudo systemctl status ducktickets'"
EOF