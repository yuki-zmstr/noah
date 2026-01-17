"""Tests for user profile service and feedback processing."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import json

from src.services.user_profile_service import UserProfileEngine, user_profile_engine
from src.services.feedback_service import FeedbackProcessor, FeedbackType, feedback_processor
from src.models.user_profile import UserProfile, ReadingBehavior, PreferenceSnapshot
from src.models.content import ContentItem
from src.schemas.user_profile import PreferenceModel, LanguageReadingLevels


class TestUserProfileEngine:
    """Test cases for UserProfileEngine."""

    @pytest.fixture
    def profile_engine(self):
        """Create a UserProfileEngine instance."""
        return UserProfileEngine()

    @pytest.fixture
    def sample_user_profile(self, db_session):
        """Create a sample user profile."""
        profile = UserProfile(
            user_id="test_user_123",
            preferences={
                "topics": [
                    {"topic": "fiction", "weight": 0.7, "confidence": 0.8,
                     "last_updated": datetime.utcnow().isoformat(), "evolution_trend": "stable"}
                ],
                "content_types": [
                    {"type": "book", "preference": 0.8,
                        "last_updated": datetime.utcnow().isoformat()}
                ],
                "contextual_preferences": [],
                "evolution_history": []
            },
            reading_levels={
                "english": {"level": 8.5, "confidence": 0.7, "assessment_count": 5},
                "japanese": {"level": 0.3, "confidence": 0.5, "assessment_count": 2}
            },
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        db_session.add(profile)
        db_session.commit()
        db_session.refresh(profile)
        return profile

    @pytest.fixture
    def sample_content(self, db_session):
        """Create sample content for testing."""
        content = ContentItem(
            id="content_123",
            title="Test Fiction Book",
            content="This is a test fiction book with interesting characters...",
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
                "topics": [
                    {"topic": "fiction", "confidence": 0.9},
                    {"topic": "adventure", "confidence": 0.7}
                ],
                "reading_level": {"flesch_kincaid": 8.5, "level": "intermediate"},
                "complexity": {"sentence_length": 15.2},
                "embedding": [0.1, 0.2, 0.3],
                "key_phrases": ["adventure", "characters", "story"]
            }
        )
        db_session.add(content)
        db_session.commit()
        db_session.refresh(content)
        return content

    @pytest.mark.asyncio
    async def test_get_or_create_profile_new_user(self, profile_engine, db_session):
        """Test creating a new user profile."""
        user_id = "new_user_456"

        profile = await profile_engine.get_or_create_profile(user_id, db_session)

        assert profile is not None
        assert profile.user_id == user_id
        assert profile.preferences is not None
        assert profile.reading_levels is not None

        # Verify default values
        preferences = PreferenceModel(**profile.preferences)
        reading_levels = LanguageReadingLevels(**profile.reading_levels)

        assert len(preferences.topics) == 0
        assert reading_levels.english["level"] == 8.0
        assert reading_levels.japanese["level"] == 0.3

    @pytest.mark.asyncio
    async def test_get_or_create_profile_existing_user(self, profile_engine, db_session, sample_user_profile):
        """Test retrieving an existing user profile."""
        profile = await profile_engine.get_or_create_profile(sample_user_profile.user_id, db_session)

        assert profile.user_id == sample_user_profile.user_id
        assert profile.preferences == sample_user_profile.preferences
        assert profile.reading_levels == sample_user_profile.reading_levels

    @pytest.mark.asyncio
    async def test_update_reading_behavior(self, profile_engine, db_session, sample_user_profile, sample_content):
        """Test recording reading behavior."""
        behavior_data = {
            "session_id": "session_123",
            "start_time": datetime.utcnow(),
            "end_time": datetime.utcnow() + timedelta(minutes=30),
            "completion_rate": 0.85,
            "reading_speed": 250.0,
            "pause_patterns": [{"timestamp": "2024-01-01T10:00:00", "duration": 30}],
            "interactions": [{"type": "highlight", "position": 150}],
            "context": {"device_type": "mobile", "time_of_day": "evening"}
        }

        behavior = await profile_engine.update_reading_behavior(
            sample_user_profile.user_id, sample_content.id, behavior_data, db_session
        )

        assert behavior is not None
        assert behavior.user_id == sample_user_profile.user_id
        assert behavior.content_id == sample_content.id
        assert behavior.completion_rate == 0.85
        assert behavior.reading_speed == 250.0

    @pytest.mark.asyncio
    async def test_assess_reading_level_english(self, profile_engine, db_session, sample_user_profile):
        """Test English reading level assessment."""
        content_analysis = {
            "reading_level": {"flesch_kincaid": 10.0}
        }
        performance_metrics = {
            "completion_rate": 0.9,
            "reading_speed": 280.0,
            "pause_patterns": [],
            "interactions": [{"type": "highlight"}]
        }

        new_level = await profile_engine.assess_reading_level(
            sample_user_profile.user_id, "english", content_analysis, performance_metrics, db_session
        )

        assert new_level is not None
        assert "level" in new_level
        assert "confidence" in new_level
        assert "assessment_count" in new_level
        assert new_level["assessment_count"] == 6  # Original 5 + 1

    @pytest.mark.asyncio
    async def test_assess_reading_level_japanese(self, profile_engine, db_session, sample_user_profile):
        """Test Japanese reading level assessment."""
        content_analysis = {
            "reading_level": {"kanji_density": 0.4}
        }
        performance_metrics = {
            "completion_rate": 0.7,
            "reading_speed": 150.0,
            "pause_patterns": [{"duration": 10}, {"duration": 15}],
            "interactions": []
        }

        new_level = await profile_engine.assess_reading_level(
            sample_user_profile.user_id, "japanese", content_analysis, performance_metrics, db_session
        )

        assert new_level is not None
        assert new_level["assessment_count"] == 3  # Original 2 + 1

    @pytest.mark.asyncio
    async def test_update_preferences_from_feedback(self, profile_engine, db_session, sample_user_profile, sample_content):
        """Test updating preferences from feedback."""
        feedback_data = {
            "type": "explicit",
            "value": 0.8,
            "context": {"time_of_day": "evening", "device_type": "tablet"}
        }

        await profile_engine.update_preferences_from_feedback(
            sample_user_profile.user_id, sample_content.id, feedback_data, db_session
        )

        # Refresh profile to get updated data
        db_session.refresh(sample_user_profile)
        preferences = PreferenceModel(**sample_user_profile.preferences)

        # Check that fiction topic weight increased (it was 0.7, should be higher now)
        fiction_topic = next(
            (t for t in preferences.topics if t["topic"] == "fiction"), None)
        assert fiction_topic is not None
        assert fiction_topic["weight"] > 0.7

    @pytest.mark.asyncio
    async def test_get_preference_transparency(self, profile_engine, db_session, sample_user_profile):
        """Test preference transparency generation."""
        transparency = await profile_engine.get_preference_transparency(sample_user_profile.user_id, db_session)

        assert transparency is not None
        assert transparency["user_id"] == sample_user_profile.user_id
        assert "reading_levels" in transparency
        assert "topic_preferences" in transparency
        assert "content_type_preferences" in transparency

        # Check reading level explanations
        assert "explanation" in transparency["reading_levels"]["english"]
        assert "explanation" in transparency["reading_levels"]["japanese"]

    @pytest.mark.asyncio
    async def test_get_collaborative_filtering_data(self, profile_engine, db_session, sample_user_profile):
        """Test collaborative filtering data generation."""
        # Create some reading behavior first
        behavior = ReadingBehavior(
            content_id="content_123",
            user_id=sample_user_profile.user_id,
            session_id="session_123",
            start_time=datetime.utcnow(),
            completion_rate=0.8,
            reading_speed=250.0,
            created_at=datetime.utcnow()
        )
        db_session.add(behavior)
        db_session.commit()

        cf_data = await profile_engine.get_collaborative_filtering_data(sample_user_profile.user_id, db_session)

        assert cf_data is not None
        assert "user_reading_history" in cf_data
        assert "similar_users" in cf_data
        assert "content_similarities" in cf_data
        assert "preference_vector" in cf_data

        assert len(cf_data["user_reading_history"]) == 1
        assert cf_data["user_reading_history"][0]["content_id"] == "content_123"

    def test_calculate_performance_score(self, profile_engine):
        """Test performance score calculation."""
        metrics = {
            "completion_rate": 0.9,
            "reading_speed": 250.0,
            "pause_patterns": [{"duration": 5}],
            "interactions": [{"type": "highlight"}, {"type": "note"}]
        }

        score = profile_engine._calculate_performance_score(metrics)

        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be a good score given the metrics

    def test_update_reading_level(self, profile_engine):
        """Test reading level update logic."""
        current_data = {
            "level": 8.0,
            "confidence": 0.6,
            "assessment_count": 3
        }

        # Test with good performance on harder content
        new_data = profile_engine._update_reading_level(
            current_data, 10.0, 0.85)

        assert new_data["level"] > 8.0  # Should increase
        assert new_data["assessment_count"] == 4
        assert "last_assessment" in new_data

    def test_calculate_implicit_rating(self, profile_engine):
        """Test implicit rating calculation."""
        behavior = ReadingBehavior(
            completion_rate=0.8,
            reading_speed=250.0,
            interactions=[{"type": "highlight"}, {"type": "note"}]
        )

        rating = profile_engine._calculate_implicit_rating(behavior)

        assert -1.0 <= rating <= 1.0
        assert rating > 0  # Should be positive given good metrics

    def test_calculate_trend(self, profile_engine):
        """Test trend calculation."""
        assert profile_engine._calculate_trend(0.5, 0.7) == "increasing"
        assert profile_engine._calculate_trend(0.7, 0.5) == "decreasing"
        assert profile_engine._calculate_trend(0.5, 0.52) == "stable"


class TestFeedbackProcessor:
    """Test cases for FeedbackProcessor."""

    @pytest.fixture
    def feedback_processor(self):
        """Create a FeedbackProcessor instance."""
        return FeedbackProcessor()

    @pytest.fixture
    def sample_user_profile(self, db_session):
        """Create a sample user profile."""
        profile = UserProfile(
            user_id="test_user_123",
            preferences={
                "topics": [
                    {"topic": "fiction", "weight": 0.7, "confidence": 0.8,
                     "last_updated": datetime.utcnow().isoformat(), "evolution_trend": "stable"}
                ],
                "content_types": [
                    {"type": "book", "preference": 0.8,
                        "last_updated": datetime.utcnow().isoformat()}
                ],
                "contextual_preferences": [],
                "evolution_history": []
            },
            reading_levels={
                "english": {"level": 8.5, "confidence": 0.7, "assessment_count": 5},
                "japanese": {"level": 0.3, "confidence": 0.5, "assessment_count": 2}
            },
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        db_session.add(profile)
        db_session.commit()
        db_session.refresh(profile)
        return profile

    @pytest.fixture
    def sample_content(self, db_session):
        """Create sample content for testing."""
        content = ContentItem(
            id="content_123",
            title="Test Fiction Book",
            content="This is a test fiction book with interesting characters...",
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
                "topics": [
                    {"topic": "fiction", "confidence": 0.9},
                    {"topic": "adventure", "confidence": 0.7}
                ],
                "reading_level": {"flesch_kincaid": 8.5, "level": "intermediate"},
                "complexity": {"sentence_length": 15.2},
                "embedding": [0.1, 0.2, 0.3],
                "key_phrases": ["adventure", "characters", "story"]
            }
        )
        db_session.add(content)
        db_session.commit()
        db_session.refresh(content)
        return content

    @pytest.fixture
    def sample_behavior_data(self):
        """Create sample behavior data."""
        return {
            "completion_rate": 0.85,
            "reading_speed": 250.0,
            "estimated_reading_time": 300,
            "actual_reading_time": 360,
            "pause_patterns": [{"timestamp": "2024-01-01T10:00:00", "duration": 30}],
            "interactions": [
                {"type": "highlight", "position": 150},
                {"type": "note", "content": "Interesting point"}
            ]
        }

    @pytest.mark.asyncio
    async def test_process_explicit_feedback_rating(self, feedback_processor, db_session, sample_user_profile, sample_content):
        """Test processing explicit rating feedback."""
        feedback_data = {
            "type": "explicit_rating",
            "rating": 4,  # 4 out of 5
            "context": {"device_type": "tablet"}
        }

        result = await feedback_processor.process_explicit_feedback(
            sample_user_profile.user_id, sample_content.id, feedback_data, db_session
        )

        assert result["feedback_processed"] is True
        assert result["feedback_type"] == "explicit_rating"
        assert result["normalized_value"] == 0.5  # (4-3)/2 = 0.5
        assert "explanation" in result

    @pytest.mark.asyncio
    async def test_process_explicit_feedback_like_dislike(self, feedback_processor, db_session, sample_user_profile, sample_content):
        """Test processing like/dislike feedback."""
        feedback_data = {
            "type": "like_dislike",
            "liked": True
        }

        result = await feedback_processor.process_explicit_feedback(
            sample_user_profile.user_id, sample_content.id, feedback_data, db_session
        )

        assert result["feedback_processed"] is True
        assert result["normalized_value"] == 0.8

    @pytest.mark.asyncio
    async def test_process_implicit_feedback(self, feedback_processor, db_session, sample_user_profile, sample_content, sample_behavior_data):
        """Test processing implicit feedback."""
        result = await feedback_processor.process_implicit_feedback(
            sample_user_profile.user_id, sample_content.id, sample_behavior_data, db_session
        )

        assert "feedback_processed" in result
        assert "signals_detected" in result
        assert "signal_types" in result

    def test_normalize_explicit_feedback_rating(self, feedback_processor):
        """Test explicit feedback normalization for ratings."""
        feedback_data = {"rating": 5}
        normalized = feedback_processor._normalize_explicit_feedback(
            feedback_data, FeedbackType.EXPLICIT_RATING
        )

        assert normalized["value"] == 1.0  # (5-3)/2 = 1.0
        assert normalized["type"] == "explicit"

    def test_normalize_explicit_feedback_like(self, feedback_processor):
        """Test explicit feedback normalization for likes."""
        feedback_data = {"liked": True}
        normalized = feedback_processor._normalize_explicit_feedback(
            feedback_data, FeedbackType.LIKE_DISLIKE
        )

        assert normalized["value"] == 0.8

    def test_analyze_comment_sentiment(self, feedback_processor):
        """Test comment sentiment analysis."""
        positive_comment = "This book is amazing and wonderful!"
        negative_comment = "This book is terrible and boring."
        neutral_comment = "This book is okay."

        assert feedback_processor._analyze_comment_sentiment(
            positive_comment) > 0
        assert feedback_processor._analyze_comment_sentiment(
            negative_comment) < 0
        assert feedback_processor._analyze_comment_sentiment(
            neutral_comment) == 0

    def test_analyze_completion_feedback(self, feedback_processor):
        """Test completion rate analysis."""
        # High completion
        high_completion = {"completion_rate": 0.9}
        result = feedback_processor._analyze_completion_feedback(
            high_completion)
        assert result is not None
        assert result["value"] > 0

        # Low completion
        low_completion = {"completion_rate": 0.1}
        result = feedback_processor._analyze_completion_feedback(
            low_completion)
        assert result is not None
        assert result["value"] < 0

        # Medium completion (should return None)
        medium_completion = {"completion_rate": 0.6}
        result = feedback_processor._analyze_completion_feedback(
            medium_completion)
        assert result is None

    def test_analyze_time_feedback(self, feedback_processor):
        """Test reading time analysis."""
        # Engaged reading (took longer than expected)
        engaged_data = {
            "estimated_reading_time": 300,
            "actual_reading_time": 400
        }
        result = feedback_processor._analyze_time_feedback(engaged_data)
        assert result is not None
        assert result["value"] > 0

        # Rushed reading
        rushed_data = {
            "estimated_reading_time": 300,
            "actual_reading_time": 120
        }
        result = feedback_processor._analyze_time_feedback(rushed_data)
        assert result is not None
        assert result["value"] < 0

    def test_analyze_interaction_feedback(self, feedback_processor):
        """Test interaction analysis."""
        # High interaction
        high_interaction = {
            "interactions": [
                {"type": "highlight"}, {"type": "note"}, {"type": "bookmark"},
                {"type": "highlight"}, {"type": "note"}
            ]
        }
        result = feedback_processor._analyze_interaction_feedback(
            high_interaction)
        assert result is not None
        assert result["value"] > 0

        # Meaningful interactions
        meaningful_interaction = {
            "interactions": [{"type": "highlight"}, {"type": "note"}]
        }
        result = feedback_processor._analyze_interaction_feedback(
            meaningful_interaction)
        assert result is not None
        assert result["value"] > 0

        # No interactions
        no_interaction = {"interactions": []}
        result = feedback_processor._analyze_interaction_feedback(
            no_interaction)
        assert result is None

    def test_combine_implicit_signals(self, feedback_processor):
        """Test combining multiple implicit signals."""
        signals = [
            {
                "type": FeedbackType.IMPLICIT_COMPLETION.value,
                "value": 0.6,
                "confidence": 0.8
            },
            {
                "type": FeedbackType.IMPLICIT_INTERACTION.value,
                "value": 0.4,
                "confidence": 0.6
            }
        ]

        combined = feedback_processor._combine_implicit_signals(signals)

        assert combined is not None
        assert combined["type"] == "implicit"
        assert -1.0 <= combined["value"] <= 1.0
        assert combined["confidence"] > 0

    def test_classify_completion_pattern(self, feedback_processor):
        """Test completion pattern classification."""
        assert feedback_processor._classify_completion_pattern(
            0.9, 8, 1) == "high_completer"
        assert feedback_processor._classify_completion_pattern(
            0.2, 1, 8) == "low_completer"
        assert feedback_processor._classify_completion_pattern(
            0.6, 6, 2) == "selective_completer"
        assert feedback_processor._classify_completion_pattern(
            0.6, 2, 6) == "browser"

    @pytest.mark.asyncio
    async def test_analyze_feedback_patterns(self, feedback_processor, db_session, sample_user_profile):
        """Test feedback pattern analysis."""
        # Create some reading behaviors
        behaviors = []
        for i in range(5):
            behavior = ReadingBehavior(
                content_id=f"content_{i}",
                user_id=sample_user_profile.user_id,
                session_id=f"session_{i}",
                start_time=datetime.utcnow() - timedelta(days=i),
                completion_rate=0.8 - (i * 0.1),
                reading_speed=250.0 + (i * 10),
                interactions=[{"type": "highlight"}] * i,
                context={"device_type": "mobile", "time_of_day": "evening"},
                created_at=datetime.utcnow() - timedelta(days=i)
            )
            behaviors.append(behavior)
            db_session.add(behavior)

        db_session.commit()

        patterns = await feedback_processor.analyze_feedback_patterns(sample_user_profile.user_id, db_session)

        assert patterns["patterns_found"] is True
        assert patterns["patterns"]["total_sessions"] == 5
        assert "completion_patterns" in patterns["patterns"]
        assert "time_patterns" in patterns["patterns"]
        assert "interaction_patterns" in patterns["patterns"]
        assert "insights" in patterns
        assert "recommendations" in patterns

    @pytest.mark.asyncio
    async def test_get_feedback_transparency(self, feedback_processor, db_session, sample_user_profile):
        """Test feedback transparency."""
        transparency = await feedback_processor.get_feedback_transparency(sample_user_profile.user_id, db_session)

        assert transparency is not None
        assert transparency["user_id"] == sample_user_profile.user_id
        assert "feedback_data_points" in transparency
        assert "explanations" in transparency
        assert "feedback_effectiveness" in transparency


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
