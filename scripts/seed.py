"""
Seed script to create initial data
"""
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models import Event, TicketBatch, User

def create_sample_data():
    """Create sample event and ticket batches"""
    db = SessionLocal()
    
    try:
        # Create admin user
        admin_user = User(
            id="admin-user-id",
            email="admin@ducktickets.com",
            full_name="Admin User",
            role="admin"
        )
        db.add(admin_user)
        
        # Create sample event
        event = Event(
            name="DuckConf 2024",
            description="A conferência mais quack do ano!",
            location="Centro de Convenções - São Paulo, SP",
            start_date=datetime.now() + timedelta(days=30),
            end_date=datetime.now() + timedelta(days=30, hours=8),
            max_attendees=500
        )
        db.add(event)
        db.flush()  # Get event ID
        
        # Create ticket batches
        early_bird = TicketBatch(
            event_id=event.id,
            name="Early Bird",
            description="Lote promocional com desconto especial",
            price=Decimal("99.90"),
            quantity=100,
            sale_start=datetime.now(),
            sale_end=datetime.now() + timedelta(days=15)
        )
        db.add(early_bird)
        
        regular = TicketBatch(
            event_id=event.id,
            name="Regular",
            description="Ingresso regular",
            price=Decimal("149.90"),
            quantity=300,
            sale_start=datetime.now() + timedelta(days=15),
            sale_end=datetime.now() + timedelta(days=25)
        )
        db.add(regular)
        
        last_minute = TicketBatch(
            event_id=event.id,
            name="Last Minute",
            description="Últimas vagas disponíveis",
            price=Decimal("199.90"),
            quantity=100,
            sale_start=datetime.now() + timedelta(days=25),
            sale_end=datetime.now() + timedelta(days=29)
        )
        db.add(last_minute)
        
        db.commit()
        print("Sample data created successfully!")
        print(f"Event ID: {event.id}")
        print("Ticket batches created: Early Bird, Regular, Last Minute")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()