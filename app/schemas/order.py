from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

class OrderItemCreate(BaseModel):
    ticket_batch_id: int
    quantity: int

class OrderCreate(BaseModel):
    event_id: int
    email: str
    full_name: str
    phone: Optional[str] = None
    items: List[OrderItemCreate]

class OrderItemResponse(BaseModel):
    id: int
    ticket_batch_id: int
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    
    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    event_id: int
    email: str
    full_name: str
    phone: Optional[str] = None
    total_amount: Decimal
    status: str
    created_at: datetime
    order_items: List[OrderItemResponse]
    
    class Config:
        from_attributes = True