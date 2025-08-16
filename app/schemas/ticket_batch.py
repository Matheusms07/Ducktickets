from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional

class TicketBatchBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    quantity: int
    sale_start: datetime
    sale_end: datetime

class TicketBatchCreate(TicketBatchBase):
    event_id: int

class TicketBatchUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    quantity: Optional[int] = None
    sale_start: Optional[datetime] = None
    sale_end: Optional[datetime] = None
    is_active: Optional[bool] = None

class TicketBatchResponse(TicketBatchBase):
    id: int
    event_id: int
    sold_quantity: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True