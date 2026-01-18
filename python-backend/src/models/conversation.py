"""Conversation and messaging models."""

from sqlalchemy import Column, String, DateTime, Integer, JSON, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from src.database import Base


class ConversationSession(Base):
    """Conversation session model."""

    __tablename__ = "conversation_sessions"

    session_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("user_profiles.user_id"))
    context = Column(JSON)  # ConversationContext as JSON
    start_time = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    is_persistent = Column(Boolean, default=True)

    # Relationships
    messages = relationship("ConversationMessage", back_populates="session")
    user_profile = relationship(
        "UserProfile", back_populates="conversation_sessions")


class ConversationMessage(Base):
    """Individual conversation message model."""

    __tablename__ = "conversation_messages"

    message_id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("conversation_sessions.session_id"))
    sender = Column(String, nullable=False)  # "user" or "noah"
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    intent = Column(JSON)  # UserIntent as JSON
    recommendations = Column(JSON)  # List of ContentRecommendation

    # Relationships
    session = relationship("ConversationSession", back_populates="messages")


class ConversationHistory(Base):
    """Conversation history summary model."""

    __tablename__ = "conversation_histories"

    user_id = Column(String, primary_key=True)
    total_messages = Column(Integer, default=0)
    first_interaction = Column(DateTime)
    last_interaction = Column(DateTime)
    conversation_summaries = Column(JSON)  # List of ConversationSummary
