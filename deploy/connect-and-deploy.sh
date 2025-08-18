#!/bin/bash
# Connect and Deploy to EC2

EC2_IP="35.173.219.67"
DB_PASSWORD="903*#UTP(?d7a>#XT?4uYrBDk2bq{ZQS"
DB_ENDPOINT="ducktickets-db-hml.ci1ow6ogmtx7.us-east-1.rds.amazonaws.com:5432"

echo "🦆 DuckTickets - Manual Deploy Instructions"
echo "==========================================="
echo ""
echo "📋 Copy and paste these commands in your terminal:"
echo ""
echo "# 1. Connect to EC2"
echo "ssh -o StrictHostKeyChecking=no ec2-user@$EC2_IP"
echo ""
echo "# 2. Once connected, run these commands:"
echo ""
cat << 'COMMANDS'
# Update system
sudo yum update -y

# Install dependencies
sudo yum install -y python3.11 python3.11-pip git nginx

# Create app user
sudo useradd -m -s /bin/bash ducktickets 2>/dev/null || true

# Create app directory
sudo mkdir -p /opt/ducktickets/app
sudo chown -R ducktickets:ducktickets /opt/ducktickets

# Clone repository
cd /opt/ducktickets
sudo -u ducktickets git clone https://github.com/Matheusms07/Ducktickets.git app

# Install Python dependencies
cd /opt/ducktickets/app
sudo -u ducktickets python3.11 -m pip install --user -r requirements.txt
sudo -u ducktickets python3.11 -m pip install --user gunicorn psycopg2-binary PyJWT passlib[bcrypt] bleach

# Create environment file
COMMANDS

echo "sudo tee /opt/ducktickets/.env > /dev/null << 'ENV'"
echo "ENVIRONMENT=homologation"
echo "DATABASE_URL=postgresql://ducktickets:$DB_PASSWORD@$DB_ENDPOINT/ducktickets"
echo "SECRET_KEY=\$(openssl rand -base64 32)"
echo "AWS_REGION=us-east-1"
echo "S3_BUCKET=ducktickets-s3-hml-a52f3678"
echo "SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/243429551092/ducktickets-sqs-hml"
echo "DEBUG=false"
echo "ALLOWED_ORIGINS=http://$EC2_IP"
echo "ENV"
echo ""

cat << 'COMMANDS2'
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

# Check status
sudo systemctl status ducktickets
sudo systemctl status nginx

echo "✅ Deployment completed!"
echo "🌐 Application available at: http://35.173.219.67"
echo "🔑 Admin login: super_admin@ducktickets.com / 12qwaszx"
COMMANDS2

echo ""
echo "🌐 After deployment, access: http://$EC2_IP"
echo "🔑 Admin login: super_admin@ducktickets.com / 12qwaszx"