from fastapi import APIRouter, Depends, HTTPException, Response, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from ..database import get_db
from ..models import Event, TicketBatch, Order, Attendee, Coupon
from ..schemas import EventCreate, EventUpdate, EventResponse
from ..rate_limit import limiter

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    """Admin dashboard page"""
    return templates.TemplateResponse("admin.html", {"request": request})

@router.get("/status")
def admin_status(db: Session = Depends(get_db)):
    """Admin dashboard status"""
    total_events = db.query(Event).count()
    active_events = db.query(Event).filter(Event.is_active == True).count()
    total_orders = db.query(Order).count()
    paid_orders = db.query(Order).filter(Order.status == "paid").count()
    
    return {
        "total_events": total_events,
        "active_events": active_events,
        "total_orders": total_orders,
        "paid_orders": paid_orders
    }

@router.get("/events")
def list_events(db: Session = Depends(get_db)):
    """List all events"""
    events = db.query(Event).all()
    return [
        {
            "id": e.id,
            "name": e.name,
            "description": e.description,
            "location": e.location,
            "start_date": e.start_date.isoformat(),
            "end_date": e.end_date.isoformat(),
            "is_active": e.is_active
        } for e in events
    ]

@router.post("/event")
@limiter.limit("10/minute")
def create_event(
    request: Request,
    event: EventCreate,
    db: Session = Depends(get_db)
):
    """Create new event"""
    db_event = Event(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return {
        "id": db_event.id,
        "name": db_event.name,
        "message": "Evento criado com sucesso"
    }

@router.delete("/event/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    """Delete event"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    db.delete(event)
    db.commit()
    return {"message": "Evento excluído"}

@router.get("/batches/{event_id}")
def list_batches(event_id: int, db: Session = Depends(get_db)):
    """List ticket batches for event"""
    batches = db.query(TicketBatch).filter(TicketBatch.event_id == event_id).all()
    return [
        {
            "id": b.id,
            "name": b.name,
            "description": b.description,
            "price": float(b.price),
            "quantity": b.quantity,
            "sold_quantity": b.sold_quantity or 0,
            "sale_start": b.sale_start.isoformat(),
            "sale_end": b.sale_end.isoformat(),
            "is_active": b.is_active,
            "requires_coupon": getattr(b, 'requires_coupon', False)
        } for b in batches
    ]

@router.post("/batches")
def create_ticket_batch(
    event_id: int = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    quantity: int = Form(...),
    sale_start: str = Form(...),
    sale_end: str = Form(...),
    requires_coupon: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Create ticket batch"""
    try:
        batch = TicketBatch(
            event_id=event_id,
            name=name,
            description=description,
            price=Decimal(str(price)),
            quantity=quantity,
            sale_start=datetime.fromisoformat(sale_start.replace('Z', '')),
            sale_end=datetime.fromisoformat(sale_end.replace('Z', '')),
            is_active=True
        )
        
        db.add(batch)
        db.commit()
        db.refresh(batch)
        return {"id": batch.id, "message": "Lote criado com sucesso"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/batches/{batch_id}")
def update_batch(
    batch_id: int,
    name: str = None,
    price: float = None,
    quantity: int = None,
    is_active: bool = None,
    db: Session = Depends(get_db)
):
    """Update batch"""
    batch = db.query(TicketBatch).filter(TicketBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    if name is not None:
        batch.name = name
    if price is not None:
        batch.price = Decimal(str(price))
    if quantity is not None:
        batch.quantity = quantity
    if is_active is not None:
        batch.is_active = is_active
    
    db.commit()
    return {"message": "Lote atualizado"}

@router.delete("/batches/{batch_id}")
def delete_batch(batch_id: int, db: Session = Depends(get_db)):
    """Delete batch"""
    batch = db.query(TicketBatch).filter(TicketBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    db.delete(batch)
    db.commit()
    return {"message": "Lote excluído"}

@router.get("/attendees")
def get_attendees(event_id: int, db: Session = Depends(get_db)):
    """Get event attendees"""
    attendees = db.query(Attendee).join(Order).filter(
        Order.event_id == event_id,
        Order.status == "paid"
    ).all()
    return [
        {
            "id": a.id,
            "full_name": a.full_name,
            "email": a.email,
            "phone": a.phone,
            "is_checked_in": a.is_checked_in,
            "created_at": a.created_at.isoformat()
        } for a in attendees
    ]

@router.get("/orders")
def get_orders(event_id: int, db: Session = Depends(get_db)):
    """Get event orders"""
    orders = db.query(Order).filter(Order.event_id == event_id).all()
    return [
        {
            "id": o.id,
            "full_name": o.full_name,
            "email": o.email,
            "total_amount": float(o.total_amount),
            "status": o.status,
            "created_at": o.created_at.isoformat()
        } for o in orders
    ]

# User Management Routes
@router.get("/users", response_class=HTMLResponse)
def admin_users_page(request: Request):
    """Admin users management page"""
    return templates.TemplateResponse("admin_users.html", {"request": request})

@router.get("/api/users")
def list_all_users(db: Session = Depends(get_db)):
    """List all users"""
    from ..models import User
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "is_admin": u.is_admin,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat(),
            "last_login": u.last_login.isoformat() if u.last_login else None
        } for u in users
    ]

@router.put("/api/users/{user_id}")
def update_user(
    user_id: int,
    full_name: str = None,
    email: str = None,
    password: str = None,
    is_admin: bool = None,
    is_active: bool = None,
    db: Session = Depends(get_db)
):
    """Update user"""
    from ..models import User
    from ..auth import auth_manager
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if full_name is not None:
        user.full_name = full_name
    if email is not None:
        user.email = email
    if password is not None:
        user.password_hash = auth_manager.get_password_hash(password)
    if is_admin is not None:
        user.is_admin = is_admin
    if is_active is not None:
        user.is_active = is_active
    
    db.commit()
    return {"message": "User updated successfully"}

@router.patch("/api/users/{user_id}/status")
def toggle_user_status(
    user_id: int,
    is_active: bool,
    db: Session = Depends(get_db)
):
    """Toggle user active status"""
    from ..models import User
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = is_active
    db.commit()
    
    return {"message": f"User {'activated' if is_active else 'deactivated'} successfully"}