"""Pydantic schemas for content data."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Optional


class ContentMetadata(BaseModel):
    """Content metadata model."""
    author: str
    source: str
    publish_date: datetime
    content_type: str
    estimated_reading_time: int
    tags: List[str]
    # Enhanced metadata fields
    word_count: Optional[int] = None
    reading_level: Optional[str] = None
    complexity_score: Optional[float] = None
    key_topics: Optional[List[str]] = None
    language_specific_metrics: Optional[Dict] = None
    ingestion_timestamp: Optional[str] = None
    user_context: Optional[str] = None


class ContentAnalysis(BaseModel):
    """Content analysis results model."""
    topics: List[Dict]
    reading_level: Dict
    complexity: Dict
    embedding: List[float]
    key_phrases: List[str]


class ContentItemCreate(BaseModel):
    """Schema for creating content items."""
    id: Optional[str] = None  # Will be generated if not provided
    title: str
    content: str
    language: str  # "english" or "japanese"
    metadata: ContentMetadata
    analysis: Optional[ContentAnalysis] = None


class ContentItemResponse(BaseModel):
    """Schema for content item response."""
    id: str
    title: str
    content: str
    language: str
    metadata: ContentMetadata = Field(alias="content_metadata")
    analysis: Optional[ContentAnalysis]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class SavedContentRequest(BaseModel):
    """Schema for saving content for a user."""
    content_id: str
    user_id: str
    user_rating: Optional[int] = Field(None, ge=1, le=5)
    user_notes: Optional[str] = None
    tags: Optional[List[str]] = []
    save_reason: Optional[str] = None
    user_metadata: Optional[Dict] = None


class SavedContentResponse(BaseModel):
    """Schema for saved content response."""
    content_id: str
    user_id: str
    saved_at: datetime
    user_rating: Optional[int]
    user_notes: Optional[str]
    tags: List[str]
    save_reason: Optional[str]
    content_title: str
    content_language: str


class ContentSearchRequest(BaseModel):
    """Schema for content search request."""
    query_text: str
    language: Optional[str] = None
    reading_level: Optional[str] = None
    user_id: Optional[str] = None
    limit: int = Field(10, ge=1, le=50)
    include_user_content: bool = True


class ContentSearchResult(BaseModel):
    """Schema for individual search result."""
    content: ContentItemResponse
    similarity_score: float
    match_metadata: Dict


class ContentSearchResponse(BaseModel):
    """Schema for content search response."""
    query_text: str
    results: List[ContentSearchResult]
    total_results: int
    search_method: str  # "vector_similarity" or "text_based_fallback"


class ContentRecommendationRequest(BaseModel):
    """Schema for content recommendation request."""
    user_id: str
    topics: Optional[List[str]] = None
    language: Optional[str] = None
    reading_level: Optional[str] = None
    limit: int = Field(10, ge=1, le=20)
    exclude_saved: bool = True


class ContentIngestionRequest(BaseModel):
    """Schema for content ingestion request."""
    title: str
    content: str
    language: str
    author: Optional[str] = "Unknown"
    source: Optional[str] = "Manual Input"
    content_type: Optional[str] = "article"
    tags: Optional[List[str]] = []
    user_id: Optional[str] = None
