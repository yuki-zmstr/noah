"""Main API router configuration."""

from fastapi import APIRouter

from .endpoints import users, content, conversations, recommendations, websocket, reading_progress, preferences
from .content_storage import router as content_storage_router

# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(content.router, prefix="/content", tags=["content"])
api_router.include_router(content_storage_router, tags=["content-storage"])
api_router.include_router(conversations.router,
                          prefix="/conversations", tags=["conversations"])
api_router.include_router(recommendations.router,
                          prefix="/recommendations", tags=["recommendations"])
api_router.include_router(preferences.router,
                          prefix="/preferences", tags=["preferences"])
api_router.include_router(reading_progress.router,
                          prefix="/reading-progress", tags=["reading-progress"])
api_router.include_router(websocket.router, prefix="/chat", tags=["websocket"])
