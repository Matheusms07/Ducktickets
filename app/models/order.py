from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from ..database import Base

class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    user_id = Column(String(255))  # Cognito user ID
    email = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50))
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    status = Column(String(50), default=OrderStatus.PENDING)
    idempotency_key = Column(String(255), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    event = relationship("Event", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order")
    attendees = relationship("Attendee", back_populates="order")
    payments = relationship("Payment", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    ticket_batch_id = Column(Integer, ForeignKey("ticket_batches.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(10, 2), nullable=False)
    total_price = Column(DECIMAL(10, 2), nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    ticket_batch = relationship("TicketBatch", back_populates="order_items")