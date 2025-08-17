# 💰 AWS Cost Optimization - DuckTickets HML

## 🎯 Target: ~$25-35/month

### 📊 Resource Configuration

#### **EC2 (Elastic Beanstalk)**
- **Instance**: t3.micro (1 vCPU, 1GB RAM)
- **Cost**: ~$8.50/month
- **Config**: Single instance (no load balancer)
- **Auto Scaling**: 1-2 instances max

#### **RDS PostgreSQL**
- **Instance**: db.t3.micro (1 vCPU, 1GB RAM)
- **Storage**: 20GB GP2
- **Cost**: ~$15-18/month
- **Config**: Single-AZ, 1-day backup retention

#### **S3 Storage**
- **Usage**: Static files, uploads
- **Cost**: ~$1-2/month
- **Config**: Standard storage class

#### **SQS**
- **Usage**: Background tasks
- **Cost**: ~$0.50/month
- **Config**: Standard queue

#### **CloudWatch Logs**
- **Retention**: 7 days
- **Cost**: ~$1-2/month

### 🔧 Cost Optimization Settings

#### **Elastic Beanstalk**
```yaml
# .ebextensions/03_environment.config
option_settings:
  aws:autoscaling:launchconfiguration:
    InstanceType: t3.micro
  aws:autoscaling:asg:
    MinSize: 1
    MaxSize: 2
  aws:elasticbeanstalk:environment:
    EnvironmentType: LoadBalanced  # Changed to single instance
```

#### **RDS**
```bash
# Low-cost RDS settings
--db-instance-class db.t3.micro
--allocated-storage 20
--storage-type gp2
--no-multi-az
--backup-retention-period 1
```

### 📈 Monitoring & Alerts

#### **CloudWatch Alarms**
- CPU > 80% for 5 minutes
- Database connections > 80%
- Disk space < 20%

#### **Cost Alerts**
- Monthly budget: $40
- Alert at 80% ($32)
- Alert at 100% ($40)

### 🚀 Deployment Commands

```bash
# 1. Setup AWS resources
chmod +x deploy/aws-setup.sh
./deploy/aws-setup.sh

# 2. Deploy application
eb deploy

# 3. Run database migrations
eb ssh
cd /var/app/current
python -m alembic upgrade head

# 4. Create admin user
python scripts/create_admin.py
```

### 📋 Post-Deployment Checklist

- [ ] Application accessible via EB URL
- [ ] Database connected and migrated
- [ ] Admin user created
- [ ] Health check passing
- [ ] Logs streaming to CloudWatch
- [ ] Cost alerts configured

### ⚠️ Important Notes

1. **Free Tier**: If account is < 12 months old, EC2 t3.micro is free
2. **RDS**: Biggest cost component (~60% of total)
3. **Scaling**: Auto-scales to 2 instances under load
4. **Backups**: Only 1-day retention to minimize costs
5. **Monitoring**: 7-day log retention only

### 🔄 Cleanup Commands

```bash
# Delete environment
eb terminate ducktickets-hml

# Delete RDS
aws rds delete-db-instance \
    --db-instance-identifier ducktickets-hml-db \
    --skip-final-snapshot

# Delete S3 bucket
aws s3 rb s3://bucket-name --force

# Delete SQS queue
aws sqs delete-queue --queue-url QUEUE_URL
```