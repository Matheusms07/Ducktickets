from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal
from ..database import get_db
from ..models import Event, TicketBatch, Order, OrderItem, Attendee
from ..schemas import OrderCreate
from ..services.qrcode.generator import generate_qr_payload
from ..rate_limit import limiter

router = APIRouter(prefix="/checkout", tags=["checkout"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
def checkout_page(
    event_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Checkout page"""
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Get all active batches for this event
        batches = db.query(TicketBatch).filter(
            TicketBatch.event_id == event_id,
            TicketBatch.is_active == True
        ).all()
        
        print(f"Found {len(batches)} active batches for event {event_id}")
        for batch in batches:
            print(f"Batch: {batch.name}, Price: {batch.price}, Quantity: {batch.quantity}")
        
        # Filter batches with available tickets
        available_batches = []
        for batch in batches:
            sold = batch.sold_quantity or 0
            available = batch.quantity - sold
            print(f"Batch {batch.name}: {available} tickets available")
            if available > 0:
                available_batches.append(batch)
        
        return templates.TemplateResponse("checkout.html", {
            "request": request,
            "event": event,
            "batches": available_batches
        })
    except Exception as e:
        print(f"Checkout page error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/order")
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db)
):
    """Create order"""
    try:
        print(f"Creating order: {order_data}")
        
        # Get event
        event = db.query(Event).filter(Event.id == order_data.event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Calculate total
        total_amount = Decimal('0')
        for item in order_data.items:
            batch = db.query(TicketBatch).filter(TicketBatch.id == item.ticket_batch_id).first()
            if batch:
                total_amount += batch.price * item.quantity
        
        # Create order
        order = Order(
            event_id=order_data.event_id,
            email=order_data.email,
            full_name=order_data.full_name,
            phone=order_data.phone,
            total_amount=total_amount,
            status="pending"
        )
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        # Create attendees for each ticket
        for item in order_data.items:
            for i in range(item.quantity):
                attendee = Attendee(
                    order_id=order.id,
                    ticket_batch_id=item.ticket_batch_id,
                    full_name=order_data.full_name,
                    email=order_data.email,
                    phone=order_data.phone
                )
                db.add(attendee)
        
        db.commit()
        print(f"Order created: {order.id} with attendees")
        
        return {
            "id": order.id,
            "total_amount": float(order.total_amount),
            "status": order.status
        }
        
    except Exception as e:
        print(f"Order creation error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pay")
def initiate_payment(order_id: int, db: Session = Depends(get_db)):
    """Mock payment"""
    return {
        "checkout_url": f"/checkout/success?order_id={order_id}"
    }

@router.get("/success", response_class=HTMLResponse)
def payment_success(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Success page"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        order.status = "paid"
        db.commit()
    
    return templates.TemplateResponse("success.html", {
        "request": request,
        "order": order
    })