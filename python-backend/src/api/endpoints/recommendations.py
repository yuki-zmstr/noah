"""Recommendation API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from src.database import get_db
from src.models.user_profile import UserProfile
from src.models.content import ContentItem

router = APIRouter()


@router.get("/users/{user_id}")
async def get_recommendations(
    user_id: str,
    limit: int = 10,
    language: Optional[str] = None,
    discovery_mode: bool = False,
    db: Session = Depends(get_db)
):
    """Get content recommendations for a user."""
    # Verify user exists
    user = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Basic recommendation logic (to be enhanced with AWS Agent Core)
    query = db.query(ContentItem)

    if language:
        query = query.filter(ContentItem.language == language)

    # For now, return random content (will be replaced with intelligent recommendations)
    recommendations = query.limit(limit).all()

    return {
        "user_id": user_id,
        "recommendations": [
            {
                "content_id": item.id,
                "title": item.title,
                "language": item.language,
                "metadata": item.content_metadata,
                "recommendation_score": 0.8,  # Placeholder
                "recommendation_reason": "Based on your reading preferences"  # Placeholder
            }
            for item in recommendations
        ],
        "discovery_mode": discovery_mode
    }


@router.post("/users/{user_id}/feedback")
async def submit_feedback(
    user_id: str,
    feedback_data: dict,
    db: Session = Depends(get_db)
):
    """Submit user feedback on recommendations."""
    # Verify user exists
    user = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Process feedback (to be enhanced with preference learning)
    # For now, just acknowledge receipt

    return {
        "message": "Feedback received successfully",
        "user_id": user_id,
        "feedback_processed": True
    }


@router.get("/discovery/{user_id}")
async def get_discovery_recommendations(
    user_id: str,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """Get discovery mode recommendations that diverge from user preferences."""
    # Verify user exists
    user = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Discovery logic (to be enhanced)
    content_items = db.query(ContentItem).limit(limit).all()

    return {
        "user_id": user_id,
        "discovery_recommendations": [
            {
                "content_id": item.id,
                "title": item.title,
                "language": item.language,
                "divergence_score": 0.7,  # Placeholder
                "discovery_reason": "Exploring new genres outside your usual preferences"
            }
            for item in content_items
        ]
    }
