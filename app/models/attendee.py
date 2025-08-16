from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class Attendee(Base):
    __tablename__ = "attendees"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    ticket_batch_id = Column(Integer, ForeignKey("ticket_batches.id"), nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50))
    qr_code = Column(String(500), unique=True, index=True)
    is_checked_in = Column(Boolean, default=False)
    checked_in_at = Column(DateTime)
    custom_fields = Column(Text)  # JSON string for custom fields
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    order = relationship("Order", back_populates="attendees")