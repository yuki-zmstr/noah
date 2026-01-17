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
    ConversationMessageCreate,
    ConversationMessageResponse,
    ConversationSessionCreate,
    ConversationSessionResponse,
    ConversationContext
)

__all__ = [
    "UserProfileCreate",
    "UserProfileResponse",
    "PreferenceModel",
    "LanguageReadingLevels",
    "ReadingContext",
    "TopicPreference",
    "ContentItemCreate",
    "ContentItemResponse",
    "ContentMetadata",
    "ContentAnalysis",
    "PurchaseLinkCreate",
    "PurchaseLinkResponse",
    "ConversationMessageCreate",
    "ConversationMessageResponse",
    "ConversationSessionCreate",
    "ConversationSessionResponse",
    "ConversationContext",
]
