import hashlib
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, Text
from ..database import Base

class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    
    key = Column(String(255), primary_key=True)
    response_data = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

def generate_idempotency_key(user_id: str, event_id: int, data: dict) -> str:
    """Generate idempotency key for order creation"""
    content = f"{user_id}:{event_id}:{str(sorted(data.items()))}"
    return hashlib.sha256(content.encode()).hexdigest()

def check_idempotency(db: Session, key: str) -> dict:
    """Check if operation was already performed"""
    record = db.query(IdempotencyKey).filter(
        IdempotencyKey.key == key,
        IdempotencyKey.expires_at > datetime.utcnow()
    ).first()
    
    if record:
        return {"exists": True, "data": record.response_data}
    return {"exists": False}

def store_idempotency(db: Session, key: str, response_data: str, ttl_hours: int = 24):
    """Store idempotency result"""
    expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
    
    record = IdempotencyKey(
        key=key,
        response_data=response_data,
        expires_at=expires_at
    )
    
    db.merge(record)
    db.commit()