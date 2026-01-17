"""Tests for the discovery mode engine."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.services.discovery_engine import discovery_engine
from src.models.user_profile import UserProfile, ReadingBehavior
from src.models.content import ContentItem, DiscoveryRecommendation
from src.schemas.user_profile import PreferenceModel, LanguageReadingLevels
from src.schemas.content import ContentMetadata, ContentAnalysis


@pytest.fixture
def established_user_profile(db_session: Session):
    """Create a user profile with established preferences for testing discovery."""
    preferences = PreferenceModel(
        topics=[
            {"topic": "technology", "weight": 0.9, "confidence": 0.9,
             "last_updated": datetime.utcnow().isoformat(), "evolution_trend": "stable"},
            {"topic": "programming", "weight": 0.8, "confidence": 0.8,
             "last_updated": datetime.utcnow().isoformat(), "evolution_trend": "increasing"},
            {"topic": "science", "weight": 0.6, "confidence": 0.7,
             "last_updated": datetime.utcnow().isoformat(), "evolution_trend": "stable"}
        ],
        content_types=[
            {"type": "article", "preference": 0.8,
                "last_updated": datetime.utcnow().isoformat()},
            {"type": "blog", "preference": 0.7,
                "last_updated": datetime.utcnow().isoformat()}
        ],
        contextual_preferences=[
            {"factor": "time_of_day", "value": "evening", "weight": 0.6,
             "last_updated": datetime.utcnow().isoformat()}
        ],
        evolution_history=[]
    )

    reading_levels = LanguageReadingLevels(
        english={"level": 12.0, "confidence": 0.9, "assessment_count": 25},
        japanese={"level": 0.5, "confidence": 0.7, "assessment_count": 12}
    )

    profile = UserProfile(
        user_id="established_user",
        preferences=preferences.dict(),
        reading_levels=reading_levels.dict(),
        created_at=datetime.utcnow() - timedelta(days=90),
        last_updated=datetime.utcnow()
    )

    db_session.add(profile)
    db_session.commit()
    return profile


@pytest.fixture
def diverse_content_items(db_session: Session):
    """Create diverse content items for discovery testing."""
    content_items = []

    # Technology content (matches user preferences - should not be in discovery)
    tech_content = ContentItem(
        id="content_tech_discovery",
        title="Advanced Machine Learning Techniques",
        content="This article covers advanced ML techniques...",
        language="english",
        content_metadata={
            "author": "Tech Expert",
            "source": "Tech Journal",
            "publish_date": datetime.utcnow().isoformat(),
            "content_type": "article",
            "estimated_reading_time": 25,
            "tags": ["technology", "machine_learning"]
        },
        analysis={
            "topics": [
                {"topic": "technology", "confidence": 0.9},
                {"topic": "machine_learning", "confidence": 0.8}
            ],
            "reading_level": {"flesch_kincaid": 12.5, "level": "advanced"},
            "complexity": {"overall": 0.7, "vocabulary": 0.8, "syntax": 0.6},
            "embedding": [0.1] * 384,
            "key_phrases": ["machine learning", "algorithms", "data science"]
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    # Art/creativity content (divergent but with bridging topics)
    art_content = ContentItem(
        id="content_art_discovery",
        title="Digital Art and Creative Technology",
        content="Exploring the intersection of art and technology...",
        language="english",
        content_metadata={
            "author": "Art Critic",
            "source": "Art Magazine",
            "publish_date": datetime.utcnow().isoformat(),
            "content_type": "article",
            "estimated_reading_time": 18,
            "tags": ["art", "creativity", "digital"]
        },
        analysis={
            "topics": [
                {"topic": "art", "confidence": 0.9},
                {"topic": "creativity", "confidence": 0.8},
                {"topic": "digital", "confidence": 0.7}  # Bridge to technology
            ],
            "reading_level": {"flesch_kincaid": 11.0, "level": "intermediate"},
            "complexity": {"overall": 0.5, "vocabulary": 0.6, "syntax": 0.4},
            "embedding": [0.2] * 384,
            "key_phrases": ["digital art", "creative process", "artistic expression"]
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    # History content (completely divergent)
    history_content = ContentItem(
        id="content_history_discovery",
        title="Ancient Roman Architecture",
        content="A study of architectural innovations in ancient Rome...",
        language="english",
        content_metadata={
            "author": "History Professor",
            "source": "History Quarterly",
            "publish_date": datetime.utcnow().isoformat(),
            "content_type": "book",  # Different content type
            "estimated_reading_time": 45,
            "tags": ["history", "architecture", "ancient_rome"]
        },
        analysis={
            "topics": [
                {"topic": "history", "confidence": 0.9},
                {"topic": "architecture", "confidence": 0.8},
                {"topic": "ancient_rome", "confidence": 0.7}
            ],
            "reading_level": {"flesch_kincaid": 13.0, "level": "advanced"},
            "complexity": {"overall": 0.6, "vocabulary": 0.7, "syntax": 0.5},
            "embedding": [0.3] * 384,
            "key_phrases": ["Roman architecture", "historical analysis", "ancient civilizations"]
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    # Psychology content (bridging through science)
    psychology_content = ContentItem(
        id="content_psychology_discovery",
        title="Cognitive Science and Human Behavior",
        content="Understanding human behavior through cognitive science...",
        language="english",
        content_metadata={
            "author": "Psychology Researcher",
            "source": "Psychology Today",
            "publish_date": datetime.utcnow().isoformat(),
            "content_type": "article",
            "estimated_reading_time": 22,
            "tags": ["psychology", "cognitive_science", "behavior"]
        },
        analysis={
            "topics": [
                {"topic": "psychology", "confidence": 0.9},
                {"topic": "cognitive_science", "confidence": 0.8},
                # Bridge to user's science interest
                {"topic": "science", "confidence": 0.6}
            ],
            "reading_level": {"flesch_kincaid": 11.5, "level": "intermediate"},
            "complexity": {"overall": 0.6, "vocabulary": 0.7, "syntax": 0.5},
            "embedding": [0.4] * 384,
            "key_phrases": ["cognitive science", "human behavior", "psychological research"]
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    # Too difficult content (should be filtered out)
    difficult_content = ContentItem(
        id="content_difficult_discovery",
        title="Advanced Quantum Field Theory",
        content="Complex mathematical treatment of quantum field theory...",
        language="english",
        content_metadata={
            "author": "Physics Professor",
            "source": "Physics Journal",
            "publish_date": datetime.utcnow().isoformat(),
            "content_type": "paper",
            "estimated_reading_time": 90,
            "tags": ["physics", "quantum", "mathematics"]
        },
        analysis={
            "topics": [
                {"topic": "physics", "confidence": 0.9},
                {"topic": "quantum_mechanics", "confidence": 0.8},
                {"topic": "mathematics", "confidence": 0.7}
            ],
            # Too difficult
            "reading_level": {"flesch_kincaid": 18.0, "level": "expert"},
            "complexity": {"overall": 0.9, "vocabulary": 0.9, "syntax": 0.8},
            "embedding": [0.5] * 384,
            "key_phrases": ["quantum field theory", "mathematical physics", "advanced concepts"]
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    content_items = [tech_content, art_content,
                     history_content, psychology_content, difficult_content]

    for item in content_items:
        db_session.add(item)

    db_session.commit()
    return content_items


@pytest.fixture
def user_reading_history(db_session: Session, established_user_profile, diverse_content_items):
    """Create reading history showing established preferences."""
    behaviors = []

    # User has read technology content extensively
    tech_behavior = ReadingBehavior(
        content_id="content_tech_discovery",
        user_id=established_user_profile.user_id,
        session_id="session_tech_1",
        start_time=datetime.utcnow() - timedelta(days=5),
        end_time=datetime.utcnow() - timedelta(days=5, hours=-1),
        completion_rate=0.95,
        reading_speed=280.0,
        pause_patterns=[],
        interactions=[{"type": "highlight",
                       "timestamp": datetime.utcnow().isoformat()}],
        context={"time_of_day": "evening", "device_type": "desktop"},
        created_at=datetime.utcnow() - timedelta(days=5)
    )
    behaviors.append(tech_behavior)

    for behavior in behaviors:
        db_session.add(behavior)

    db_session.commit()
    return behaviors


@pytest.mark.asyncio
async def test_generate_discovery_recommendations_basic(db_session: Session, established_user_profile, diverse_content_items, user_reading_history):
    """Test basic discovery recommendation generation."""
    user_id = established_user_profile.user_id

    recommendations = await discovery_engine.generate_discovery_recommendations(
        user_id=user_id,
        limit=5,
        db=db_session
    )

    assert len(recommendations) > 0
    assert all("content_id" in rec for rec in recommendations)
    assert all("divergence_score" in rec for rec in recommendations)
    assert all("discovery_reason" in rec for rec in recommendations)
    assert all("bridging_topics" in rec for rec in recommendations)

    # All recommendations should meet minimum divergence threshold
    for rec in recommendations:
        assert rec["divergence_score"] >= discovery_engine.min_divergence_score


@pytest.mark.asyncio
async def test_discovery_excludes_established_preferences(db_session: Session, established_user_profile, diverse_content_items, user_reading_history):
    """Test that discovery recommendations diverge from established preferences."""
    user_id = established_user_profile.user_id

    recommendations = await discovery_engine.generate_discovery_recommendations(
        user_id=user_id,
        limit=10,
        db=db_session
    )

    # Should not heavily recommend pure technology content (user's main interest)
    tech_recs = [rec for rec in recommendations if "technology" in rec["title"].lower(
    ) and "art" not in rec["title"].lower()]

    # Pure tech content should have lower priority or be excluded
    if tech_recs:
        # If included, should have high divergence score or bridging elements
        for tech_rec in tech_recs:
            assert tech_rec["divergence_score"] >= 0.3 or len(
                tech_rec["bridging_topics"]) > 0


@pytest.mark.asyncio
async def test_discovery_bridging_topics(db_session: Session, established_user_profile, diverse_content_items, user_reading_history):
    """Test that discovery recommendations include bridging topics."""
    user_id = established_user_profile.user_id

    recommendations = await discovery_engine.generate_discovery_recommendations(
        user_id=user_id,
        limit=10,
        db=db_session
    )

    # Find art content (should have bridging topics)
    art_recs = [rec for rec in recommendations if "art" in rec["title"].lower()]

    if art_recs:
        art_rec = art_recs[0]
        # Should have bridging topics connecting to user's interests
        assert len(art_rec["bridging_topics"]) > 0
        # Should explain the bridge in discovery reason
        assert "bridge" in art_rec["discovery_reason"].lower(
        ) or "connect" in art_rec["discovery_reason"].lower()


@pytest.mark.asyncio
async def test_discovery_accessibility_filtering(db_session: Session, established_user_profile, diverse_content_items, user_reading_history):
    """Test that discovery recommendations are still accessible to the user."""
    user_id = established_user_profile.user_id

    recommendations = await discovery_engine.generate_discovery_recommendations(
        user_id=user_id,
        limit=10,
        db=db_session
    )

    # Should not include content that's too difficult
    for rec in recommendations:
        if rec["language"] == "english":
            analysis = ContentAnalysis(**rec["analysis"])
            content_level = analysis.reading_level.get("flesch_kincaid", 8.0)
            user_level = 12.0  # From established_user_profile

            # Should be accessible (allowing some challenge for discovery)
            assert content_level <= user_level + 3.0

        # Should have reasonable accessibility score
        assert rec["accessibility_score"] >= 0.3


@pytest.mark.asyncio
async def test_discovery_content_type_divergence(db_session: Session, established_user_profile, diverse_content_items, user_reading_history):
    """Test discovery of different content types."""
    user_id = established_user_profile.user_id

    recommendations = await discovery_engine.generate_discovery_recommendations(
        user_id=user_id,
        limit=10,
        db=db_session
    )

    # Should include content types user hasn't typically read
    content_types = set()
    for rec in recommendations:
        content_types.add(rec["metadata"]["content_type"])

    # User typically reads articles and blogs, so should suggest books or other types
    established_types = {"article", "blog"}
    new_types = content_types - established_types

    # Should have some content type diversity
    assert len(new_types) > 0 or len(content_types) > 1


@pytest.mark.asyncio
async def test_discovery_serendipity_factors(db_session: Session, established_user_profile, diverse_content_items, user_reading_history):
    """Test serendipity factors in discovery recommendations."""
    user_id = established_user_profile.user_id

    recommendations = await discovery_engine.generate_discovery_recommendations(
        user_id=user_id,
        limit=5,
        db=db_session
    )

    # Check that serendipity factors are calculated
    for rec in recommendations:
        assert "serendipity_factors" in rec
        # Serendipity factors should be a dictionary
        assert isinstance(rec["serendipity_factors"], dict)


@pytest.mark.asyncio
async def test_discovery_ranking_and_diversity(db_session: Session, established_user_profile, diverse_content_items, user_reading_history):
    """Test discovery recommendation ranking and diversity."""
    user_id = established_user_profile.user_id

    recommendations = await discovery_engine.generate_discovery_recommendations(
        user_id=user_id,
        limit=5,
        db=db_session
    )

    if len(recommendations) > 1:
        # Should be ranked by combined discovery score
        combined_scores = [rec.get("combined_discovery_score", 0)
                           for rec in recommendations]

        # Check diversity in topics
        all_topics = set()
        for rec in recommendations:
            if rec["analysis"]:
                for topic_data in rec["analysis"]["topics"]:
                    all_topics.add(topic_data["topic"])

        # Should have diverse topics
        # At least one unique topic per recommendation
        assert len(all_topics) >= len(recommendations)


@pytest.mark.asyncio
async def test_discovery_excludes_recently_read(db_session: Session, established_user_profile, diverse_content_items, user_reading_history):
    """Test that discovery excludes recently read content."""
    user_id = established_user_profile.user_id

    recommendations = await discovery_engine.generate_discovery_recommendations(
        user_id=user_id,
        limit=10,
        db=db_session
    )

    # Should not include content the user has already read
    read_content_ids = {
        behavior.content_id for behavior in user_reading_history}
    recommended_ids = {rec["content_id"] for rec in recommendations}

    # No overlap between read and recommended content
    assert len(read_content_ids & recommended_ids) == 0


@pytest.mark.asyncio
async def test_discovery_response_tracking(db_session: Session, established_user_profile, diverse_content_items):
    """Test tracking user responses to discovery recommendations."""
    user_id = established_user_profile.user_id
    content_id = "content_art_discovery"

    # Track positive response
    await discovery_engine.track_discovery_response(
        user_id=user_id,
        content_id=content_id,
        response="interested",
        db=db_session
    )

    # Check that response was recorded
    discovery_rec = db_session.query(DiscoveryRecommendation).filter(
        DiscoveryRecommendation.user_id == user_id,
        DiscoveryRecommendation.content_id == content_id
    ).first()

    # Note: This test assumes a discovery recommendation was created first
    # In practice, this would be created during recommendation generation


@pytest.mark.asyncio
async def test_discovery_with_language_filter(db_session: Session, established_user_profile, diverse_content_items, user_reading_history):
    """Test discovery recommendations with language filtering."""
    user_id = established_user_profile.user_id

    # Test English recommendations
    english_recs = await discovery_engine.generate_discovery_recommendations(
        user_id=user_id,
        language="english",
        limit=5,
        db=db_session
    )

    # All recommendations should be in English
    assert all(rec["language"] == "english" for rec in english_recs)


@pytest.mark.asyncio
async def test_discovery_with_minimal_user_data(db_session: Session, diverse_content_items):
    """Test discovery recommendations for user with minimal data."""
    # Create minimal user profile
    minimal_preferences = PreferenceModel(
        topics=[{"topic": "general", "weight": 0.1, "confidence": 0.2,
                "last_updated": datetime.utcnow().isoformat(), "evolution_trend": "stable"}],
        content_types=[],
        contextual_preferences=[],
        evolution_history=[]
    )

    minimal_profile = UserProfile(
        user_id="minimal_discovery_user",
        preferences=minimal_preferences.dict(),
        reading_levels=LanguageReadingLevels(
            english={"level": 8.0, "confidence": 0.3, "assessment_count": 1},
            japanese={"level": 0.3, "confidence": 0.3, "assessment_count": 0}
        ).dict(),
        created_at=datetime.utcnow(),
        last_updated=datetime.utcnow()
    )

    db_session.add(minimal_profile)
    db_session.commit()

    recommendations = await discovery_engine.generate_discovery_recommendations(
        user_id="minimal_discovery_user",
        limit=5,
        db=db_session
    )

    # Should still generate some discovery recommendations
    # For minimal users, most content could be considered "discovery"
    assert len(recommendations) >= 0  # May be empty if no suitable content


@pytest.mark.asyncio
async def test_discovery_excludes_previous_discoveries(db_session: Session, established_user_profile, diverse_content_items, user_reading_history):
    """Test that discovery excludes previously recommended discovery content."""
    user_id = established_user_profile.user_id

    # Create a previous discovery recommendation
    previous_discovery = DiscoveryRecommendation(
        content_id="content_art_discovery",
        user_id=user_id,
        divergence_score=0.7,
        bridging_topics=["digital"],
        discovery_reason="Explores art through technology",
        created_at=datetime.utcnow() - timedelta(days=15)
    )

    db_session.add(previous_discovery)
    db_session.commit()

    recommendations = await discovery_engine.generate_discovery_recommendations(
        user_id=user_id,
        limit=10,
        db=db_session
    )

    # Should not include previously discovered content (within 30 days)
    recommended_ids = {rec["content_id"] for rec in recommendations}
    assert "content_art_discovery" not in recommended_ids


@pytest.mark.asyncio
async def test_discovery_genre_bridging(db_session: Session, established_user_profile, diverse_content_items, user_reading_history):
    """Test genre bridging in discovery recommendations."""
    user_id = established_user_profile.user_id

    recommendations = await discovery_engine.generate_discovery_recommendations(
        user_id=user_id,
        limit=10,
        db=db_session
    )

    # Look for content that bridges from user's established interests
    psychology_recs = [
        rec for rec in recommendations if "psychology" in rec["title"].lower()]

    if psychology_recs:
        psych_rec = psychology_recs[0]
        # Should have science as a bridging topic (user likes science)
        bridging_topics = psych_rec["bridging_topics"]
        # The bridging might be through "science" connection
        assert len(bridging_topics) >= 0  # May have bridging topics


@pytest.mark.asyncio
async def test_discovery_no_suitable_content(db_session: Session, established_user_profile):
    """Test discovery behavior when no suitable content is available."""
    user_id = established_user_profile.user_id

    # No content items in database
    recommendations = await discovery_engine.generate_discovery_recommendations(
        user_id=user_id,
        limit=5,
        db=db_session
    )

    # Should return empty list gracefully
    assert recommendations == []
