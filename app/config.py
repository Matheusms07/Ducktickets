from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://user:pass@localhost/ducktickets"
    
    # AWS
    aws_region: str = "us-east-1"
    s3_bucket: str = "ducktickets-assets"
    sqs_queue_url: str = ""
    sqs_dlq_url: str = ""
    
    # Cognito
    cognito_user_pool_id: str = ""
    cognito_client_id: str = ""
    cognito_region: str = "us-east-1"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    allowed_origins: str = "https://yourdomain.com"
    
    # Mercado Pago
    mercado_pago_access_token: str = ""
    mercado_pago_webhook_secret: str = ""
    
    # SES
    ses_sender_email: str = "noreply@yourdomain.com"
    
    # Redis (optional for rate limiting)
    redis_url: Optional[str] = None
    
    # Environment
    environment: str = "development"
    debug: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()