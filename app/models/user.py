from sqlalchemy import Column, String, DateTime, Boolean
from datetime import datetime
from ..database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(255), primary_key=True)  # Cognito user ID
    email = Column(String(255), unique=True, index=True)
    full_name = Column(String(255))
    role = Column(String(50), default="buyer")  # admin, buyer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)