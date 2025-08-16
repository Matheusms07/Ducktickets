from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Order, Event, Attendee, TicketBatch

router = APIRouter(tags=["user"])
templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/meus-ingressos", response_class=HTMLResponse)
def meus_ingressos_page(request: Request):
    """Meus ingressos page"""
    return templates.TemplateResponse("meus_ingressos.html", {"request": request})

@router.get("/user/orders")
def get_user_orders(email: str, db: Session = Depends(get_db)):
    """Get user orders by email"""
    orders = db.query(Order).filter(Order.email == email).all()
    
    result = []
    for order in orders:
        # Get event info
        event = db.query(Event).filter(Event.id == order.event_id).first()
        
        result.append({
            "id": order.id,
            "event_name": event.name if event else "Evento",
            "total_amount": float(order.total_amount),
            "status": order.status,
            "created_at": order.created_at.isoformat(),
            "attendees_count": len(order.attendees)
        })
    
    return result

@router.get("/api/user/tickets")
def get_user_tickets(email: str, db: Session = Depends(get_db)):
    """Get user tickets by email"""
    # Get all attendees for this email
    attendees = db.query(Attendee).filter(Attendee.email == email).all()
    
    result = []
    for attendee in attendees:
        order = db.query(Order).filter(Order.id == attendee.order_id).first()
        if order:
            event = db.query(Event).filter(Event.id == order.event_id).first()
            batch = db.query(TicketBatch).filter(TicketBatch.id == attendee.ticket_batch_id).first()
            
            result.append({
                "id": attendee.id,
                "attendee_name": attendee.full_name,
                "event_name": event.name if event else "Evento",
                "event_date": event.start_date.isoformat() if event and event.start_date else None,
                "event_location": event.location if event else None,
                "batch_name": batch.name if batch else "Ingresso",
                "price": float(batch.price) if batch else 0.0,
                "payment_status": order.status,
                "order_id": order.id
            })
    
    return result

@router.get("/admin-login", response_class=HTMLResponse)
def admin_login_page(request: Request):
    """Admin login page"""
    return templates.TemplateResponse("admin_login.html", {"request": request})