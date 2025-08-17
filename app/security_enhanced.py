"""
Enhanced security middleware and utilities
"""
import hashlib
import secrets
import time
from typing import Dict, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import structlog

logger = structlog.get_logger()

class SecurityHeaders:
    """Security headers configuration"""
    
    @staticmethod
    def get_headers(environment: str = "production") -> Dict[str, str]:
        """Get security headers based on environment"""
        base_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=()",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
        
        if environment == "production":
            base_headers.update({
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
                "Content-Security-Policy": (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
                    "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
                    "img-src 'self' data: https:; "
                    "connect-src 'self'; "
                    "frame-ancestors 'none'; "
                    "base-uri 'self'; "
                    "form-action 'self'"
                )
            })
        
        return base_headers

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Advanced rate limiting middleware"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients: Dict[str, Dict] = {}
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier"""
        auth_header = request.headers.get("Authorization")
        if auth_header:
            scheme, token = get_authorization_scheme_param(auth_header)
            if scheme.lower() == "bearer" and token:
                return hashlib.sha256(token.encode()).hexdigest()[:16]
        
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        return request.client.host if request.client else "unknown"
    
    def _is_rate_limited(self, client_id: str) -> bool:
        """Check if client is rate limited"""
        now = time.time()
        
        if client_id not in self.clients:
            self.clients[client_id] = {"calls": 1, "reset_time": now + self.period}
            return False
        
        client_data = self.clients[client_id]
        
        if now > client_data["reset_time"]:
            client_data["calls"] = 1
            client_data["reset_time"] = now + self.period
            return False
        
        if client_data["calls"] >= self.calls:
            return True
        
        client_data["calls"] += 1
        return False
    
    async def dispatch(self, request: Request, call_next):
        client_id = self._get_client_id(request)
        
        if self._is_rate_limited(client_id):
            logger.warning("Rate limit exceeded", client_id=client_id, path=request.url.path)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={"Retry-After": str(self.period)}
            )
        
        response = await call_next(request)
        return response

class SecurityMiddleware(BaseHTTPMiddleware):
    """Main security middleware"""
    
    def __init__(self, app, environment: str = "production"):
        super().__init__(app)
        self.environment = environment
        self.security_headers = SecurityHeaders.get_headers(environment)
    
    async def dispatch(self, request: Request, call_next):
        request_id = secrets.token_hex(8)
        
        logger.info(
            "Request started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            user_agent=request.headers.get("User-Agent", ""),
            client_ip=self._get_client_ip(request)
        )
        
        request.state.request_id = request_id
        
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        
        logger.info(
            "Request completed",
            request_id=request_id,
            status_code=response.status_code,
            process_time=process_time
        )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get real client IP"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"