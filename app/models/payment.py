from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from ..database import Base

class PaymentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    external_id = Column(String(255), unique=True, index=True)  # MP payment ID
    provider = Column(String(50), default="mercado_pago")
    amount = Column(DECIMAL(10, 2), nullable=False)
    status = Column(String(50), default=PaymentStatus.PENDING)
    payment_method = Column(String(100))
    transaction_data = Column(Text)  # JSON string
    webhook_processed = Column(String(255))  # webhook deduplication
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order = relationship("Order", back_populates="payments")