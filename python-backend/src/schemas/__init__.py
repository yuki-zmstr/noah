"""Pydantic schemas for API request/response validation."""

from .user_profile import (
    UserProfileCreate,
    UserProfileResponse,
    PreferenceModel,
    LanguageReadingLevels,
    ReadingContext,
    TopicPreference
)
from .content import (
    ContentItemCreate,
    ContentItemResponse,
    ContentMetadata,
    ContentAnalysis,
    PurchaseLinkCreate,
    PurchaseLinkResponse
)
from .conversation import (
    ConversationSessionCreate,
    ConversationSessionResponse,
    ConversationMessageCreate,
    ConversationMessageResponse,
    ConversationContext
)

__all__ = [
    # User Profile schemas
    "UserProfileCreate",
    "UserProfileResponse",
    "PreferenceModel",
    "LanguageReadingLevels",
    "ReadingContext",
    "TopicPreference",

    # Content schemas
    "ContentItemCreate",
    "ContentItemResponse",
    "ContentMetadata",
    "ContentAnalysis",
    "PurchaseLinkCreate",
    "PurchaseLinkResponse",

    # Conversation schemas
    "ConversationSessionCreate",
    "ConversationSessionResponse",
    "ConversationMessageCreate",
    "ConversationMessageResponse",
    "ConversationContext"
]
