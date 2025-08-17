from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
import structlog
import sys

from .config_environments import settings
from .database import engine, Base, get_db
from .routes import admin_router, checkout_router, webhook_router, tickets_router, health_router, user_router
from .routes.auth import router as auth_router
from .security_enhanced import SecurityMiddleware, RateLimitMiddleware
# from .rate_limit import limiter
from .models import Event, TicketBatch
from sqlalchemy.orm import Session
from sqlalchemy import func

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize X-Ray tracing
if settings.environment == "production":
    xray_recorder.configure(context_missing='LOG_ERROR')
    patch_all()

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI
app = FastAPI(
    title="DuckTickets",
    description="Event ticketing platform",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Templates
templates = Jinja2Templates(directory="templates")

# CORS middleware
allowed_origins = settings.allowed_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Security and Rate limiting middleware
app.add_middleware(SecurityMiddleware, environment=settings.environment)
app.add_middleware(RateLimitMiddleware, calls=settings.rate_limit_calls, period=settings.rate_limit_period)

# Security headers now handled by SecurityMiddleware

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    import uuid
    request_id = str(uuid.uuid4())
    
    # Add request ID to context
    with structlog.contextvars.bound_contextvars(request_id=request_id):
        logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host
        )
        
        response = await call_next(request)
        
        logger.info(
            "Request completed",
            status_code=response.status_code,
            method=request.method,
            url=str(request.url)
        )
        
        response.headers["X-Request-ID"] = request_id
        return response

# Include routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(checkout_router)
app.include_router(webhook_router)
app.include_router(tickets_router)
app.include_router(user_router)

# Static files (for templates)
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    pass  # Directory doesn't exist in production

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    """Homepage with event listing"""
    db = next(get_db())
    try:
        events = db.query(Event).filter(Event.is_active == True).all()
        
        # Calcular preço mínimo para cada evento
        for event in events:
            min_price = db.query(func.min(TicketBatch.price)).filter(
                TicketBatch.event_id == event.id,
                TicketBatch.is_active == True
            ).scalar()
            event.min_price = float(min_price) if min_price else 0.0
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "events": events
        })
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)