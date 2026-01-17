"""Tests for the contextual recommendation engine."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.services.recommendation_engine import contextual_recommendation_engine
from src.models.user_profile import UserProfile, ReadingBehavior
from src.models.content import ContentItem
from src.schemas.user_profile import ReadingContext, PreferenceModel, LanguageReadingLevels
from src.schemas.content import ContentMetadata, ContentAnalysis


@pytest.fixture
def sample_user_profile(db_session: Session):
    """Create a sample user profile for testing."""
    preferences = PreferenceModel(
        topics=[
            {"topic": "technology", "weight": 0.8, "confidence": 0.9,
             "last_updated": datetime.utcnow().isoformat(), "evolution_trend": "stable"},
            {"topic": "science", "weight": 0.6, "confidence": 0.7,
             "last_updated": datetime.utcnow().isoformat(), "evolution_trend": "increasing"}
        ],
        content_types=[
            {"type": "article", "preference": 0.7,
                "last_updated": datetime.utcnow().isoformat()},
            {"type": "book", "preference": 0.5,
                "last_updated": datetime.utcnow().isoformat()}
        ],
        contextual_preferences=[
            {"factor": "time_of_day", "value": "evening", "weight": 0.6,
             "last_updated": datetime.utcnow().isoformat()}
        ],
        evolution_history=[]
    )

    reading_levels = LanguageReadingLevels(
        english={"level": 10.0, "confidence": 0.8, "assessment_count": 15},
        japanese={"level": 0.4, "confidence": 0.6, "assessment_count": 8}
    )

    profile = UserProfile(
        user_id="test_user_1",
        preferences=preferences.model_dump(),
        reading_levels=reading_levels.model_dump(),
        created_at=datetime.utcnow(),
        last_updated=datetime.utcnow()
    )

    db_session.add(profile)
    db_session.commit()
    return profile


@pytest.fixture
def sample_content_items(db_session: Session):
    """Create sample content items for testing."""
    content_items = []

    # Technology article - should match user preferences
    tech_metadata = {
        "author": "Tech Author",
        "source": "Tech Blog",
        "publish_date": datetime.utcnow().isoformat(),
        "content_type": "article",
        "estimated_reading_time": 15,
        "tags": ["technology", "programming"]
    }

    tech_analysis = {
        "topics": [
            {"topic": "technology", "confidence": 0.9},
            {"topic": "programming", "confidence": 0.8}
        ],
        "reading_level": {"flesch_kincaid": 10.5, "level": "advanced"},
        "complexity": {"overall": 0.6, "vocabulary": 0.7, "syntax": 0.5},
        "embedding": [0.1] * 384,  # Mock embedding
        "key_phrases": ["artificial intelligence",
                        "machine learning", "programming"]
    }

    tech_content = ContentItem(
        id="content_tech_1",
        title="Advanced AI Programming Techniques",
        content="This article discusses advanced programming techniques for AI development...",
        language="english",
        content_metadata=tech_metadata,
        analysis=tech_analysis,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    # Science book - partially matches preferences
    science_metadata = {
        "author": "Science Author",
        "source": "Science Publisher",
        "publish_date": datetime.utcnow().isoformat(),
        "content_type": "book",
        "estimated_reading_time": 120,
        "tags": ["science", "physics"]
    }

    science_analysis = {
        "topics": [
            {"topic": "science", "confidence": 0.8},
            {"topic": "physics", "confidence": 0.9}
        ],
        "reading_level": {"flesch_kincaid": 9.0, "level": "intermediate"},
        "complexity": {"overall": 0.5, "vocabulary": 0.6, "syntax": 0.4},
        "embedding": [0.2] * 384,
        "key_phrases": ["quantum physics", "scientific method", "research"]
    }

    science_content = ContentItem(
        id="content_science_1",
        title="Introduction to Quantum Physics",
        content="This book provides an introduction to quantum physics concepts...",
        language="english",
        content_metadata=science_metadata,
        analysis=science_analysis,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    # History article - doesn't match preferences (for diversity testing)
    history_metadata = {
        "author": "History Author",
        "source": "History Magazine",
        "publish_date": datetime.utcnow().isoformat(),
        "content_type": "article",
        "estimated_reading_time": 20,
        "tags": ["history", "medieval"]
    }

    history_analysis = {
        "topics": [
            {"topic": "history", "confidence": 0.9},
            {"topic": "medieval", "confidence": 0.7}
        ],
        "reading_level": {"flesch_kincaid": 11.0, "level": "advanced"},
        "complexity": {"overall": 0.7, "vocabulary": 0.8, "syntax": 0.6},
        "embedding": [0.3] * 384,
        "key_phrases": ["medieval period",
                        "historical analysis", "ancient civilizations"]
    }

    history_content = ContentItem(
        id="content_history_1",
        title="Medieval European History",
        content="This article explores the medieval period in European history...",
        language="english",
        content_metadata=history_metadata,
        analysis=history_analysis,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    content_items = [tech_content, science_content, history_content]

    for item in content_items:
        db_session.add(item)

    db_session.commit()
    return content_items


@pytest.mark.asyncio
async def test_generate_contextual_recommendations_basic(db_session: Session, sample_user_profile, sample_content_items):
    """Test basic contextual recommendation generation."""
    user_id = sample_user_profile.user_id

    recommendations = await contextual_recommendation_engine.generate_contextual_recommendations(
        user_id=user_id,
        limit=10,
        db=db_session
    )

    assert len(recommendations) > 0
    assert all("content_id" in rec for rec in recommendations)
    assert all("recommendation_score" in rec for rec in recommendations)
    assert all("recommendation_reason" in rec for rec in recommendations)

    # Check that recommendations are sorted by score
    scores = [rec["recommendation_score"] for rec in recommendations]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_contextual_recommendations_with_context(db_session: Session, sample_user_profile, sample_content_items):
    """Test contextual recommendations with specific reading context."""
    user_id = sample_user_profile.user_id

    context = ReadingContext(
        time_of_day="evening",
        device_type="tablet",
        available_time=20,
        user_mood="focused"
    )

    recommendations = await contextual_recommendation_engine.generate_contextual_recommendations(
        user_id=user_id,
        context=context,
        limit=5,
        db=db_session
    )

    assert len(recommendations) > 0

    # Check that contextual factors are included
    for rec in recommendations:
        assert "contextual_factors" in rec
        assert "score_breakdown" in rec


@pytest.mark.asyncio
async def test_reading_level_filtering(db_session: Session, sample_user_profile, sample_content_items):
    """Test that content is filtered by appropriate reading level."""
    user_id = sample_user_profile.user_id

    recommendations = await contextual_recommendation_engine.generate_contextual_recommendations(
        user_id=user_id,
        limit=10,
        db=db_session
    )

    # All recommendations should be at appropriate reading level
    for rec in recommendations:
        if rec["language"] == "english":
            analysis = ContentAnalysis(**rec["analysis"])
            content_level = analysis.reading_level.get("flesch_kincaid", 8.0)
            user_level = 10.0  # From sample profile

            # Should be within reasonable range
            assert abs(content_level - user_level) <= 3.0


@pytest.mark.asyncio
async def test_language_filtering(db_session: Session, sample_user_profile, sample_content_items):
    """Test language-specific recommendations."""
    user_id = sample_user_profile.user_id

    # Test English recommendations
    english_recs = await contextual_recommendation_engine.generate_contextual_recommendations(
        user_id=user_id,
        language="english",
        limit=10,
        db=db_session
    )

    assert all(rec["language"] == "english" for rec in english_recs)


@pytest.mark.asyncio
async def test_preference_scoring(db_session: Session, sample_user_profile, sample_content_items):
    """Test that content matching user preferences gets higher scores."""
    user_id = sample_user_profile.user_id

    recommendations = await contextual_recommendation_engine.generate_contextual_recommendations(
        user_id=user_id,
        limit=10,
        db=db_session
    )

    # Find technology and history content in recommendations
    tech_rec = None
    history_rec = None

    for rec in recommendations:
        if "technology" in rec["title"].lower():
            tech_rec = rec
        elif "history" in rec["title"].lower():
            history_rec = rec

    # Technology content should score higher than history (based on user preferences)
    if tech_rec and history_rec:
        assert tech_rec["recommendation_score"] > history_rec["recommendation_score"]


@pytest.mark.asyncio
async def test_diversity_filtering(db_session: Session, sample_user_profile, sample_content_items):
    """Test that diversity filtering prevents filter bubbles."""
    user_id = sample_user_profile.user_id

    # Add more similar content to test diversity
    similar_content = ContentItem(
        id="content_tech_2",
        title="Another AI Programming Article",
        content="Another article about AI programming...",
        language="english",
        content_metadata={
            "author": "Another Tech Author",
            "source": "Tech Blog",
            "publish_date": datetime.utcnow().isoformat(),
            "content_type": "article",
            "estimated_reading_time": 12,
            "tags": ["technology", "programming"]
        },
        analysis={
            "topics": [{"topic": "technology", "confidence": 0.9}],
            "reading_level": {"flesch_kincaid": 10.0},
            "complexity": {"overall": 0.6},
            "embedding": [0.1] * 384,
            "key_phrases": ["programming", "technology"]
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db_session.add(similar_content)
    db_session.commit()

    recommendations = await contextual_recommendation_engine.generate_contextual_recommendations(
        user_id=user_id,
        limit=5,
        db=db_session
    )

    # Should include diverse content types and topics
    content_types = set()
    topics = set()

    for rec in recommendations:
        content_types.add(rec["metadata"]["content_type"])
        if rec["analysis"]:
            for topic_data in rec["analysis"]["topics"]:
                topics.add(topic_data["topic"])

    # Should have some diversity
    assert len(content_types) > 1 or len(topics) > 2


@pytest.mark.asyncio
async def test_context_inference(db_session: Session, sample_user_profile, sample_content_items):
    """Test context inference from user patterns."""
    user_id = sample_user_profile.user_id

    # Add some reading behavior history
    behavior = ReadingBehavior(
        content_id="content_tech_1",
        user_id=user_id,
        session_id="session_1",
        start_time=datetime.utcnow() - timedelta(hours=2),
        end_time=datetime.utcnow() - timedelta(hours=1, minutes=45),
        completion_rate=0.9,
        reading_speed=250.0,
        pause_patterns=[],
        interactions=[],
        context={"time_of_day": "evening", "device_type": "desktop"},
        created_at=datetime.utcnow()
    )

    db_session.add(behavior)
    db_session.commit()

    # Test without explicit context (should infer from patterns)
    recommendations = await contextual_recommendation_engine.generate_contextual_recommendations(
        user_id=user_id,
        context=None,  # No explicit context
        limit=5,
        db=db_session
    )

    assert len(recommendations) > 0
    # Context should be inferred and applied
    for rec in recommendations:
        assert "contextual_factors" in rec


@pytest.mark.asyncio
async def test_empty_user_profile(db_session: Session, sample_content_items):
    """Test recommendations for user with minimal profile data."""
    # Create minimal user profile
    minimal_profile = UserProfile(
        user_id="minimal_user",
        preferences=PreferenceModel(
            topics=[], content_types=[], contextual_preferences=[], evolution_history=[]
        ).model_dump(),
        reading_levels=LanguageReadingLevels(
            english={"level": 8.0, "confidence": 0.3, "assessment_count": 0},
            japanese={"level": 0.3, "confidence": 0.3, "assessment_count": 0}
        ).model_dump(),
        created_at=datetime.utcnow(),
        last_updated=datetime.utcnow()
    )

    db_session.add(minimal_profile)
    db_session.commit()

    recommendations = await contextual_recommendation_engine.generate_contextual_recommendations(
        user_id="minimal_user",
        limit=5,
        db=db_session
    )

    # Should still generate some recommendations
    assert len(recommendations) > 0
    # Scores might be lower but should be valid
    for rec in recommendations:
        assert 0.0 <= rec["recommendation_score"] <= 1.0


@pytest.mark.asyncio
async def test_no_content_available(db_session: Session, sample_user_profile):
    """Test behavior when no content is available."""
    user_id = sample_user_profile.user_id

    # No content items in database
    recommendations = await contextual_recommendation_engine.generate_contextual_recommendations(
        user_id=user_id,
        limit=5,
        db=db_session
    )

    # Should return empty list gracefully
    assert recommendations == []


@pytest.mark.asyncio
async def test_time_based_scoring(db_session: Session, sample_user_profile, sample_content_items):
    """Test time-of-day based scoring adjustments."""
    user_id = sample_user_profile.user_id

    # Test morning context
    morning_context = ReadingContext(
        time_of_day="morning",
        device_type="desktop",
        available_time=30
    )

    morning_recs = await contextual_recommendation_engine.generate_contextual_recommendations(
        user_id=user_id,
        context=morning_context,
        limit=5,
        db=db_session
    )

    # Test evening context
    evening_context = ReadingContext(
        time_of_day="evening",
        device_type="desktop",
        available_time=30
    )

    evening_recs = await contextual_recommendation_engine.generate_contextual_recommendations(
        user_id=user_id,
        context=evening_context,
        limit=5,
        db=db_session
    )

    # Both should generate recommendations
    assert len(morning_recs) > 0
    assert len(evening_recs) > 0

    # Time factors should be applied
    for rec in morning_recs:
        assert "time_factors" in rec.get(
            "contextual_factors", {}) or "time_based" in rec.get("score_breakdown", {})


@pytest.mark.asyncio
async def test_mood_based_scoring(db_session: Session, sample_user_profile, sample_content_items):
    """Test mood-based scoring adjustments."""
    user_id = sample_user_profile.user_id

    # Test focused mood
    focused_context = ReadingContext(
        time_of_day="afternoon",
        device_type="desktop",
        available_time=45,
        user_mood="focused"
    )

    focused_recs = await contextual_recommendation_engine.generate_contextual_recommendations(
        user_id=user_id,
        context=focused_context,
        limit=5,
        db=db_session
    )

    # Test relaxed mood
    relaxed_context = ReadingContext(
        time_of_day="evening",
        device_type="tablet",
        available_time=20,
        user_mood="relaxed"
    )

    relaxed_recs = await contextual_recommendation_engine.generate_contextual_recommendations(
        user_id=user_id,
        context=relaxed_context,
        limit=5,
        db=db_session
    )

    # Both should generate recommendations
    assert len(focused_recs) > 0
    assert len(relaxed_recs) > 0

    # Mood factors should be applied
    for rec in focused_recs:
        assert "mood_factors" in rec.get(
            "contextual_factors", {}) or "mood_based" in rec.get("score_breakdown", {})
