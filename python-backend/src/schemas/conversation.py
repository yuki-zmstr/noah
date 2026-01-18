"""Pydantic schemas for conversation data."""

from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Optional


class ConversationContext(BaseModel):
    """Conversation context model."""
    current_topic: Optional[str] = None
    recent_recommendations: List[str] = []
    user_mood: Optional[str] = None
    discovery_mode_active: bool = False
    preferred_language: str = "english"  # "english" or "japanese"


class ConversationMessageCreate(BaseModel):
    """Schema for creating conversation messages."""
    message_id: str
    session_id: str
    sender: str  # "user" or "noah"
    content: str
    intent: Optional[Dict] = None
    recommendations: Optional[List[Dict]] = None


class ConversationMessageResponse(BaseModel):
    """Schema for conversation message response."""
    message_id: str
    session_id: str
    sender: str
    content: str
    timestamp: datetime
    intent: Optional[Dict]
    recommendations: Optional[List[Dict]]

    class Config:
        from_attributes = True


class ConversationSessionCreate(BaseModel):
    """Schema for creating conversation sessions."""
    session_id: str
    user_id: str
    context: Optional[ConversationContext] = None
    is_persistent: bool = True


class ConversationSessionResponse(BaseModel):
    """Schema for conversation session response."""
    session_id: str
    user_id: str
    context: Optional[ConversationContext]
    start_time: datetime
    last_activity: datetime
    is_persistent: bool

    class Config:
        from_attributes = True
