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
    ContentItem, DiscoveryRecommendation,
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

    # Health check endpoint MUST be defined FIRST and be very simple
    # to avoid any middleware interference with ALB health checks
    @app.get("/health")
    async def health_check():
        """Health check endpoint for load balancer."""
        return {"status": "healthy"}

    # Add CORS middleware AFTER health check
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
        # Log all requests including health checks for debugging
        logger.info(
            f"Request: {request.method} {request.url.path} from {request.client.host if request.client else 'unknown'}")
        logger.info(f"Headers: {dict(request.headers)}")
        
        response = await call_next(request)
        
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
                ContentItem.__name__, DiscoveryRecommendation.__name__,
                ConversationSession.__name__, ConversationMessage.__name__, ConversationHistory.__name__
            ]
            logger.info(f"Registered models: {', '.join(registered_models)}")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            logger.warning("Application starting without database connection. DB operations will fail until connection is established.")
            # Don't raise - allow app to start for health checks

        # Initialize and log Strands agents configuration
        try:
            from src.services.enhanced_conversation_service import EnhancedConversationService
            from src.services.strands_config import strands_config, validate_strands_config
            
            # Initialize conversation service to check Strands availability
            conversation_service = EnhancedConversationService()
            service_info = conversation_service.get_service_info()
            
            logger.info(f"Conversation service initialized: {service_info['service_type']}")
            
            if service_info.get("strands_available"):
                logger.info("Strands agents framework successfully integrated")
                logger.info(f"Agent model: {strands_config.agent_model}")
                logger.info(f"Tools enabled: {service_info.get('agent_info', {}).get('tools', [])}")
                
                # Validate configuration
                validation = validate_strands_config(strands_config)
                if validation["valid"]:
                    logger.info("Strands configuration validation passed")
                else:
                    logger.warning(f"Strands configuration issues: {validation['errors']}")
            else:
                logger.info("Using AWS Agent Core fallback for conversation processing")
                
        except Exception as e:
            logger.error(f"Error initializing Strands agents: {e}")
            logger.info("Falling back to AWS Agent Core for conversation processing")

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
                "strands_agents": settings.strands_enabled,
                "multilingual_support": True,
                "discovery_mode": True,
                "streaming_responses": True
            },
            "agent_config": {
                "strands_enabled": settings.strands_enabled,
                "model": settings.strands_agent_model,
                "streaming": settings.strands_streaming_enabled
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
