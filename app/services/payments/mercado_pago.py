import mercadopago
import hmac
import hashlib
from typing import Dict, Any
from .base import PaymentProvider
from ...models.order import Order
from ...config import settings

class MercadoPagoProvider(PaymentProvider):
    def __init__(self):
        self.sdk = mercadopago.SDK(settings.mercado_pago_access_token)
    
    def create_payment(self, order: Order) -> Dict[str, Any]:
        """Create Mercado Pago preference"""
        items = []
        for item in order.order_items:
            items.append({
                "title": f"{item.ticket_batch.name} - {order.event.name}",
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
                "currency_id": "BRL"
            })
        
        preference_data = {
            "items": items,
            "payer": {
                "name": order.full_name,
                "email": order.email,
                "phone": {
                    "number": order.phone or ""
                }
            },
            "external_reference": str(order.id),
            "notification_url": f"{settings.allowed_origins}/webhook",
            "back_urls": {
                "success": f"{settings.allowed_origins}/checkout/success?order_id={order.id}",
                "failure": f"{settings.allowed_origins}/checkout/failure?order_id={order.id}",
                "pending": f"{settings.allowed_origins}/checkout/pending?order_id={order.id}"
            },
            "auto_return": "approved"
        }
        
        response = self.sdk.preference().create(preference_data)
        
        if response["status"] == 201:
            return {
                "success": True,
                "preference_id": response["response"]["id"],
                "init_point": response["response"]["init_point"]
            }
        else:
            return {"success": False, "error": response["response"]}
    
    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Verify Mercado Pago webhook signature"""
        if not settings.mercado_pago_webhook_secret:
            return True  # Skip verification in development
        
        expected_signature = hmac.new(
            settings.mercado_pago_webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def process_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Mercado Pago webhook"""
        if data.get("type") == "payment":
            payment_id = data["data"]["id"]
            payment_info = self.get_payment_status(payment_id)
            
            return {
                "payment_id": payment_id,
                "status": payment_info.get("status"),
                "external_reference": payment_info.get("external_reference"),
                "amount": payment_info.get("transaction_amount"),
                "payment_method": payment_info.get("payment_method_id")
            }
        
        return {}
    
    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Get payment status from Mercado Pago"""
        response = self.sdk.payment().get(payment_id)
        
        if response["status"] == 200:
            return response["response"]
        else:
            return {}