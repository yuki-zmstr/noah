"""Main FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
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

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add trusted host middleware for security
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.amazonaws.com"]
    )

    # Include API routes
    app.include_router(api_router, prefix="/api/v1")

    @app.on_event("startup")
    async def startup_event():
        """Initialize database and other services on startup."""
        logger.info("Starting Noah Reading Agent...")

        # Create database tables
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise

        # Log registered models
        registered_models = [
            UserProfile.__name__, ReadingBehavior.__name__, PreferenceSnapshot.__name__,
            ContentItem.__name__, PurchaseLink.__name__, DiscoveryRecommendation.__name__,
            ConversationSession.__name__, ConversationMessage.__name__, ConversationHistory.__name__
        ]
        logger.info(f"Registered models: {', '.join(registered_models)}")

        logger.info("Noah Reading Agent startup completed")

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "app_name": settings.app_name,
            "version": settings.app_version
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
