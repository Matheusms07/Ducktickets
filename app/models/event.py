from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, DECIMAL
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    location = Column(String(500))
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    banner_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    max_attendees = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ticket_batches = relationship("TicketBatch", back_populates="event")
    orders = relationship("Order", back_populates="event")