import csv
from io import StringIO
from typing import List
from sqlalchemy.orm import Session
from ..models.attendee import Attendee
from ..models.order import Order

def export_attendees_csv(db: Session, event_id: int) -> str:
    """Export attendees to CSV format"""
    
    attendees = db.query(Attendee).join(Order).filter(
        Order.event_id == event_id,
        Order.status == "paid"
    ).all()
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'ID',
        'Nome Completo',
        'Email',
        'Telefone',
        'Lote',
        'Check-in',
        'Data Check-in',
        'QR Code',
        'Pedido',
        'Data Criação'
    ])
    
    # Data
    for attendee in attendees:
        writer.writerow([
            attendee.id,
            attendee.full_name,
            attendee.email,
            attendee.phone or '',
            attendee.order.order_items[0].ticket_batch.name if attendee.order.order_items else '',
            'Sim' if attendee.is_checked_in else 'Não',
            attendee.checked_in_at.strftime('%d/%m/%Y %H:%M') if attendee.checked_in_at else '',
            attendee.qr_code,
            attendee.order_id,
            attendee.created_at.strftime('%d/%m/%Y %H:%M')
        ])
    
    return output.getvalue()