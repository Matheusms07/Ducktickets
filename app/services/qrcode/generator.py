import qrcode
import hashlib
import hmac
from io import BytesIO
from typing import Dict, Any
from ...config import settings

def generate_qr_payload(order_id: int, attendee_id: int) -> str:
    """Generate signed QR code payload"""
    data = f"{order_id}:{attendee_id}"
    signature = hmac.new(
        settings.secret_key.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:16]  # First 16 chars
    
    return f"{data}:{signature}"

def verify_qr_payload(payload: str) -> Dict[str, Any]:
    """Verify QR code payload"""
    try:
        parts = payload.split(":")
        if len(parts) != 3:
            return {"valid": False}
        
        order_id, attendee_id, signature = parts
        data = f"{order_id}:{attendee_id}"
        
        expected_signature = hmac.new(
            settings.secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()[:16]
        
        if not hmac.compare_digest(signature, expected_signature):
            return {"valid": False}
        
        return {
            "valid": True,
            "order_id": int(order_id),
            "attendee_id": int(attendee_id)
        }
    except (ValueError, IndexError):
        return {"valid": False}

def generate_qr_code(payload: str) -> bytes:
    """Generate QR code image"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to bytes
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    return img_buffer.getvalue()