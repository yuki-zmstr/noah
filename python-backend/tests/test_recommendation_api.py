"""Tests for recommendation API endpoints."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from src.main import app
from src.models.user_profile import UserProfile
from src.models.content import ContentItem
from src.schemas.user_profile import PreferenceModel, LanguageReadingLevels


def test_get_recommendations_basic(client: TestClient, db_session):
    """Test basic recommendations endpoint."""
    # Create a test user profile
    preferences = PreferenceModel(
        topics=[{"topic": "technology", "weight": 0.8, "confidence": 0.9,
                "last_updated": datetime.utcnow().isoformat(), "evolution_trend": "stable"}],
        content_types=[{"type": "article", "preference": 0.7,
                       "last_updated": datetime.utcnow().isoformat()}],
        contextual_preferences=[],
        evolution_history=[]
    )

    reading_levels = LanguageReadingLevels(
        english={"level": 10.0, "confidence": 0.8, "assessment_count": 15},
        japanese={"level": 0.4, "confidence": 0.6, "assessment_count": 8}
    )

    profile = UserProfile(
        user_id="test_api_user",
        preferences=preferences.model_dump(),
        reading_levels=reading_levels.model_dump(),
        created_at=datetime.utcnow(),
        last_updated=datetime.utcnow()
    )

    db_session.add(profile)

    # Create test content
    content = ContentItem(
        id="test_content_api",
        title="Test Technology Article",
        content="This is a test article about technology...",
        language="english",
        content_metadata={
            "author": "Test Author",
            "source": "Test Source",
            "publish_date": datetime.utcnow().isoformat(),
            "content_type": "article",
            "estimated_reading_time": 10,
            "tags": ["technology"]
        },
        analysis={
            "topics": [{"topic": "technology", "confidence": 0.9}],
            "reading_level": {"flesch_kincaid": 10.0, "level": "intermediate"},
            "complexity": {"overall": 0.5, "vocabulary": 0.6, "syntax": 0.4},
            "embedding": [0.1] * 384,
            "key_phrases": ["technology", "innovation"]
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db_session.add(content)
    db_session.commit()

    # Test the recommendations endpoint
    response = client.get("/api/recommendations/users/test_api_user?limit=5")

    assert response.status_code == 200
    data = response.json()

    assert "user_id" in data
    assert "recommendations" in data
    assert "discovery_mode" in data
    assert data["user_id"] == "test_api_user"
    assert data["discovery_mode"] is False


def test_get_discovery_recommendations(client: TestClient, db_session):
    """Test discovery recommendations endpoint."""
    # Create a test user profile with established preferences
    preferences = PreferenceModel(
        topics=[{"topic": "technology", "weight": 0.9, "confidence": 0.9,
                "last_updated": datetime.utcnow().isoformat(), "evolution_trend": "stable"}],
        content_types=[{"type": "article", "preference": 0.8,
                       "last_updated": datetime.utcnow().isoformat()}],
        contextual_preferences=[],
        evolution_history=[]
    )

    reading_levels = LanguageReadingLevels(
        english={"level": 12.0, "confidence": 0.9, "assessment_count": 25},
        japanese={"level": 0.5, "confidence": 0.7, "assessment_count": 12}
    )

    profile = UserProfile(
        user_id="test_discovery_user",
        preferences=preferences.model_dump(),
        reading_levels=reading_levels.model_dump(),
        created_at=datetime.utcnow(),
        last_updated=datetime.utcnow()
    )

    db_session.add(profile)

    # Create diverse content for discovery
    art_content = ContentItem(
        id="test_art_content",
        title="Digital Art and Creativity",
        content="This article explores digital art...",
        language="english",
        content_metadata={
            "author": "Art Expert",
            "source": "Art Magazine",
            "publish_date": datetime.utcnow().isoformat(),
            "content_type": "article",
            "estimated_reading_time": 15,
            "tags": ["art", "creativity"]
        },
        analysis={
            "topics": [
                {"topic": "art", "confidence": 0.9},
                {"topic": "creativity", "confidence": 0.8}
            ],
            "reading_level": {"flesch_kincaid": 11.0, "level": "intermediate"},
            "complexity": {"overall": 0.5, "vocabulary": 0.6, "syntax": 0.4},
            "embedding": [0.2] * 384,
            "key_phrases": ["digital art", "creative process"]
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db_session.add(art_content)
    db_session.commit()

    # Test the discovery endpoint
    response = client.get(
        "/api/recommendations/discovery/test_discovery_user?limit=3")

    assert response.status_code == 200
    data = response.json()

    assert "user_id" in data
    assert "discovery_recommendations" in data
    assert data["user_id"] == "test_discovery_user"


def test_submit_feedback(client: TestClient, db_session):
    """Test feedback submission endpoint."""
    # Create a test user profile
    preferences = PreferenceModel(
        topics=[],
        content_types=[],
        contextual_preferences=[],
        evolution_history=[]
    )

    reading_levels = LanguageReadingLevels(
        english={"level": 8.0, "confidence": 0.5, "assessment_count": 5},
        japanese={"level": 0.3, "confidence": 0.3, "assessment_count": 0}
    )

    profile = UserProfile(
        user_id="test_feedback_user",
        preferences=preferences.model_dump(),
        reading_levels=reading_levels.model_dump(),
        created_at=datetime.utcnow(),
        last_updated=datetime.utcnow()
    )

    db_session.add(profile)

    # Create test content
    content = ContentItem(
        id="test_feedback_content",
        title="Test Feedback Article",
        content="This is a test article for feedback...",
        language="english",
        content_metadata={
            "author": "Test Author",
            "source": "Test Source",
            "publish_date": datetime.utcnow().isoformat(),
            "content_type": "article",
            "estimated_reading_time": 10,
            "tags": ["test"]
        },
        analysis={
            "topics": [{"topic": "test", "confidence": 0.8}],
            "reading_level": {"flesch_kincaid": 8.0, "level": "intermediate"},
            "complexity": {"overall": 0.5, "vocabulary": 0.5, "syntax": 0.5},
            "embedding": [0.1] * 384,
            "key_phrases": ["test", "feedback"]
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db_session.add(content)
    db_session.commit()

    # Test feedback submission
    feedback_data = {
        "content_id": "test_feedback_content",
        "feedback_type": "like",
        "context": {"time_of_day": "evening"}
    }

    response = client.post("/api/recommendations/users/test_feedback_user/feedback",
                           json=feedback_data)

    assert response.status_code == 200
    data = response.json()

    assert "message" in data
    assert "feedback_processed" in data
    assert data["feedback_processed"] is True


def test_user_not_found(client: TestClient):
    """Test error handling when user is not found."""
    response = client.get("/api/recommendations/users/nonexistent_user")

    # Print response for debugging
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.text}")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "User not found"


def test_contextual_recommendations_endpoint(client: TestClient, db_session):
    """Test the new contextual recommendations endpoint."""
    # Create a test user profile
    preferences = PreferenceModel(
        topics=[{"topic": "science", "weight": 0.7, "confidence": 0.8,
                "last_updated": datetime.utcnow().isoformat(), "evolution_trend": "stable"}],
        content_types=[{"type": "book", "preference": 0.6,
                       "last_updated": datetime.utcnow().isoformat()}],
        contextual_preferences=[],
        evolution_history=[]
    )

    reading_levels = LanguageReadingLevels(
        english={"level": 9.0, "confidence": 0.7, "assessment_count": 10},
        japanese={"level": 0.3, "confidence": 0.4, "assessment_count": 3}
    )

    profile = UserProfile(
        user_id="test_contextual_user",
        preferences=preferences.model_dump(),
        reading_levels=reading_levels.model_dump(),
        created_at=datetime.utcnow(),
        last_updated=datetime.utcnow()
    )

    db_session.add(profile)

    # Create test content
    content = ContentItem(
        id="test_contextual_content",
        title="Science Book for Testing",
        content="This is a science book for testing contextual recommendations...",
        language="english",
        content_metadata={
            "author": "Science Author",
            "source": "Science Publisher",
            "publish_date": datetime.utcnow().isoformat(),
            "content_type": "book",
            "estimated_reading_time": 60,
            "tags": ["science", "research"]
        },
        analysis={
            "topics": [{"topic": "science", "confidence": 0.9}],
            "reading_level": {"flesch_kincaid": 9.5, "level": "intermediate"},
            "complexity": {"overall": 0.6, "vocabulary": 0.7, "syntax": 0.5},
            "embedding": [0.3] * 384,
            "key_phrases": ["science", "research", "methodology"]
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db_session.add(content)
    db_session.commit()

    # Test contextual recommendations with context
    request_data = {
        "context": {
            "time_of_day": "afternoon",
            "device_type": "desktop",
            "available_time": 45,
            "user_mood": "focused"
        },
        "limit": 5,
        "language": "english"
    }

    response = client.post("/api/recommendations/users/test_contextual_user/contextual",
                           json=request_data)

    assert response.status_code == 200
    data = response.json()

    assert "user_id" in data
    assert "recommendations" in data
    assert "context_applied" in data
    assert data["user_id"] == "test_contextual_user"
    assert data["context_applied"] is not None
