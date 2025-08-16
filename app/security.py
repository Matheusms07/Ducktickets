from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import requests
from functools import lru_cache
from .config import settings
from .database import get_db
from .models.user import User
from sqlalchemy.orm import Session

security = HTTPBearer(auto_error=False)

@lru_cache()
def get_cognito_jwks():
    """Cache Cognito JWKs"""
    if not settings.cognito_user_pool_id:
        return {}
    url = f"https://cognito-idp.{settings.cognito_region}.amazonaws.com/{settings.cognito_user_pool_id}/.well-known/jwks.json"
    try:
        response = requests.get(url)
        return response.json()
    except:
        return {}

def verify_cognito_token(token: str):
    """Verify Cognito JWT token"""
    if not settings.cognito_user_pool_id:
        # Development mode - create mock payload
        return {"sub": "test-user", "email": "admin@test.com", "name": "Test Admin"}
    
    try:
        jwks = get_cognito_jwks()
        header = jwt.get_unverified_header(token)
        
        # Find the correct key
        key = None
        for jwk in jwks["keys"]:
            if jwk["kid"] == header["kid"]:
                key = jwk
                break
        
        if not key:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Verify token
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.cognito_client_id,
            issuer=f"https://cognito-idp.{settings.cognito_region}.amazonaws.com/{settings.cognito_user_pool_id}"
        )
        
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user"""
    if not credentials and not settings.cognito_user_pool_id:
        # Development mode - create test admin user
        user = db.query(User).filter(User.id == "test-admin").first()
        if not user:
            user = User(
                id="test-admin",
                email="admin@test.com",
                full_name="Test Admin",
                role="admin"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    payload = verify_cognito_token(credentials.credentials)
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        # Create user if doesn't exist
        user = User(
            id=user_id,
            email=payload.get("email"),
            full_name=payload.get("name", "")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user

def require_admin(current_user: User = Depends(get_current_user)):
    """Require admin role"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def security_headers(request: Request, call_next):
    """Add security headers"""
    response = call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response