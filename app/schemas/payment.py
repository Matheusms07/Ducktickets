from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional

class PaymentResponse(BaseModel):
    id: int
    order_id: int
    external_id: Optional[str] = None
    provider: str
    amount: Decimal
    status: str
    payment_method: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True