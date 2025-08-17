"""
Environment-specific configuration
"""
import os
from typing import Optional
from pydantic import BaseSettings, validator

class BaseConfig(BaseSettings):
    """Base configuration"""
    
    # App
    app_name: str = "DuckTickets"
    version: str = "1.0.0"
    debug: bool = False
    
    # Security
    secret_key: str
    allowed_origins: str = "http://localhost:8000"
    
    # Database
    database_url: str
    
    # AWS
    aws_region: str = "us-east-1"
    s3_bucket: Optional[str] = None
    sqs_queue_url: Optional[str] = None
    
    # External Services
    mercado_pago_access_token: Optional[str] = None
    ses_sender_email: Optional[str] = None
    
    # Rate Limiting
    rate_limit_calls: int = 100
    rate_limit_period: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = False

class DevelopmentConfig(BaseConfig):
    """Development configuration"""
    debug: bool = True
    environment: str = "development"
    
    # Relaxed security for development
    allowed_origins: str = "http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000"
    
    # Higher rate limits for development
    rate_limit_calls: int = 1000
    rate_limit_period: int = 60
    
    @validator('secret_key', pre=True)
    def validate_secret_key(cls, v):
        if not v or v == "test-secret-key-local-only":
            return "dev-secret-key-not-for-production-use-only"
        return v

class HomologationConfig(BaseConfig):
    """Homologation/Staging configuration"""
    debug: bool = False
    environment: str = "homologation"
    
    # Moderate security for testing
    rate_limit_calls: int = 200
    rate_limit_period: int = 60
    
    @validator('secret_key', pre=True)
    def validate_secret_key(cls, v):
        if not v or len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters for homologation")
        return v
    
    @validator('database_url', pre=True)
    def validate_database_url(cls, v):
        if not v or "sqlite" in v:
            raise ValueError("Homologation must use PostgreSQL database")
        return v

class ProductionConfig(BaseConfig):
    """Production configuration"""
    debug: bool = False
    environment: str = "production"
    
    # Strict security for production
    rate_limit_calls: int = 100
    rate_limit_period: int = 60
    
    @validator('secret_key', pre=True)
    def validate_secret_key(cls, v):
        if not v or len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters for production")
        if v in ["test-secret-key-local-only", "dev-secret-key-not-for-production-use-only"]:
            raise ValueError("Cannot use development secret key in production")
        return v
    
    @validator('database_url', pre=True)
    def validate_database_url(cls, v):
        if not v or "sqlite" in v:
            raise ValueError("Production must use PostgreSQL database")
        return v
    
    @validator('allowed_origins', pre=True)
    def validate_allowed_origins(cls, v):
        if "localhost" in v or "127.0.0.1" in v:
            raise ValueError("Production cannot allow localhost origins")
        return v

def get_config() -> BaseConfig:
    """Get configuration based on environment"""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    config_map = {
        "development": DevelopmentConfig,
        "dev": DevelopmentConfig,
        "homologation": HomologationConfig,
        "hml": HomologationConfig,
        "staging": HomologationConfig,
        "production": ProductionConfig,
        "prod": ProductionConfig,
    }
    
    config_class = config_map.get(environment, DevelopmentConfig)
    return config_class()

# Global settings instance
settings = get_config()