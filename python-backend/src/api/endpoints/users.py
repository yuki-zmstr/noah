"""User profile API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.database import get_db
from src.models.user_profile import UserProfile
from src.schemas.user_profile import UserProfileCreate, UserProfileResponse

router = APIRouter()


@router.post("/", response_model=UserProfileResponse)
async def create_user_profile(
    user_profile: UserProfileCreate,
    db: Session = Depends(get_db)
):
    """Create a new user profile."""
    # Check if user already exists
    existing_user = db.query(UserProfile).filter(
        UserProfile.user_id == user_profile.user_id
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400, detail="User profile already exists")

    # Create new user profile
    db_user = UserProfile(
        user_id=user_profile.user_id,
        preferences=user_profile.preferences.dict() if user_profile.preferences else None,
        reading_levels=user_profile.reading_levels.dict(
        ) if user_profile.reading_levels else None
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get user profile by ID."""
    user = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")

    return user


@router.put("/{user_id}", response_model=UserProfileResponse)
async def update_user_profile(
    user_id: str,
    user_profile: UserProfileCreate,
    db: Session = Depends(get_db)
):
    """Update user profile."""
    user = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")

    # Update fields
    if user_profile.preferences:
        user.preferences = user_profile.preferences.dict()
    if user_profile.reading_levels:
        user.reading_levels = user_profile.reading_levels.dict()

    db.commit()
    db.refresh(user)

    return user


@router.delete("/{user_id}")
async def delete_user_profile(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Delete user profile."""
    user = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")

    db.delete(user)
    db.commit()

    return {"message": "User profile deleted successfully"}
