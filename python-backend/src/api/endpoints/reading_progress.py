"""Reading progress tracking API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Optional

from src.database import get_db
from src.schemas.reading_behavior import ReadingBehaviorCreate, ReadingBehaviorResponse
from src.schemas.user_profile import ReadingContext
from src.services.reading_progress_service import reading_progress_tracker
from pydantic import BaseModel

router = APIRouter()


class StartSessionRequest(BaseModel):
    """Request schema for starting a reading session."""
    user_id: str
    content_id: str
    context: Optional[ReadingContext] = None


class UpdateProgressRequest(BaseModel):
    """Request schema for updating reading progress."""
    session_id: str
    progress_data: Dict


class CompleteSessionRequest(BaseModel):
    """Request schema for completing a reading session."""
    session_id: str
    completion_data: Dict


class ProgressAnalyticsRequest(BaseModel):
    """Request schema for progress analytics."""
    user_id: str
    time_period_days: int = 30


@router.post("/sessions/start")
async def start_reading_session(
    request: StartSessionRequest,
    db: Session = Depends(get_db)
):
    """Start a new reading session with adaptive difficulty assessment."""
    try:
        session_data = await reading_progress_tracker.start_reading_session(
            request.user_id, request.content_id, request.context, db
        )
        return {
            "success": True,
            "data": session_data
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start reading session: {str(e)}")


@router.put("/sessions/progress")
async def update_reading_progress(
    request: UpdateProgressRequest,
    db: Session = Depends(get_db)
):
    """Update reading progress with real-time behavioral metrics."""
    try:
        progress_update = await reading_progress_tracker.update_reading_progress(
            request.session_id, request.progress_data, db
        )
        return {
            "success": True,
            "data": progress_update
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update progress: {str(e)}")


@router.post("/sessions/complete")
async def complete_reading_session(
    request: CompleteSessionRequest,
    db: Session = Depends(get_db)
):
    """Complete a reading session and perform comprehensive analysis."""
    try:
        completion_summary = await reading_progress_tracker.complete_reading_session(
            request.session_id, request.completion_data, db
        )
        return {
            "success": True,
            "data": completion_summary
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to complete session: {str(e)}")


@router.get("/analytics/{user_id}")
async def get_progress_analytics(
    user_id: str,
    time_period_days: int = 30,
    db: Session = Depends(get_db)
):
    """Get comprehensive progress analytics for a user."""
    try:
        analytics = await reading_progress_tracker.get_progress_analytics(
            user_id, time_period_days, db
        )
        return {
            "success": True,
            "data": analytics
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.get("/sessions/{session_id}/status")
async def get_session_status(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get current status of a reading session."""
    try:
        from src.models.user_profile import ReadingBehavior

        behavior = db.query(ReadingBehavior).filter(
            ReadingBehavior.session_id == session_id
        ).first()

        if not behavior:
            raise HTTPException(
                status_code=404, detail="Reading session not found")

        session_status = {
            "session_id": session_id,
            "user_id": behavior.user_id,
            "content_id": behavior.content_id,
            "start_time": behavior.start_time.isoformat(),
            "end_time": behavior.end_time.isoformat() if behavior.end_time else None,
            "completion_rate": behavior.completion_rate,
            "reading_speed": behavior.reading_speed,
            "is_completed": behavior.end_time is not None,
            "context": behavior.context
        }

        return {
            "success": True,
            "data": session_status
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get session status: {str(e)}")


@router.get("/users/{user_id}/recent-sessions")
async def get_recent_sessions(
    user_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get recent reading sessions for a user."""
    try:
        from src.models.user_profile import ReadingBehavior
        from sqlalchemy import desc

        recent_sessions = db.query(ReadingBehavior).filter(
            ReadingBehavior.user_id == user_id
        ).order_by(desc(ReadingBehavior.created_at)).limit(limit).all()

        sessions_data = []
        for session in recent_sessions:
            sessions_data.append({
                "session_id": session.session_id,
                "content_id": session.content_id,
                "start_time": session.start_time.isoformat(),
                "end_time": session.end_time.isoformat() if session.end_time else None,
                "completion_rate": session.completion_rate,
                "reading_speed": session.reading_speed,
                "is_completed": session.end_time is not None,
                "created_at": session.created_at.isoformat()
            })

        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "sessions": sessions_data,
                "total_sessions": len(sessions_data)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get recent sessions: {str(e)}")


@router.get("/users/{user_id}/skill-insights")
async def get_skill_insights(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get skill development insights for a user."""
    try:
        insights = await reading_progress_tracker._generate_skill_development_insights(user_id, db)
        return {
            "success": True,
            "data": insights
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get skill insights: {str(e)}")


@router.get("/users/{user_id}/difficulty-recommendations")
async def get_difficulty_recommendations(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get adaptive difficulty recommendations for a user."""
    try:
        from src.models.user_profile import ReadingBehavior
        from sqlalchemy import desc
        from datetime import datetime, timedelta

        # Get the most recent completed session for analysis
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        recent_behavior = db.query(ReadingBehavior).filter(
            ReadingBehavior.user_id == user_id,
            ReadingBehavior.end_time.isnot(None),
            ReadingBehavior.created_at >= cutoff_date
        ).order_by(desc(ReadingBehavior.created_at)).first()

        if not recent_behavior:
            return {
                "success": True,
                "data": {
                    "message": "No recent completed sessions found",
                    "recommendations": []
                }
            }

        # Analyze the recent session
        session_analysis = await reading_progress_tracker._analyze_completed_session(recent_behavior, db)

        # Get difficulty recommendations
        recommendations = await reading_progress_tracker._update_difficulty_recommendations(
            user_id, session_analysis, db
        )

        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "based_on_session": recent_behavior.session_id,
                "session_performance": session_analysis["performance_score"],
                "recommendations": recommendations
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get difficulty recommendations: {str(e)}")


@router.get("/users/{user_id}/skill-progression")
async def get_skill_progression(
    user_id: str,
    content_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get skill progression analysis for a user."""
    try:
        if not content_id:
            # Get the most recent content
            from src.models.user_profile import ReadingBehavior
            from sqlalchemy import desc

            recent_behavior = db.query(ReadingBehavior).filter(
                ReadingBehavior.user_id == user_id,
                ReadingBehavior.end_time.isnot(None)
            ).order_by(desc(ReadingBehavior.created_at)).first()

            if not recent_behavior:
                raise HTTPException(
                    status_code=404, detail="No completed sessions found")
            content_id = recent_behavior.content_id

        # Calculate performance data from recent session
        # This would come from actual session analysis
        performance_data = {"performance_score": 0.7}

        progression = await reading_progress_tracker.assess_skill_progression(
            user_id, content_id, performance_data, db
        )

        return {
            "success": True,
            "data": progression
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get skill progression: {str(e)}")


@router.get("/users/{user_id}/learning-path")
async def get_learning_path(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get personalized learning path for a user."""
    try:
        learning_path = await reading_progress_tracker.generate_personalized_learning_path(user_id, db)

        return {
            "success": True,
            "data": learning_path
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate learning path: {str(e)}")


@router.post("/users/{user_id}/difficulty-adjustment")
async def track_difficulty_adjustment(
    user_id: str,
    adjustment_data: Dict,
    db: Session = Depends(get_db)
):
    """Track an adaptive difficulty adjustment."""
    try:
        await reading_progress_tracker.track_adaptive_difficulty_adjustment(
            user_id=user_id,
            content_id=adjustment_data["content_id"],
            original_difficulty=adjustment_data["original_difficulty"],
            adjusted_difficulty=adjustment_data["adjusted_difficulty"],
            adjustment_reason=adjustment_data["reason"],
            db=db
        )

        return {
            "success": True,
            "message": "Difficulty adjustment tracked successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to track difficulty adjustment: {str(e)}")
