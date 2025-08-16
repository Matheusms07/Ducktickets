from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class Coupon(Base):
    __tablename__ = "coupons"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    ticket_batch_id = Column(Integer, ForeignKey("ticket_batches.id"), nullable=False)
    discount_percent = Column(DECIMAL(5, 2), default=0)  # 0-100
    discount_amount = Column(DECIMAL(10, 2), default=0)  # valor fixo
    max_uses = Column(Integer, default=1)
    used_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    ticket_batch = relationship("TicketBatch", back_populates="coupons")