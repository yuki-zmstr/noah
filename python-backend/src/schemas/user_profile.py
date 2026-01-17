"""Pydantic schemas for user profile data."""

from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Optional


class TopicPreference(BaseModel):
    """Topic preference model."""
    topic: str
    weight: float
    confidence: float
    last_updated: datetime
    evolution_trend: str  # "increasing", "decreasing", or "stable"


class PreferenceModel(BaseModel):
    """User preference model."""
    topics: List[Dict]
    content_types: List[Dict]
    contextual_preferences: List[Dict]
    evolution_history: List[Dict]


class LanguageReadingLevels(BaseModel):
    """Reading levels for different languages."""
    english: Dict
    japanese: Dict


class ReadingContext(BaseModel):
    """Reading context information."""
    time_of_day: str
    device_type: str
    location: Optional[str] = None
    available_time: Optional[int] = None
    user_mood: Optional[str] = None


class UserProfileCreate(BaseModel):
    """Schema for creating a user profile."""
    user_id: str
    preferences: Optional[PreferenceModel] = None
    reading_levels: Optional[LanguageReadingLevels] = None


class UserProfileResponse(BaseModel):
    """Schema for user profile response."""
    user_id: str
    preferences: Optional[PreferenceModel]
    reading_levels: Optional[LanguageReadingLevels]
    last_updated: datetime
    created_at: datetime

    class Config:
        from_attributes = True
