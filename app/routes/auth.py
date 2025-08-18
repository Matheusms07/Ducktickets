"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..database import get_db
from ..auth import auth_manager
from ..auth import get_current_user
from ..validators import InputValidator
from ..models import User

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="templates")

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    is_admin: bool = False

@router.post("/login", response_model=LoginResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT tokens"""
    
    # Validate input
    email = InputValidator.validate_email(login_data.email)
    
    # Authenticate user
    user = auth_manager.authenticate_user(db, email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token = auth_manager.create_access_token(data={"sub": str(user.id)})
    refresh_token = auth_manager.create_refresh_token(data={"sub": str(user.id)})
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_admin": user.is_admin
        }
    )

@router.post("/admin/login", response_model=LoginResponse)
def admin_login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Admin-specific login with additional validation"""
    
    # Validate input
    email = InputValidator.validate_email(login_data.email)
    
    # Authenticate user
    user = auth_manager.authenticate_user(db, email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check admin privileges
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Create tokens
    access_token = auth_manager.create_access_token(data={"sub": str(user.id), "admin": True})
    refresh_token = auth_manager.create_refresh_token(data={"sub": str(user.id), "admin": True})
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_admin": user.is_admin
        }
    )

@router.post("/register", response_model=dict)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register new user"""
    
    # Validate input
    email = InputValidator.validate_email(user_data.email)
    password = InputValidator.validate_password(user_data.password)
    full_name = InputValidator.validate_name(user_data.full_name)
    
    # Check if user exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    password_hash = auth_manager.get_password_hash(password)
    user = User(
        email=email,
        password_hash=password_hash,
        full_name=full_name,
        is_admin=user_data.is_admin
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"message": "User created successfully", "user_id": user.id}

@router.post("/refresh")
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token"""
    
    try:
        payload = auth_manager.verify_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == int(user_id)).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Create new access token
        access_token = auth_manager.create_access_token(
            data={"sub": str(user.id), "admin": user.is_admin}
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_admin": current_user.is_admin,
        "created_at": current_user.created_at.isoformat()
    }