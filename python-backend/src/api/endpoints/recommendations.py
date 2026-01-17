"""Recommendation API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from src.database import get_db
from src.models.user_profile import UserProfile
from src.models.content import ContentItem
from src.schemas.user_profile import ReadingContext
from src.services.recommendation_engine import contextual_recommendation_engine
from src.services.discovery_engine import discovery_engine

router = APIRouter()


class RecommendationRequest(BaseModel):
    """Request model for contextual recommendations."""
    context: Optional[ReadingContext] = None
    limit: int = 10
    language: Optional[str] = None


class FeedbackRequest(BaseModel):
    """Request model for recommendation feedback."""
    content_id: str
    feedback_type: str  # "like", "dislike", "interested", "not_interested"
    rating: Optional[float] = None
    context: Optional[dict] = None


class DiscoveryResponseRequest(BaseModel):
    """Request model for discovery response tracking."""
    content_id: str
    response: str  # "interested", "not_interested", "purchased", "saved"


@router.post("/users/{user_id}/contextual")
async def get_contextual_recommendations(
    user_id: str,
    request: RecommendationRequest,
    db: Session = Depends(get_db)
):
    """Get contextual recommendations for a user."""
    # Verify user exists
    user = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        recommendations = await contextual_recommendation_engine.generate_contextual_recommendations(
            user_id=user_id,
            context=request.context,
            limit=request.limit,
            language=request.language,
            db=db
        )

        return {
            "user_id": user_id,
            "recommendations": recommendations,
            "context_applied": request.context.dict() if request.context else None,
            "total_count": len(recommendations)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating recommendations: {str(e)}")


@router.get("/users/{user_id}")
async def get_recommendations(
    user_id: str,
    limit: int = 10,
    language: Optional[str] = None,
    discovery_mode: bool = False,
    db: Session = Depends(get_db)
):
    """Get content recommendations for a user (legacy endpoint)."""
    # Verify user exists
    user = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        if discovery_mode:
            # Use discovery engine
            recommendations = await discovery_engine.generate_discovery_recommendations(
                user_id=user_id,
                limit=limit,
                language=language,
                db=db
            )

            return {
                "user_id": user_id,
                "recommendations": recommendations,
                "discovery_mode": True,
                "total_count": len(recommendations)
            }
        else:
            # Use contextual recommendation engine
            recommendations = await contextual_recommendation_engine.generate_contextual_recommendations(
                user_id=user_id,
                limit=limit,
                language=language,
                db=db
            )

            return {
                "user_id": user_id,
                "recommendations": [
                    {
                        "content_id": rec["content_id"],
                        "title": rec["title"],
                        "language": rec["language"],
                        "metadata": rec["metadata"],
                        "recommendation_score": rec["recommendation_score"],
                        "recommendation_reason": rec["recommendation_reason"]
                    }
                    for rec in recommendations
                ],
                "discovery_mode": False,
                "total_count": len(recommendations)
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating recommendations: {str(e)}")


@router.post("/users/{user_id}/feedback")
async def submit_feedback(
    user_id: str,
    feedback: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """Submit user feedback on recommendations."""
    # Verify user exists
    user = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # Convert feedback to preference update format
        feedback_value = 0.0
        if feedback.feedback_type == "like":
            feedback_value = 0.8
        elif feedback.feedback_type == "dislike":
            feedback_value = -0.8
        elif feedback.feedback_type == "interested":
            feedback_value = 0.6
        elif feedback.feedback_type == "not_interested":
            feedback_value = -0.6
        elif feedback.rating is not None:
            # Convert rating (0-5) to feedback value (-1 to 1)
            feedback_value = (feedback.rating - 2.5) / 2.5

        # Update user preferences
        from src.services.user_profile_service import user_profile_engine

        feedback_data = {
            "type": "explicit",
            "value": feedback_value,
            "context": feedback.context or {}
        }

        await user_profile_engine.update_preferences_from_feedback(
            user_id, feedback.content_id, feedback_data, db
        )

        return {
            "message": "Feedback received and preferences updated",
            "user_id": user_id,
            "content_id": feedback.content_id,
            "feedback_processed": True
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing feedback: {str(e)}")


@router.get("/discovery/{user_id}")
async def get_discovery_recommendations(
    user_id: str,
    limit: int = 5,
    language: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get discovery mode recommendations that diverge from user preferences."""
    # Verify user exists
    user = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        recommendations = await discovery_engine.generate_discovery_recommendations(
            user_id=user_id,
            limit=limit,
            language=language,
            db=db
        )

        return {
            "user_id": user_id,
            "discovery_recommendations": recommendations,
            "total_count": len(recommendations)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating discovery recommendations: {str(e)}")


@router.post("/discovery/{user_id}/response")
async def track_discovery_response(
    user_id: str,
    response: DiscoveryResponseRequest,
    db: Session = Depends(get_db)
):
    """Track user response to discovery recommendation."""
    # Verify user exists
    user = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        await discovery_engine.track_discovery_response(
            user_id=user_id,
            content_id=response.content_id,
            response=response.response,
            db=db
        )

        return {
            "message": "Discovery response tracked successfully",
            "user_id": user_id,
            "content_id": response.content_id,
            "response": response.response
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error tracking discovery response: {str(e)}")
