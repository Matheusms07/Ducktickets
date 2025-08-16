from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AttendeeResponse(BaseModel):
    id: int
    order_id: int
    ticket_batch_id: int
    full_name: str
    email: str
    phone: Optional[str] = None
    qr_code: str
    is_checked_in: bool
    checked_in_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True