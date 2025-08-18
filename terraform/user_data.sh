#!/bin/bash
# DuckTickets EC2 Production Setup Script

# Update system
yum update -y

# Install dependencies
yum install -y python3 python3-pip git amazon-cloudwatch-agent
amazon-linux-extras install nginx1 -y

# Create app user
useradd -m -s /bin/bash ducktickets
usermod -aG wheel ducktickets

# Create app directory
mkdir -p /opt/ducktickets/app
chown -R ducktickets:ducktickets /opt/ducktickets

# Clone repository and setup
cd /opt/ducktickets
sudo -u ducktickets git clone https://github.com/Matheusms07/Ducktickets.git app

# Get public IP for CORS
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

# Set up environment variables
if [ "${domain_name}" != "" ]; then
    if [ "${environment}" = "prod" ]; then
        DOMAIN_URL="https://${domain_name}"
    else
        DOMAIN_URL="https://${environment}.${domain_name}"
    fi
    ALLOWED_ORIGINS="$DOMAIN_URL,http://$PUBLIC_IP"
else
    ALLOWED_ORIGINS="http://$PUBLIC_IP"
fi

# Create .env in the correct location (app directory)
cat > /opt/ducktickets/app/.env << EOF
ENVIRONMENT=${environment}
DATABASE_URL=${database_url}
SECRET_KEY=${secret_key}$(openssl rand -base64 16)
AWS_REGION=${aws_region}
S3_BUCKET=${s3_bucket}
SQS_QUEUE_URL=${sqs_queue_url}
DEBUG=false
ALLOWED_ORIGINS=$ALLOWED_ORIGINS
EOF

# Set correct ownership
chown ducktickets:ducktickets /opt/ducktickets/app/.env

# Install Python dependencies (compatible versions for Python 3.7)
cd /opt/ducktickets/app
sudo -u ducktickets python3 -m pip install --user --upgrade pip

# Core FastAPI dependencies
sudo -u ducktickets python3 -m pip install --user fastapi==0.103.2 uvicorn[standard]==0.24.0 gunicorn==21.2.0

# Database dependencies
sudo -u ducktickets python3 -m pip install --user sqlalchemy==2.0.23 alembic==1.12.1 psycopg2-binary==2.9.9

# Pydantic and settings (Python 3.7 compatible)
sudo -u ducktickets python3 -m pip install --user pydantic==2.5.3 pydantic-settings==2.0.3

# Authentication and security
sudo -u ducktickets python3 -m pip install --user python-jose[cryptography]==3.3.0 PyJWT passlib[bcrypt] bleach

# Web dependencies
sudo -u ducktickets python3 -m pip install --user python-multipart==0.0.6 jinja2==3.1.2

# AWS and external services (Python 3.7 compatible)
sudo -u ducktickets python3 -m pip install --user boto3==1.33.13 aws-xray-sdk==2.12.1

# Payment and QR codes
sudo -u ducktickets python3 -m pip install --user mercadopago==2.2.1 qrcode[pil]==7.4.2

# Rate limiting and logging (Python 3.7 compatible)
sudo -u ducktickets python3 -m pip install --user slowapi==0.1.9 structlog==23.1.0

# Cache (Redis)
sudo -u ducktickets python3 -m pip install --user redis==5.0.1

# Verify installation
sudo -u ducktickets python3 -c "import fastapi, sqlalchemy, boto3, slowapi; print('All dependencies OK')"

# Fix pydantic import issue
sed -i 's/from pydantic import BaseSettings, validator/from pydantic_settings import BaseSettings\nfrom pydantic import validator/' /opt/ducktickets/app/app/config_environments.py

# Fix auth import issue
sed -i 's/auth_manager.get_current_user/get_current_user/' /opt/ducktickets/app/app/routes/auth.py
sed -i '/from ..auth import auth_manager/a from ..auth import get_current_user' /opt/ducktickets/app/app/routes/auth.py

# Run database migrations
sudo -u ducktickets /home/ducktickets/.local/bin/python3 -m alembic upgrade head

# Create admin user
sudo -u ducktickets /home/ducktickets/.local/bin/python3 scripts/create_admin.py

# Create systemd service
cat > /etc/systemd/system/ducktickets.service << 'EOF'
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
ExecStart=/home/ducktickets/.local/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx with SSL ready
cat > /etc/nginx/conf.d/ducktickets.conf << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /static/ {
        alias /opt/ducktickets/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/healthz;
        access_log off;
    }
}
EOF

# Enable and start services
systemctl daemon-reload
systemctl enable nginx
systemctl start nginx
systemctl enable ducktickets
systemctl start ducktickets

# Create deployment script
cat > /opt/ducktickets/deploy.sh << 'DEPLOY_EOF'
#!/bin/bash
set -e
cd /opt/ducktickets/app
sudo -u ducktickets git pull origin main
sudo -u ducktickets /home/ducktickets/.local/bin/python3 -m pip install --user -r requirements.txt
sudo -u ducktickets /home/ducktickets/.local/bin/python3 -m alembic upgrade head
sudo systemctl restart ducktickets
echo "Deployment completed successfully!"
DEPLOY_EOF

chmod +x /opt/ducktickets/deploy.sh
chown ducktickets:ducktickets /opt/ducktickets/deploy.sh

# Setup log rotation
cat > /etc/logrotate.d/ducktickets << 'LOGROTATE_EOF'
/var/log/ducktickets/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ducktickets ducktickets
    postrotate
        systemctl reload ducktickets
    endscript
}
LOGROTATE_EOF

# Create log directory
mkdir -p /var/log/ducktickets
chown ducktickets:ducktickets /var/log/ducktickets

# Log completion
echo "✅ DuckTickets Setup Completed!" | tee -a /var/log/ducktickets-setup.log
echo "🌐 Application available at: http://$PUBLIC_IP" | tee -a /var/log/ducktickets-setup.log
echo "🔑 Admin: super_admin@ducktickets.com / 12qwaszx" | tee -a /var/log/ducktickets-setup.log

# Send completion notification to CloudWatch
aws logs create-log-group --log-group-name /aws/ec2/ducktickets --region ${aws_region} 2>/dev/null || true
aws logs create-log-stream --log-group-name /aws/ec2/ducktickets --log-stream-name $(hostname) --region ${aws_region} 2>/dev/null || true
aws logs put-log-events --log-group-name /aws/ec2/ducktickets --log-stream-name $(hostname) --log-events timestamp=$(date +%s000),message="DuckTickets deployment completed successfully on $PUBLIC_IP" --region ${aws_region} 2>/dev/null || true