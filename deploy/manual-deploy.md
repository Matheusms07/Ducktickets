# 🚀 Manual Deploy Guide

## 📋 Deploy Steps

### 1. **Connect to EC2**
```bash
# Get EC2 IP
EC2_IP=$(cd terraform && terraform output -raw ec2_public_ip)
echo "EC2 IP: $EC2_IP"

# Connect (may need to wait for instance to be ready)
ssh -o StrictHostKeyChecking=no ec2-user@$EC2_IP
```

### 2. **Setup Application**
```bash
# Update system
sudo yum update -y

# Install dependencies
sudo yum install -y python3.11 python3.11-pip git nginx

# Create app user
sudo useradd -m -s /bin/bash ducktickets
sudo usermod -aG wheel ducktickets

# Create app directory
sudo mkdir -p /opt/ducktickets/app
sudo chown -R ducktickets:ducktickets /opt/ducktickets

# Clone repository
cd /opt/ducktickets
sudo -u ducktickets git clone https://github.com/Matheusms07/Ducktickets.git app
```

### 3. **Install Python Dependencies**
```bash
cd /opt/ducktickets/app
sudo -u ducktickets python3.11 -m pip install --user -r requirements.txt
sudo -u ducktickets python3.11 -m pip install --user gunicorn psycopg2-binary PyJWT passlib[bcrypt] bleach
```

### 4. **Configure Environment**
```bash
# Get database info
DB_PASSWORD="903*#UTP(?d7a>#XT?4uYrBDk2bq{ZQS"
DB_ENDPOINT="ducktickets-db-hml.c8qg8qg8qg8q.us-east-1.rds.amazonaws.com"

# Create environment file
sudo tee /opt/ducktickets/.env > /dev/null << EOF
ENVIRONMENT=homologation
DATABASE_URL=postgresql://ducktickets:$DB_PASSWORD@$DB_ENDPOINT/ducktickets
SECRET_KEY=$(openssl rand -base64 32)
AWS_REGION=us-east-1
S3_BUCKET=ducktickets-s3-hml-a52f3678
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/243429551092/ducktickets-sqs-hml
DEBUG=false
ALLOWED_ORIGINS=http://35.173.219.67
EOF
```

### 5. **Create Systemd Service**
```bash
sudo tee /etc/systemd/system/ducktickets.service > /dev/null << 'EOF'
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
EOF
```

### 6. **Configure Nginx**
```bash
sudo tee /etc/nginx/conf.d/ducktickets.conf > /dev/null << 'EOF'
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
EOF
```

### 7. **Run Migrations & Create Admin**
```bash
cd /opt/ducktickets/app
sudo -u ducktickets /home/ducktickets/.local/bin/python3.11 -m alembic upgrade head
sudo -u ducktickets /home/ducktickets/.local/bin/python3.11 scripts/create_admin.py
```

### 8. **Start Services**
```bash
sudo systemctl enable nginx
sudo systemctl start nginx
sudo systemctl daemon-reload
sudo systemctl enable ducktickets
sudo systemctl start ducktickets
```

### 9. **Check Status**
```bash
sudo systemctl status ducktickets
sudo systemctl status nginx
sudo journalctl -u ducktickets -f
```

## 🌐 **Access Application**
- **URL**: http://35.173.219.67
- **Admin**: super_admin@ducktickets.com / 12qwaszx

## 🔧 **Troubleshooting**
```bash
# Check logs
sudo journalctl -u ducktickets -f
sudo journalctl -u nginx -f

# Restart services
sudo systemctl restart ducktickets
sudo systemctl restart nginx

# Check ports
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :80
```