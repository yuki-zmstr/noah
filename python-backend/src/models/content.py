"""Content and recommendation models."""

from sqlalchemy import Column, String, DateTime, Integer, Float, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from src.database import Base


class ContentItem(Base):
    """Content item model for books and articles."""

    __tablename__ = "content_items"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    language = Column(String, nullable=False)  # "english" or "japanese"
    content_metadata = Column(JSON)  # ContentMetadata as JSON
    analysis = Column(JSON)  # ContentAnalysis as JSON
    adaptations = Column(JSON)  # List of ContentAdaptation as JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Relationships
    reading_behaviors = relationship(
        "ReadingBehavior", back_populates="content_item")
    discovery_recommendations = relationship(
        "DiscoveryRecommendation", back_populates="content_item")


class DiscoveryRecommendation(Base):
    """Discovery mode recommendation tracking."""

    __tablename__ = "discovery_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(String, ForeignKey("content_items.id"))
    user_id = Column(String, ForeignKey("user_profiles.user_id"))
    divergence_score = Column(Float, nullable=False)
    bridging_topics = Column(JSON)  # List of topics
    discovery_reason = Column(String, nullable=False)
    # "interested", "not_interested", "purchased", "saved"
    user_response = Column(String)
    response_timestamp = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    content_item = relationship(
        "ContentItem", back_populates="discovery_recommendations")
    user_profile = relationship(
        "UserProfile", back_populates="discovery_recommendations")
