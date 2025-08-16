import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base
from app.models import Event, TicketBatch
from datetime import datetime, timedelta
from decimal import Decimal

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_event(client):
    db = TestingSessionLocal()
    event = Event(
        name="Test Event",
        description="Test Description",
        location="Test Location",
        start_date=datetime.now() + timedelta(days=30),
        end_date=datetime.now() + timedelta(days=30, hours=8)
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    
    batch = TicketBatch(
        event_id=event.id,
        name="Test Batch",
        price=Decimal("99.90"),
        quantity=100,
        sale_start=datetime.now(),
        sale_end=datetime.now() + timedelta(days=25)
    )
    db.add(batch)
    db.commit()
    event_id = event.id
    db.close()
    return event_id

def test_health_check(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_checkout_page(client, sample_event):
    response = client.get(f"/checkout?event_id={sample_event}")
    assert response.status_code == 200

def test_create_order(client, sample_event):
    db = TestingSessionLocal()
    batch = db.query(TicketBatch).filter(TicketBatch.event_id == sample_event).first()
    db.close()
    
    order_data = {
        "event_id": sample_event,
        "full_name": "Test User",
        "email": "test@example.com",
        "phone": "11999999999",
        "items": [
            {
                "ticket_batch_id": batch.id,
                "quantity": 2
            }
        ]
    }
    
    response = client.post("/checkout/order", json=order_data)
    assert response.status_code == 200
    assert response.json()["total_amount"] == 199.8