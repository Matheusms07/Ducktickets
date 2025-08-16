from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db
import boto3
from ..config import settings

router = APIRouter()

@router.get("/healthz")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint for load balancer"""
    try:
        # Check database
        db.execute(text("SELECT 1"))
        
        # Check SQS (optional)
        sqs_status = "ok"
        if settings.sqs_queue_url:
            try:
                sqs = boto3.client('sqs', region_name=settings.aws_region)
                sqs.get_queue_attributes(QueueUrl=settings.sqs_queue_url)
            except Exception:
                sqs_status = "error"
        
        return {
            "status": "healthy",
            "database": "ok",
            "sqs": sqs_status,
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }