from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
import json
from ..database import get_db
from ..models import Order, Payment
from ..config import settings
from ..rate_limit import limiter

router = APIRouter(prefix="/webhook", tags=["webhook"])

@router.post("/")
@limiter.limit("100/minute")
async def mercado_pago_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Process Mercado Pago webhook (mock for development)"""
    try:
        # Get raw body
        body = await request.body()
        
        # Parse webhook data
        webhook_data = json.loads(body.decode()) if body else {}
        
        # Mock processing for development
        print(f"📨 Webhook received: {webhook_data}")
        
        return {"status": "ok"}
        
    except Exception as e:
        print(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")