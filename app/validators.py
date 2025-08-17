"""
Input validation and sanitization
"""
import re
from typing import Optional
from fastapi import HTTPException, status
from pydantic import validator
import bleach

class InputValidator:
    """Input validation and sanitization utilities"""
    
    # Regex patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^\+?[\d\s\-\(\)]{10,15}$')
    NAME_PATTERN = re.compile(r'^[a-zA-ZÀ-ÿ\s]{2,100}$')
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Remove HTML tags and dangerous content"""
        if not text:
            return ""
        return bleach.clean(text, tags=[], strip=True)
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate and sanitize email"""
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        email = email.strip().lower()
        if not InputValidator.EMAIL_PATTERN.match(email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        return email
    
    @staticmethod
    def validate_phone(phone: Optional[str]) -> Optional[str]:
        """Validate and sanitize phone"""
        if not phone:
            return None
        
        phone = re.sub(r'[^\d\+\-\(\)\s]', '', phone.strip())
        if not InputValidator.PHONE_PATTERN.match(phone):
            raise HTTPException(status_code=400, detail="Invalid phone format")
        
        return phone
    
    @staticmethod
    def validate_name(name: str) -> str:
        """Validate and sanitize name"""
        if not name:
            raise HTTPException(status_code=400, detail="Name is required")
        
        name = InputValidator.sanitize_html(name.strip())
        if len(name) < 2 or len(name) > 100:
            raise HTTPException(status_code=400, detail="Name must be between 2 and 100 characters")
        
        if not InputValidator.NAME_PATTERN.match(name):
            raise HTTPException(status_code=400, detail="Name contains invalid characters")
        
        return name
    
    @staticmethod
    def validate_password(password: str) -> str:
        """Validate password strength"""
        if not password:
            raise HTTPException(status_code=400, detail="Password is required")
        
        if len(password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        
        if len(password) > 128:
            raise HTTPException(status_code=400, detail="Password too long")
        
        # Check for at least one uppercase, lowercase, digit
        if not re.search(r'[A-Z]', password):
            raise HTTPException(status_code=400, detail="Password must contain uppercase letter")
        
        if not re.search(r'[a-z]', password):
            raise HTTPException(status_code=400, detail="Password must contain lowercase letter")
        
        if not re.search(r'\d', password):
            raise HTTPException(status_code=400, detail="Password must contain digit")
        
        return password
    
    @staticmethod
    def validate_text_field(text: str, field_name: str, max_length: int = 1000) -> str:
        """Validate and sanitize text fields"""
        if not text:
            return ""
        
        text = InputValidator.sanitize_html(text.strip())
        if len(text) > max_length:
            raise HTTPException(
                status_code=400, 
                detail=f"{field_name} must be less than {max_length} characters"
            )
        
        return text