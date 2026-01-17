"""Pydantic schemas for reading behavior data."""

from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Optional


class ReadingBehaviorCreate(BaseModel):
    """Schema for creating reading behavior records."""
    content_id: str
    user_id: str
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    completion_rate: Optional[float] = None
    reading_speed: Optional[float] = None
    pause_patterns: Optional[List[Dict]] = None
    interactions: Optional[List[Dict]] = None
    context: Optional[Dict] = None


class ReadingBehaviorResponse(BaseModel):
    """Schema for reading behavior response."""
    id: int
    content_id: str
    user_id: str
    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    completion_rate: Optional[float]
    reading_speed: Optional[float]
    pause_patterns: Optional[List[Dict]]
    interactions: Optional[List[Dict]]
    context: Optional[Dict]
    created_at: datetime

    class Config:
        from_attributes = True


class PreferenceSnapshotCreate(BaseModel):
    """Schema for creating preference snapshots."""
    user_id: str
    topic_weights: Dict[str, float]
    reading_level_preference: float
    contextual_factors: Dict[str, any]
    confidence_score: float


class PreferenceSnapshotResponse(BaseModel):
    """Schema for preference snapshot response."""
    id: int
    user_id: str
    timestamp: datetime
    topic_weights: Dict[str, float]
    reading_level_preference: float
    contextual_factors: Dict[str, any]
    confidence_score: float

    class Config:
        from_attributes = True


class DiscoveryRecommendationCreate(BaseModel):
    """Schema for creating discovery recommendations."""
    content_id: str
    user_id: str
    divergence_score: float
    bridging_topics: List[str]
    discovery_reason: str


class DiscoveryRecommendationResponse(BaseModel):
    """Schema for discovery recommendation response."""
    id: int
    content_id: str
    user_id: str
    divergence_score: float
    bridging_topics: List[str]
    discovery_reason: str
    user_response: Optional[str]
    response_timestamp: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class RecommendationRequest(BaseModel):
    """Schema for recommendation requests."""
    user_id: str
    context: Optional[ReadingContext] = None
    discovery_mode: bool = False
    language_preference: Optional[str] = None
    max_results: int = 5


class RecommendationResponse(BaseModel):
    """Schema for recommendation responses."""
    content_id: str
    title: str
    author: str
    interest_score: float
    reading_level_match: float
    recommendation_reason: str
    purchase_links: Optional[List[Dict]] = None
