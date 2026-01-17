"""Test SQLAlchemy models and Pydantic schemas integration."""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base
from src.models import (
    UserProfile, ReadingBehavior, PreferenceSnapshot,
    ContentItem, PurchaseLink, DiscoveryRecommendation,
    ConversationSession, ConversationMessage, ConversationHistory
)
from src.schemas import (
    UserProfileCreate, UserProfileResponse,
    ContentItemCreate, ContentItemResponse,
    ConversationSessionCreate, ConversationSessionResponse
)


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """Create a test database session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_user_profile_model_creation(db_session):
    """Test UserProfile model creation and relationships."""
    # Create user profile
    profile = UserProfile(
        user_id="test_user_123",
        preferences={
            "topics": [{"topic": "fiction", "weight": 0.8}],
            "content_types": [{"type": "book", "preference": 0.9}]
        },
        reading_levels={
            "english": {"level": 7.5, "confidence": 0.8},
            "japanese": {"level": 4.0, "confidence": 0.6}
        }
    )

    db_session.add(profile)
    db_session.commit()

    # Verify creation
    retrieved_profile = db_session.query(UserProfile).filter(
        UserProfile.user_id == "test_user_123"
    ).first()

    assert retrieved_profile is not None
    assert retrieved_profile.user_id == "test_user_123"
    assert retrieved_profile.preferences["topics"][0]["topic"] == "fiction"
    assert retrieved_profile.reading_levels["english"]["level"] == 7.5


def test_content_item_model_creation(db_session):
    """Test ContentItem model creation."""
    content = ContentItem(
        id="content_123",
        title="Test Book",
        content="This is a test book content...",
        language="english",
        content_metadata={
            "author": "Test Author",
            "source": "test_source",
            "publish_date": datetime.utcnow().isoformat(),
            "content_type": "book",
            "estimated_reading_time": 300,
            "tags": ["fiction", "adventure"]
        },
        analysis={
            "topics": [{"topic": "adventure", "confidence": 0.9}],
            "reading_level": {"flesch_kincaid": 8.5},
            "complexity": {"sentence_length": 15.2},
            "embedding": [0.1, 0.2, 0.3],
            "key_phrases": ["adventure", "journey", "hero"]
        }
    )

    db_session.add(content)
    db_session.commit()

    # Verify creation
    retrieved_content = db_session.query(ContentItem).filter(
        ContentItem.id == "content_123"
    ).first()

    assert retrieved_content is not None
    assert retrieved_content.title == "Test Book"
    assert retrieved_content.language == "english"
    assert retrieved_content.content_metadata["author"] == "Test Author"


def test_conversation_models_relationship(db_session):
    """Test conversation models and their relationships."""
    # Create user profile first
    profile = UserProfile(
        user_id="test_user_456",
        preferences={},
        reading_levels={}
    )
    db_session.add(profile)

    # Create conversation session
    session = ConversationSession(
        session_id="session_123",
        user_id="test_user_456",
        context={
            "current_topic": "book_recommendation",
            "preferred_language": "english"
        }
    )
    db_session.add(session)

    # Create conversation message
    message = ConversationMessage(
        message_id="msg_123",
        session_id="session_123",
        sender="user",
        content="Can you recommend a good book?",
        intent={
            "intent": "book_recommendation",
            "confidence": 0.9
        }
    )
    db_session.add(message)
    db_session.commit()

    # Verify relationships
    retrieved_session = db_session.query(ConversationSession).filter(
        ConversationSession.session_id == "session_123"
    ).first()

    assert retrieved_session is not None
    assert retrieved_session.user_id == "test_user_456"
    assert len(retrieved_session.messages) == 1
    assert retrieved_session.messages[0].content == "Can you recommend a good book?"
    assert retrieved_session.user_profile.user_id == "test_user_456"


def test_reading_behavior_tracking(db_session):
    """Test reading behavior model."""
    # Create user profile and content
    profile = UserProfile(user_id="test_user_789",
                          preferences={}, reading_levels={})
    content = ContentItem(
        id="content_456",
        title="Test Article",
        content="Test content",
        language="english",
        content_metadata={}
    )

    db_session.add(profile)
    db_session.add(content)

    # Create reading behavior
    behavior = ReadingBehavior(
        content_id="content_456",
        user_id="test_user_789",
        session_id="reading_session_123",
        start_time=datetime.utcnow(),
        completion_rate=0.85,
        reading_speed=250.0,
        pause_patterns=[{"timestamp": "2024-01-01T10:00:00", "duration": 30}],
        interactions=[{"type": "highlight", "position": 150}],
        context={
            "device_type": "mobile",
            "time_of_day": "evening"
        }
    )

    db_session.add(behavior)
    db_session.commit()

    # Verify creation and relationships
    retrieved_behavior = db_session.query(ReadingBehavior).first()

    assert retrieved_behavior is not None
    assert retrieved_behavior.completion_rate == 0.85
    assert retrieved_behavior.reading_speed == 250.0
    assert retrieved_behavior.user_profile.user_id == "test_user_789"
    assert retrieved_behavior.content_item.title == "Test Article"


def test_pydantic_schema_validation():
    """Test Pydantic schema validation."""
    # Test UserProfileCreate schema
    profile_data = {
        "user_id": "test_user_schema",
        "preferences": {
            "topics": [{"topic": "science", "weight": 0.7}],
            "content_types": [],
            "contextual_preferences": [],
            "evolution_history": []
        },
        "reading_levels": {
            "english": {"level": 6.0, "confidence": 0.7},
            "japanese": {"level": 3.5, "confidence": 0.5}
        }
    }

    profile_create = UserProfileCreate(**profile_data)
    assert profile_create.user_id == "test_user_schema"
    assert profile_create.preferences.topics[0]["topic"] == "science"

    # Test ContentItemCreate schema
    content_data = {
        "id": "content_schema_test",
        "title": "Schema Test Book",
        "content": "Test content for schema validation",
        "language": "english",
        "metadata": {
            "author": "Schema Author",
            "source": "test",
            "publish_date": datetime.utcnow(),
            "content_type": "book",
            "estimated_reading_time": 180,
            "tags": ["test", "schema"]
        }
    }

    content_create = ContentItemCreate(**content_data)
    assert content_create.title == "Schema Test Book"
    assert content_create.metadata.author == "Schema Author"


def test_purchase_link_and_discovery_models(db_session):
    """Test PurchaseLink and DiscoveryRecommendation models."""
    # Create content and user profile
    content = ContentItem(
        id="content_purchase_test",
        title="Purchasable Book",
        content="Great book content",
        language="english",
        content_metadata={}
    )

    profile = UserProfile(
        user_id="test_user_purchase",
        preferences={},
        reading_levels={}
    )

    db_session.add(content)
    db_session.add(profile)

    # Create purchase link
    purchase_link = PurchaseLink(
        link_id="link_123",
        content_id="content_purchase_test",
        link_type="amazon",
        url="https://amazon.com/book/123",
        display_text="Buy on Amazon",
        format="physical",
        price="$15.99",
        availability="available"
    )

    # Create discovery recommendation
    discovery = DiscoveryRecommendation(
        content_id="content_purchase_test",
        user_id="test_user_purchase",
        divergence_score=0.7,
        bridging_topics=["adventure", "mystery"],
        discovery_reason="Genre exploration"
    )

    db_session.add(purchase_link)
    db_session.add(discovery)
    db_session.commit()

    # Verify creation and relationships
    retrieved_link = db_session.query(PurchaseLink).first()
    retrieved_discovery = db_session.query(DiscoveryRecommendation).first()

    assert retrieved_link.link_type == "amazon"
    assert retrieved_link.content_item.title == "Purchasable Book"

    assert retrieved_discovery.divergence_score == 0.7
    assert retrieved_discovery.content_item.title == "Purchasable Book"
    assert retrieved_discovery.user_profile.user_id == "test_user_purchase"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
