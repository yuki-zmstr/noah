"""FastAPI dependencies for database and services."""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from src.database import get_db
from src.services.database import db_service
from src.services.agent_core import AgentCoreService
from src.models.user_profile import UserProfile


def get_database_service():
    """Dependency to get database service."""
    return db_service


def get_agent_core_service():
    """Dependency to get AWS Agent Core service."""
    return AgentCoreService()


async def get_user_profile(
    user_id: str,
    db: Session = Depends(get_db)
) -> UserProfile:
    """Dependency to get user profile with validation."""
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == user_id).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User profile not found for user_id: {user_id}"
        )

    return profile


async def get_or_create_user_profile(
    user_id: str,
    db: Session = Depends(get_db),
    db_service=Depends(get_database_service)
) -> UserProfile:
    """Dependency to get or create user profile."""
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == user_id).first()

    if not profile:
        # Create new profile with Agent Core integration
        profile = await db_service.create_user_profile_with_agent_core(
            db=db,
            user_id=user_id
        )
        db.commit()

    return profile


class UserContext:
    """User context for request processing."""

    def __init__(self, user_id: str, profile: UserProfile):
        self.user_id = user_id
        self.profile = profile
        self.preferences = profile.preferences or {}
        self.reading_levels = profile.reading_levels or {}


async def get_user_context(
    user_id: str,
    profile: UserProfile = Depends(get_or_create_user_profile)
) -> UserContext:
    """Dependency to get user context."""
    return UserContext(user_id=user_id, profile=profile)
