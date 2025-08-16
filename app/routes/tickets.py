from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from ..database import get_db
from ..models import Attendee, Order
from ..services.qrcode.generator import verify_qr_payload
from ..security import require_admin

router = APIRouter(prefix="/tickets", tags=["tickets"])

@router.get("/validate/{qr_code}")
def validate_ticket(
    qr_code: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Validate QR code for check-in"""
    
    # Verify QR code signature
    qr_data = verify_qr_payload(qr_code)
    if not qr_data["valid"]:
        raise HTTPException(status_code=400, detail="Invalid QR code")
    
    # Find attendee
    attendee = db.query(Attendee).filter(
        Attendee.id == qr_data["attendee_id"],
        Attendee.qr_code == qr_code
    ).first()
    
    if not attendee:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Check if order is paid
    if attendee.order.status != "paid":
        raise HTTPException(status_code=400, detail="Ticket not paid")
    
    # Check if already checked in
    if attendee.is_checked_in:
        return {
            "valid": True,
            "already_checked_in": True,
            "attendee": {
                "name": attendee.full_name,
                "email": attendee.email,
                "checked_in_at": attendee.checked_in_at
            }
        }
    
    # Perform check-in
    attendee.is_checked_in = True
    attendee.checked_in_at = datetime.utcnow()
    db.commit()
    
    return {
        "valid": True,
        "checked_in": True,
        "attendee": {
            "name": attendee.full_name,
            "email": attendee.email,
            "event": attendee.order.event.name,
            "ticket_type": attendee.order.order_items[0].ticket_batch.name if attendee.order.order_items else "N/A"
        }
    }