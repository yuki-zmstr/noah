"""Pydantic schemas for reading behavior data."""

from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Optional, Any
from src.schemas.user_profile import ReadingContext


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
    contextual_factors: Dict[str, Any]
    confidence_score: float


class PreferenceSnapshotResponse(BaseModel):
    """Schema for preference snapshot response."""
    id: int
    user_id: str
    timestamp: datetime
    topic_weights: Dict[str, float]
    reading_level_preference: float
    contextual_factors: Dict[str, Any]
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


class SessionProgressUpdate(BaseModel):
    """Schema for session progress updates."""
    completion_rate: Optional[float] = None
    words_read: Optional[int] = None
    time_elapsed: Optional[float] = None  # seconds
    pause_event: Optional[Dict] = None
    interaction_event: Optional[Dict] = None
    engagement_data: Optional[Dict] = None


class SessionAnalytics(BaseModel):
    """Schema for session analytics response."""
    session_id: str
    user_id: str
    content_id: str
    session_duration_minutes: float
    completion_rate: float
    average_reading_speed: float
    performance_score: float
    skill_development_indicators: Dict
    session_quality: str
    adaptive_suggestions: List[Dict]


class ProgressMetrics(BaseModel):
    """Schema for progress metrics."""
    total_sessions: int
    completed_sessions: int
    completion_rate: float
    average_content_completion: float
    average_reading_speed_wpm: float
    average_session_duration_minutes: float
    total_reading_time_hours: float


class SkillDevelopmentTrends(BaseModel):
    """Schema for skill development trends."""
    completion_rate_trend: Dict
    reading_speed_trend: Dict
    skill_development_summary: str


class DifficultyInsights(BaseModel):
    """Schema for difficulty insights."""
    optimal_difficulty_range: Dict
    difficulty_adaptation_needed: str
    language_specific_insights: Dict


class BehavioralPatterns(BaseModel):
    """Schema for behavioral patterns."""
    preferred_reading_times: Optional[Dict] = None
    device_usage: Optional[Dict] = None
    session_length_stats: Optional[Dict] = None


class ProgressAnalyticsResponse(BaseModel):
    """Schema for comprehensive progress analytics."""
    user_id: str
    analysis_period_days: int
    total_sessions: int
    progress_metrics: ProgressMetrics
    skill_development_trends: SkillDevelopmentTrends
    difficulty_insights: DifficultyInsights
    behavioral_patterns: BehavioralPatterns
    recommendations: List[Dict]


class AdaptiveSuggestion(BaseModel):
    """Schema for adaptive suggestions."""
    type: str
    suggestion: str
    priority: str


class PerformanceIndicators(BaseModel):
    """Schema for real-time performance indicators."""
    reading_speed_percentile: Optional[float] = None
    engagement_score: Optional[float] = None
    comprehension_estimate: Optional[float] = None
    overall_performance: Optional[float] = None


class AdaptiveAdjustment(BaseModel):
    """Schema for adaptive adjustments."""
    type: str
    reason: str
    suggestion: str
    urgency: str


class RealTimeRecommendation(BaseModel):
    """Schema for real-time recommendations."""
    type: str
    message: str
    priority: str
