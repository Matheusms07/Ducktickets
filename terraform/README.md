# 🦆 DuckTickets - Terraform Infrastructure

## 🚀 Quick Deploy

```bash
cd terraform
chmod +x deploy.sh destroy.sh
./deploy.sh
```

## 📋 What Gets Created

### 💰 Cost-Optimized Resources
- **Elastic Beanstalk**: t3.micro single instance
- **RDS PostgreSQL**: db.t3.micro, 20GB storage
- **S3 Bucket**: Standard storage
- **SQS Queue**: Standard queue

### 💸 Estimated Cost: $25-35/month
- **Free Tier**: $8-15/month (first year)

## 🔧 Manual Commands

### Deploy
```bash
terraform init
terraform plan
terraform apply
```

### Get Outputs
```bash
terraform output
terraform output -raw database_password
```

### Destroy
```bash
terraform destroy
# or
./destroy.sh
```

## 📊 Outputs

- `eb_environment_url`: Application URL
- `database_endpoint`: RDS endpoint
- `database_password`: DB password (sensitive)
- `s3_bucket`: Bucket name
- `sqs_queue_url`: Queue URL

## 🔐 Security

- RDS password auto-generated
- Secret key auto-generated
- S3 bucket versioning enabled
- CloudWatch logs (7-day retention)

## 📝 Post-Deploy Steps

1. **Wait for RDS** (~10 minutes)
2. **Deploy code** to Elastic Beanstalk
3. **Run migrations**:
   ```bash
   eb ssh
   cd /var/app/current
   python -m alembic upgrade head
   ```
4. **Create admin user**:
   ```bash
   python scripts/create_admin.py
   ```

## 🎛️ Infrastructure Control

### Start/Stop (Save Money)
```bash
./stop.sh    # Stop everything (~$4/month)
./start.sh   # Start everything (~$25/month)
./status.sh  # Check current status
```

### Automatic Scheduling
```bash
./schedule-stop.sh  # Auto stop nights/weekends
```
**Saves ~$200-300/month with automatic scheduling!**

### Complete Cleanup
```bash
./destroy.sh  # Destroy everything permanently
```