"""Main FastAPI application entry point."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

# Try to import ProxyHeadersMiddleware from different locations
try:
    from starlette.middleware.proxy_headers import ProxyHeadersMiddleware
except ImportError:
    try:
        from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
    except ImportError:
        # Fallback: create a simple proxy headers middleware
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.requests import Request as StarletteRequest
        from starlette.responses import Response
        
        class ProxyHeadersMiddleware(BaseHTTPMiddleware):
            def __init__(self, app, trusted_hosts=None):
                super().__init__(app)
                self.trusted_hosts = trusted_hosts or ["*"]
            
            async def dispatch(self, request: StarletteRequest, call_next):
                # Handle X-Forwarded-* headers from load balancer
                if "x-forwarded-proto" in request.headers:
                    request.scope["scheme"] = request.headers["x-forwarded-proto"]
                if "x-forwarded-for" in request.headers:
                    # Use the first IP in the chain (original client)
                    forwarded_for = request.headers["x-forwarded-for"].split(",")[0].strip()
                    if request.client:
                        request.scope["client"] = (forwarded_for, request.client.port)
                if "x-forwarded-host" in request.headers:
                    request.scope["server"] = (request.headers["x-forwarded-host"], None)
                
                response = await call_next(request)
                return response
import logging
import asyncio
import atexit

from src.config import settings
from src.database import engine, Base
from src.api.routes import api_router

# Import all models to ensure they're registered with SQLAlchemy
from src.models import (
    UserProfile, ReadingBehavior, PreferenceSnapshot,
    ContentItem, DiscoveryRecommendation,
    ConversationSession, ConversationMessage, ConversationHistory
)

# Import monitoring and logging services
from src.services.logging_config import setup_logging
from src.services.monitoring_service import monitoring_service, AlertLevel
from src.middleware.monitoring_middleware import MonitoringMiddleware

# Setup enhanced logging
setup_logging()
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

    # Add ProxyHeadersMiddleware FIRST to handle X-Forwarded-* headers from ALB
    if settings.proxy_headers_enabled:
        app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=settings.trusted_hosts)
        logger.info(f"ProxyHeadersMiddleware enabled with trusted_hosts: {settings.trusted_hosts}")

    # Add monitoring middleware AFTER proxy headers
    app.add_middleware(MonitoringMiddleware)

    # Add CORS middleware AFTER monitoring
    # Use specific origins when credentials are needed for security
    cors_origins = settings.cors_origins_list if settings.cors_origins_list else ["*"]
    
    # Only allow credentials if we have specific origins (not "*") and it's explicitly enabled
    allow_credentials = (
        settings.cors_allow_credentials and 
        len(cors_origins) > 0 and 
        "*" not in cors_origins
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    logger.info(f"CORS configured with origins: {cors_origins}, credentials: {allow_credentials}")

    # Remove the old debugging middleware since MonitoringMiddleware handles this
    # Note: TrustedHostMiddleware removed to allow AWS load balancer health checks
    # The load balancer provides host validation at the infrastructure level

    # Include API routes
    app.include_router(api_router, prefix="/api/v1")

    @app.on_event("startup")
    async def startup_event():
        """Initialize database and other services on startup."""
        logger.info("Starting Noah Reading Agent with enhanced monitoring...")

        # Initialize monitoring
        monitoring_service.record_metric(
            name="Application.Startup",
            value=1,
            dimensions={"Version": settings.app_version}
        )

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
            
            # Track successful database initialization
            monitoring_service.record_metric(
                name="Database.Initialization",
                value=1,
                dimensions={"Status": "success"}
            )
            
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            logger.warning("Application starting without database connection. DB operations will fail until connection is established.")
            
            # Track database initialization failure
            monitoring_service.record_metric(
                name="Database.Initialization",
                value=1,
                dimensions={"Status": "failure", "ErrorType": type(e).__name__}
            )
            
            monitoring_service.create_alert(
                name="DatabaseInitializationFailure",
                level=AlertLevel.ERROR,
                message=f"Failed to initialize database: {str(e)}",
                metadata={"error_type": type(e).__name__}
            )
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
                    monitoring_service.record_metric(
                        name="Strands.Initialization",
                        value=1,
                        dimensions={"Status": "success"}
                    )
                else:
                    logger.warning(f"Strands configuration issues: {validation['errors']}")
                    monitoring_service.create_alert(
                        name="StrandsConfigurationIssue",
                        level=AlertLevel.WARNING,
                        message=f"Strands configuration validation failed: {validation['errors']}",
                        metadata={"errors": validation['errors']}
                    )
            else:
                logger.info("Using AWS Agent Core fallback for conversation processing")
                monitoring_service.record_metric(
                    name="Strands.Initialization",
                    value=1,
                    dimensions={"Status": "fallback"}
                )
                
        except Exception as e:
            logger.error(f"Error initializing Strands agents: {e}")
            logger.info("Falling back to AWS Agent Core for conversation processing")
            
            monitoring_service.record_metric(
                name="Strands.Initialization",
                value=1,
                dimensions={"Status": "failure", "ErrorType": type(e).__name__}
            )
            
            monitoring_service.create_alert(
                name="StrandsInitializationFailure",
                level=AlertLevel.WARNING,
                message=f"Failed to initialize Strands agents: {str(e)}",
                metadata={"error_type": type(e).__name__}
            )

        logger.info("Noah Reading Agent startup completed with monitoring enabled")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Clean up resources on shutdown."""
        logger.info("Shutting down Noah Reading Agent...")
        
        # Flush any remaining metrics
        try:
            monitoring_service.flush_metrics()
            logger.info("Final metrics flush completed")
        except Exception as e:
            logger.error(f"Error flushing metrics on shutdown: {e}")
        
        # Record shutdown metric
        monitoring_service.record_metric(
            name="Application.Shutdown",
            value=1,
            dimensions={"Version": settings.app_version}
        )
        
        logger.info("Noah Reading Agent shutdown completed")

    # Setup periodic metrics flushing
    async def periodic_metrics_flush():
        """Periodically flush metrics to CloudWatch."""
        while True:
            try:
                await asyncio.sleep(300)  # Flush every 5 minutes
                monitoring_service.flush_metrics()
                logger.debug("Periodic metrics flush completed")
            except Exception as e:
                logger.error(f"Error in periodic metrics flush: {e}")

    # Start background task for metrics flushing
    @app.on_event("startup")
    async def start_background_tasks():
        asyncio.create_task(periodic_metrics_flush())

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "Noah Reading Agent API",
            "version": settings.app_version,
            "docs_url": "/docs" if settings.debug else "Documentation disabled in production",
            "health_check": "/health",
            "monitoring": "/api/v1/monitoring/health"
        }

    @app.get("/api/debug/headers")
    async def debug_headers(request: Request):
        """Debug endpoint to check proxy headers (only available in debug mode)."""
        if not settings.debug:
            return {"error": "Debug endpoints disabled in production"}
        
        return {
            "headers": dict(request.headers),
            "client_host": request.client.host if request.client else None,
            "url": str(request.url),
            "forwarded_proto": request.headers.get("x-forwarded-proto"),
            "forwarded_for": request.headers.get("x-forwarded-for"),
            "forwarded_host": request.headers.get("x-forwarded-host"),
            "forwarded_port": request.headers.get("x-forwarded-port"),
            "real_ip": request.headers.get("x-real-ip"),
            "cloudfront_viewer_country": request.headers.get("cloudfront-viewer-country"),
            "user_agent": request.headers.get("user-agent"),
            "origin": request.headers.get("origin"),
            "cors_config": {
                "allowed_origins": settings.cors_origins_list,
                "allow_credentials": settings.cors_allow_credentials,
            }
        }

    @app.get("/api/config")
    async def get_config():
        """Get frontend configuration."""
        return {
            "app_name": settings.app_name,
            "version": settings.app_version,
            "debug": settings.debug,
            "cors_origins": settings.cors_origins_list,
            "features": {
                "aws_agent_core": True,
                "strands_agents": settings.strands_enabled,
                "multilingual_support": True,
                "discovery_mode": True,
                "streaming_responses": True,
                "monitoring": True
            },
            "agent_config": {
                "strands_enabled": settings.strands_enabled,
                "model": settings.strands_agent_model,
                "streaming": settings.strands_streaming_enabled
            }
        }

    return app


# Setup cleanup on exit
def cleanup_on_exit():
    """Cleanup function to run on application exit."""
    try:
        monitoring_service.flush_metrics()
        logger.info("Final cleanup completed")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

atexit.register(cleanup_on_exit)


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
