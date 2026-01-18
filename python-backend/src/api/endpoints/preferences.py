"""Preference transparency and control API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime

from src.database import get_db
from src.models.user_profile import UserProfile
from src.services.user_profile_service import user_profile_engine
from src.schemas.user_profile import PreferenceModel, LanguageReadingLevels

router = APIRouter()


@router.get("/{user_id}/transparency")
async def get_preference_transparency(
    user_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get transparent explanation of learned preferences."""
    try:
        transparency_data = await user_profile_engine.get_preference_transparency(user_id, db)
        return transparency_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get preference transparency: {str(e)}")


@router.put("/{user_id}/preferences")
async def update_user_preferences(
    user_id: str,
    preferences: PreferenceModel,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Update user preferences with immediate effect on recommendations."""
    try:
        # Get existing profile
        profile = await user_profile_engine.get_or_create_profile(user_id, db)
        
        # Update preferences
        profile.preferences = preferences.dict()
        profile.last_updated = datetime.utcnow()
        
        db.commit()
        db.refresh(profile)
        
        # Get updated transparency data to show immediate changes
        transparency_data = await user_profile_engine.get_preference_transparency(user_id, db)
        
        return {
            "message": "Preferences updated successfully",
            "user_id": user_id,
            "updated_preferences": transparency_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update preferences: {str(e)}")


@router.put("/{user_id}/reading-levels")
async def update_reading_levels(
    user_id: str,
    reading_levels: LanguageReadingLevels,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Update user reading levels with immediate effect."""
    try:
        # Get existing profile
        profile = await user_profile_engine.get_or_create_profile(user_id, db)
        
        # Update reading levels
        profile.reading_levels = reading_levels.dict()
        profile.last_updated = datetime.utcnow()
        
        db.commit()
        db.refresh(profile)
        
        return {
            "message": "Reading levels updated successfully",
            "user_id": user_id,
            "updated_reading_levels": reading_levels.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update reading levels: {str(e)}")


@router.post("/{user_id}/preferences/override")
async def override_specific_preference(
    user_id: str,
    preference_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Override a specific preference (topic, content type, or contextual)."""
    try:
        profile = await user_profile_engine.get_or_create_profile(user_id, db)
        preferences = PreferenceModel(**profile.preferences)
        
        preference_type = preference_data.get("type")  # "topic", "content_type", "contextual"
        preference_key = preference_data.get("key")
        new_value = preference_data.get("value")
        
        if preference_type == "topic":
            # Update or add topic preference
            topic_dict = {tp["topic"]: tp for tp in preferences.topics}
            if preference_key in topic_dict:
                topic_dict[preference_key]["weight"] = new_value
                topic_dict[preference_key]["last_updated"] = datetime.utcnow().isoformat()
            else:
                topic_dict[preference_key] = {
                    "topic": preference_key,
                    "weight": new_value,
                    "confidence": 0.8,  # High confidence for manual overrides
                    "last_updated": datetime.utcnow().isoformat(),
                    "evolution_trend": "manual_override"
                }
            preferences.topics = list(topic_dict.values())
            
        elif preference_type == "content_type":
            # Update or add content type preference
            type_dict = {ct["type"]: ct for ct in preferences.content_types}
            if preference_key in type_dict:
                type_dict[preference_key]["preference"] = new_value
                type_dict[preference_key]["last_updated"] = datetime.utcnow().isoformat()
            else:
                type_dict[preference_key] = {
                    "type": preference_key,
                    "preference": new_value,
                    "last_updated": datetime.utcnow().isoformat()
                }
            preferences.content_types = list(type_dict.values())
            
        elif preference_type == "contextual":
            # Update contextual preference
            factor = preference_data.get("factor")
            value = preference_data.get("context_value")
            ctx_key = f"{factor}:{value}"
            
            ctx_dict = {f"{cp['factor']}:{cp.get('value', '')}": cp for cp in preferences.contextual_preferences}
            if ctx_key in ctx_dict:
                ctx_dict[ctx_key]["weight"] = new_value
                ctx_dict[ctx_key]["last_updated"] = datetime.utcnow().isoformat()
            else:
                ctx_dict[ctx_key] = {
                    "factor": factor,
                    "value": value,
                    "weight": new_value,
                    "last_updated": datetime.utcnow().isoformat()
                }
            preferences.contextual_preferences = list(ctx_dict.values())
        
        # Save updated preferences
        profile.preferences = preferences.dict()
        profile.last_updated = datetime.utcnow()
        
        db.commit()
        db.refresh(profile)
        
        return {
            "message": f"Successfully overrode {preference_type} preference",
            "user_id": user_id,
            "preference_type": preference_type,
            "preference_key": preference_key,
            "new_value": new_value
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to override preference: {str(e)}")


@router.get("/{user_id}/evolution")
async def get_preference_evolution(
    user_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get preference evolution analysis."""
    try:
        evolution_data = await user_profile_engine.track_preference_evolution(user_id, db)
        return evolution_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get preference evolution: {str(e)}")