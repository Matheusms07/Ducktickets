from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class TicketBatch(Base):
    __tablename__ = "ticket_batches"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    price = Column(DECIMAL(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    sold_quantity = Column(Integer, default=0)
    sale_start = Column(DateTime, nullable=False)
    sale_end = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    requires_coupon = Column(Boolean, default=False)  # Novo campo
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    event = relationship("Event", back_populates="ticket_batches")
    order_items = relationship("OrderItem", back_populates="ticket_batch")
    coupons = relationship("Coupon", back_populates="ticket_batch")