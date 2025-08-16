from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
import redis
from .config import settings

# Initialize Redis if available
redis_client = None
if settings.redis_url:
    redis_client = redis.from_url(settings.redis_url)

def get_client_ip(request: Request):
    """Get client IP for rate limiting"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)

# Create limiter
limiter = Limiter(
    key_func=get_client_ip,
    storage_uri=settings.redis_url or "memory://",
    default_limits=["100/minute"]
)