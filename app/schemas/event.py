from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class EventBase(BaseModel):
    name: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_date: datetime
    end_date: datetime
    banner_url: Optional[str] = None
    max_attendees: Optional[int] = None

class EventCreate(EventBase):
    pass

class EventUpdate(EventBase):
    name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class EventResponse(EventBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True