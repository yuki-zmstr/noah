"""User profile and behavior models."""

from sqlalchemy import Column, String, DateTime, Integer, Float, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from src.database import Base


class UserProfile(Base):
    """User profile model storing preferences and reading levels."""

    __tablename__ = "user_profiles"

    user_id = Column(String, primary_key=True)
    preferences = Column(JSON)  # PreferenceModel as JSON
    reading_levels = Column(JSON)  # LanguageReadingLevels as JSON
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    behavior_history = relationship(
        "ReadingBehavior", back_populates="user_profile")
    preference_snapshots = relationship(
        "PreferenceSnapshot", back_populates="user_profile")
    conversation_sessions = relationship(
        "ConversationSession", back_populates="user_profile")
    discovery_recommendations = relationship(
        "DiscoveryRecommendation", back_populates="user_profile")


class ReadingBehavior(Base):
    """Reading behavior tracking model."""

    __tablename__ = "reading_behaviors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(String, ForeignKey("content_items.id"))
    user_id = Column(String, ForeignKey("user_profiles.user_id"))
    session_id = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    completion_rate = Column(Float)
    reading_speed = Column(Float)
    pause_patterns = Column(JSON)  # List of pause events
    interactions = Column(JSON)  # List of interaction events
    context = Column(JSON)  # ReadingContext as JSON
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user_profile = relationship(
        "UserProfile", back_populates="behavior_history")
    content_item = relationship(
        "ContentItem", back_populates="reading_behaviors")


class PreferenceSnapshot(Base):
    """Preference evolution tracking model."""

    __tablename__ = "preference_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("user_profiles.user_id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    topic_weights = Column(JSON)  # Dict mapping topics to weights
    reading_level_preference = Column(Float)
    contextual_factors = Column(JSON)  # Dict of contextual factors
    confidence_score = Column(Float)

    # Relationships
    user_profile = relationship(
        "UserProfile", back_populates="preference_snapshots")
