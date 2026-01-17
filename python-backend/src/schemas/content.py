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


class ContentAnalysis(BaseModel):
    """Content analysis results model."""
    topics: List[Dict]
    reading_level: Dict
    complexity: Dict
    embedding: List[float]
    key_phrases: List[str]


class ContentItemCreate(BaseModel):
    """Schema for creating content items."""
    id: str
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


class PurchaseLinkCreate(BaseModel):
    """Schema for creating purchase links."""
    link_id: str
    content_id: str
    link_type: str  # "amazon", "web_search", "library", "alternative_retailer"
    url: str
    display_text: str
    format: Optional[str] = None  # "physical", "digital", "audiobook"
    price: Optional[str] = None
    availability: str = "unknown"


class PurchaseLinkResponse(BaseModel):
    """Schema for purchase link response."""
    link_id: str
    content_id: str
    link_type: str
    url: str
    display_text: str
    format: Optional[str]
    price: Optional[str]
    availability: str
    generated_at: datetime

    class Config:
        from_attributes = True
