from abc import ABC, abstractmethod
from typing import Dict, Any
from ...models.order import Order

class PaymentProvider(ABC):
    """Base class for payment providers"""
    
    @abstractmethod
    def create_payment(self, order: Order) -> Dict[str, Any]:
        """Create payment and return checkout URL"""
        pass
    
    @abstractmethod
    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature"""
        pass
    
    @abstractmethod
    def process_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process webhook data and return payment info"""
        pass
    
    @abstractmethod
    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Get payment status from provider"""
        pass