"""Main FastAPI application entry point."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging

from src.config import settings
from src.database import engine, Base
from src.api.routes import api_router

# Import all models to ensure they're registered with SQLAlchemy
from src.models import (
    UserProfile, ReadingBehavior, PreferenceSnapshot,
    ContentItem, PurchaseLink, DiscoveryRecommendation,
    ConversationSession, ConversationMessage, ConversationHistory
)

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # Health check endpoint MUST be defined before CORS middleware
    # to avoid CORS rejecting ALB health checks
    @app.get("/health")
    async def health_check():
        """Health check endpoint for load balancer."""
        return {
            "status": "healthy",
            "app_name": settings.app_name,
            "version": settings.app_version,
            "timestamp": "2026-01-17T12:25:00.000Z",
            "code_version": "fixed-trusted-host-v3"  # Version marker to confirm deployment
        }

    # Add CORS middleware
    # Note: For production, set ALLOWED_ORIGINS env var to your frontend domain
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins (ALB health checks don't send Origin header)
        allow_credentials=False,  # Must be False when allow_origins is "*"
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add debugging middleware to log requests
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        # Skip logging for health checks to reduce noise
        if request.url.path != "/health":
            logger.info(
                f"Request: {request.method} {request.url} from {request.client.host if request.client else 'unknown'}")
            logger.info(f"Headers: {dict(request.headers)}")
        response = await call_next(request)
        if request.url.path != "/health":
            logger.info(f"Response status: {response.status_code}")
        return response

    # Note: TrustedHostMiddleware removed to allow AWS load balancer health checks
    # The load balancer provides host validation at the infrastructure level

    # Include API routes
    app.include_router(api_router, prefix="/api/v1")

    @app.on_event("startup")
    async def startup_event():
        """Initialize database and other services on startup."""
        logger.info("Starting Noah Reading Agent...")

        # Create database tables - don't fail startup if DB is unavailable
        # This allows health checks to pass while DB connections retry
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")

            # Log registered models
            registered_models = [
                UserProfile.__name__, ReadingBehavior.__name__, PreferenceSnapshot.__name__,
                ContentItem.__name__, PurchaseLink.__name__, DiscoveryRecommendation.__name__,
                ConversationSession.__name__, ConversationMessage.__name__, ConversationHistory.__name__
            ]
            logger.info(f"Registered models: {', '.join(registered_models)}")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            logger.warning("Application starting without database connection. DB operations will fail until connection is established.")
            # Don't raise - allow app to start for health checks

        logger.info("Noah Reading Agent startup completed")

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "Noah Reading Agent API",
            "version": settings.app_version,
            "docs_url": "/docs" if settings.debug else "Documentation disabled in production",
            "health_check": "/health"
        }

    @app.get("/api/config")
    async def get_config():
        """Get frontend configuration."""
        return {
            "app_name": settings.app_name,
            "version": settings.app_version,
            "debug": settings.debug,
            "cors_origins": settings.cors_origins,
            "features": {
                "aws_agent_core": True,
                "multilingual_support": True,
                "discovery_mode": True,
                "purchase_links": True
            }
        }

    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )


def main():
    """Entry point for the noah-server script."""
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
